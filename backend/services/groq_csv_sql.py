import pandas as pd
import json
import re
import os
from groq import Groq
from config import Config
from models.database import db


class GroqCSVSQLService:
    """
    Service for handling CSV file processing using Groq Llama3-70b-8192.
    This will:
    - read the CSV
    - use LLM to generate SQL for table creation/insertion
    - execute SQL in the PostgreSQL database
    """

    def __init__(self):
        self.model = "llama3-70b-8192"

        # Clear proxy environment variables that might interfere
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]

        try:
            api_key = Config.GROQ_API_KEY
            print(f"GROQ_API_KEY value: {'SET' if api_key else 'NOT SET'}")

            if not api_key:
                raise ValueError("GROQ_API_KEY is not set in environment variables")

            # Initialize Groq client with only the api_key parameter
            self.client = Groq(api_key=api_key)
            print("Groq client initialized for CSV-to-SQL tasks.")

        except Exception as e:
            print(f"Error initializing Groq client: {e}")
            self.client = None

    def clean_and_fix_sql(self, llm_sql_code):
        """
        Extract clean SQL code from LLM response and fix reserved keywords and type issues.
        """
        # Extract SQL code blocks between triple backticks (preferred if present)
        code_blocks = re.findall(r'``````', llm_sql_code, re.DOTALL | re.IGNORECASE)
        if code_blocks:
            # Join all code blocks (if any)
            sql_code = '\n'.join(block.strip() for block in code_blocks)
        else:
            # Fallback: remove everything before first CREATE TABLE or INSERT INTO
            lines = llm_sql_code.split('\n')
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().upper().startswith(('CREATE TABLE', 'INSERT INTO')):
                    start_idx = i
                    break
            sql_code = '\n'.join(lines[start_idx:])

        # Remove markdown formatting
        sql_code = re.sub(r'\*\*.*?\*\*', '', sql_code)  # Remove **bold**
        sql_code = re.sub(r'^#+\s.*$', '', sql_code, flags=re.MULTILINE)  # Remove headings

        # Remove any remaining backticks and notes
        sql_code = re.sub(r'```.*?$', '', sql_code, flags=re.MULTILINE)  # Remove remaining backticks
        sql_code = re.sub(r'^Note:.*$', '', sql_code, flags=re.MULTILINE)  # Remove note lines
        # Fix PostgreSQL reserved keyword 'Group' by adding quotes
        sql_code = re.sub(r'\bGroup\b', '"Group"', sql_code)

        # Fix numeric overflow: relax NUMERIC(5,2) (and similar) to NUMERIC(10,2)
        sql_code = re.sub(r'NUMERIC$$5,2$$', 'NUMERIC(10,2)', sql_code)

        # Replace COPY statements with INSERT statements (COPY requires file access)
        # This is a common issue with LLM-generated SQL
        if 'COPY' in sql_code.upper():
            sql_code = self._convert_copy_to_insert(sql_code)

        # Clean up extra whitespace and empty lines
        sql_code = re.sub(r'\n\s*\n', '\n', sql_code)
        sql_code = re.sub(r'^\s*\n', '', sql_code, flags=re.MULTILINE)  # Remove empty lines at start

        return sql_code.strip()

    def _convert_copy_to_insert(self, sql_code):
        """
        Convert COPY statements to INSERT statements since COPY requires file system access
        """
        # Remove COPY statements - we'll generate proper INSERT statements separately
        sql_code = re.sub(r'COPY.*?;', '', sql_code, flags=re.DOTALL | re.IGNORECASE)
        return sql_code

    def _generate_insert_statements(self, df, table_name):
        """
        Generate INSERT statements for all rows in the DataFrame
        """
        if df.empty:
            return ""

        columns = ', '.join([f'"{col}"' for col in df.columns])
        insert_statements = []

        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append('NULL')
                elif isinstance(val, str):
                    # Escape single quotes properly
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                else:
                    values.append(str(val))

            insert_stmt = f"INSERT INTO {table_name} ({columns}) VALUES ({', '.join(values)});"
            insert_statements.append(insert_stmt)

        return '\n'.join(insert_statements)

    def process_csv_with_llm(self, file_path, filename):
        # Add this check at the beginning
        if self.client is None:
            return {
                "success": False,
                "message": "Groq client not initialized. Please check your GROQ_API_KEY environment variable and restart the backend."
            }

        # Read CSV file
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            return {"success": False, "message": "CSV file is empty."}
        except pd.errors.ParserError as e:
            return {"success": False, "message": f"CSV parsing error: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to read CSV: {str(e)}"}

        if df.empty:
            return {"success": False, "message": "CSV file contains no data rows."}

        # Generate a valid PostgreSQL table name from the filename
        table_name = filename.replace('.csv', '').lower().replace(' ', '_').replace('-', '_')
        table_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
        if not table_name.isalpha():
            table_name = 'table_' + table_name

        # Prepare DataFrame metadata for LLM prompt
        sample = df.head(3).to_dict(orient="records")
        prompt = (
            f"You are a PostgreSQL expert. Given the following CSV file information, generate valid SQL "
            f"statements to create a table (use 'CREATE TABLE IF NOT EXISTS'). "
            f"DO NOT generate INSERT statements or COPY statements - only CREATE TABLE.\n"
            f"Table name: {table_name}\n"
            f"Columns: {', '.join(df.columns)}\n"
            f"Sample Data:\n{json.dumps(sample, indent=2)}\n\n"
            f"Requirements:\n- Use correct SQL data types for each column\n"
            f"- Use the above table name and columns exactly as provided\n"
            f"- Quote column names that might be PostgreSQL reserved words\n"
            f"- Only output SQL code for CREATE TABLE IF NOT EXISTS statement\n"
            f"- Put SQL code inside triple backticks (```sql)\n"
            f"Begin SQL code below:"
        )

        # Query Groq LLM for SQL code
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=2500,
                temperature=0.1,
            )

            print("Debug - Groq API Response Type:", type(response))
            print("Debug - Groq API Response:", response)

            # Safe attribute access
            if hasattr(response, 'choices') and len(response.choices) > 0:
                first_choice = response.choices[0]
                print("Debug - First Choice Type:", type(first_choice))
                print("Debug - First Choice:", first_choice)

                if hasattr(first_choice, 'message'):
                    llm_sql_code = first_choice.message.content.strip()
                    print("Debug - Successfully extracted content")
                else:
                    # Fallback if structure is different
                    llm_sql_code = str(first_choice)
                    print("Debug - Used fallback content extraction")
            else:
                # Handle unexpected response structure
                llm_sql_code = str(response)
                print("Debug - Response doesn't have expected choices structure")

        except Exception as e:
            print(f"Debug - Exception during Groq API call: {e}")
            print(f"Debug - Exception type: {type(e)}")
            return {"success": False, "message": f"Groq LLM call failed: {str(e)}"}

        # Clean and fix the SQL code
        clean_sql = self.clean_and_fix_sql(llm_sql_code)

        # Generate INSERT statements separately
        insert_statements = self._generate_insert_statements(df, table_name)

        # Combine CREATE TABLE and INSERT statements
        complete_sql = clean_sql
        if insert_statements:
            complete_sql += '\n\n' + insert_statements

        # Split and execute SQL statements
        statements = [stmt.strip() for stmt in complete_sql.split(';') if stmt.strip()]
        success = True
        executed_statements = []
        failed_statements = []

        for stmt in statements:
            try:
                print(f"Executing SQL: {stmt[:100]}...")  # Debug log
                result = db.execute_query(stmt + ';')
                if result:
                    executed_statements.append(stmt)
                    print(f"✓ Successfully executed: {stmt[:50]}...")
                else:
                    success = False
                    failed_statements.append(stmt)
                    print(f"✗ SQL execution failed for: {stmt[:50]}...")
            except Exception as e:
                print(f"Execution error: {e}")
                print(f"Failed statement: {stmt}")
                failed_statements.append(stmt)
                success = False

        if success:
            return {
                "success": True,
                "message": f"CSV processed and loaded into table '{table_name}' successfully",
                "llm_sql_code": llm_sql_code,
                "clean_sql": complete_sql,
                "table_name": table_name,
                "rows_inserted": len(df),
                "executed_statements": len(executed_statements)
            }
        else:
            return {
                "success": False,
                "message": f"Failed to execute some SQL statements for table '{table_name}'. Check logs for details.",
                "llm_sql_code": llm_sql_code,
                "clean_sql": complete_sql,
                "table_name": table_name,
                "executed_statements": len(executed_statements),
                "failed_statements": len(failed_statements)
            }


# Main execution for testing
if __name__ == "__main__":
    import argparse
    import sys
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(description='Process CSV file with Groq LLM')
    parser.add_argument('csv_file', help='Path to the CSV file to process')
    args = parser.parse_args()

    # Check if file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: File '{args.csv_file}' not found.")
        sys.exit(1)

    # Initialize the service
    print("Initializing GroqCSVSQLService...")
    service = GroqCSVSQLService()

    if not service.client:
        print("Error: Failed to initialize Groq client. Please check your GROQ_API_KEY environment variable.")
        sys.exit(1)

    # Process the CSV file
    filename = os.path.basename(args.csv_file)
    print(f"Processing CSV file: {filename}")

    result = service.process_csv_with_llm(args.csv_file, filename)

    if result["success"]:
        print("✅ CSV processing completed successfully!")
        print(f"Table created: {result['table_name']}")
        print(f"Rows inserted: {result['rows_inserted']}")
        print(f"Statements executed: {result.get('executed_statements', 'N/A')}")
        if 'clean_sql' in result:
            print("\n--- Generated SQL ---")
            print(result['clean_sql'][:500] + "..." if len(result['clean_sql']) > 500 else result['clean_sql'])
    else:
        print("❌ CSV processing failed!")
        print(f"Error: {result['message']}")
        print(f"Executed statements: {result.get('executed_statements', 0)}")
        print(f"Failed statements: {result.get('failed_statements', 0)}")
        if 'clean_sql' in result:
            print("\n--- Generated SQL (for debugging) ---")
            print(result['clean_sql'][:500] + "..." if len(result['clean_sql']) > 500 else result['clean_sql'])
