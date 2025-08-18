import pandas as pd
import json
import re

from groq import Groq
from config import Config
from models.database import db

class GroqCSVSQLService:
    """
    Service for handling CSV file processing using Groq Llama3-70b-8192.
    This will:
      - read the CSV
      - use LLM to generate SQL for table creation/insertion
      - execute SQL in the PostgreSQL db initialized with username 'postgres'
    """

    def __init__(self):
        self.model = "llama3-70b-8192"
        try:
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            print("Groq client initialized for CSV-to-SQL tasks.")
        except Exception as e:
            print(f"Error initializing Groq client: {e}")
            self.client = None

    def clean_and_fix_sql(self, llm_sql_code):
        """
        Extract clean SQL code from LLM response and fix reserved keywords and type issues.
        """
        # Extract SQL code blocks between triple backticks (preferred if present)
        code_blocks = re.findall(r'```(?:sql)?\s*(.*?)```', llm_sql_code, re.DOTALL | re.IGNORECASE)
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
        sql_code = re.sub(r'NUMERIC\(5,2\)', 'NUMERIC(10,2)', sql_code)

        # Clean up extra whitespace and empty lines
        sql_code = re.sub(r'\n\s*\n', '\n', sql_code)
        sql_code = re.sub(r'^\s*\n', '', sql_code, flags=re.MULTILINE)  # Remove empty lines at start

        return sql_code.strip()

    def process_csv_with_llm(self, file_path, filename):
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
        if not table_name[0].isalpha():
            table_name = 'table_' + table_name

        # Prepare DataFrame metadata for LLM prompt
        sample = df.head(3).to_dict(orient="records")
        prompt = (
          f"You are a PostgreSQL expert. Given the following CSV file information, generate valid SQL "
          f"statements to (1) create a table (use 'CREATE TABLE IF NOT EXISTS') and (2) insert all rows from the CSV. "
          f"Table name: {table_name}\n"
          f"Columns: {', '.join(df.columns)}\n"
          f"Sample Data:\n{json.dumps(sample, indent=2)}\n\n"
          f"Requirements:\n- Use correct SQL data types for each column\n"
          f"- Use the above table name and columns\n"
          f"- Only output SQL code for CREATE TABLE IF NOT EXISTS and INSERT statements\n"
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
            llm_sql_code = response.choices[0].message.content.strip()
        except Exception as e:
            return {"success": False, "message": f"Groq LLM call failed: {str(e)}"}

        # Clean and fix the SQL code
        clean_sql = self.clean_and_fix_sql(llm_sql_code)

        # Split and execute SQL statements
        statements = [stmt.strip() for stmt in clean_sql.split(';') if stmt.strip()]
        success = True
        executed_statements = []

        for stmt in statements:
            try:
                print(f"Executing SQL: {stmt[:100]}...")  # Debug log
                result = db.execute_query(stmt + ';')
                if not result:
                    success = False
                    print(f"SQL execution failed for: {stmt[:50]}...")
                else:
                    executed_statements.append(stmt)
            except Exception as e:
                print(f"Execution error: {e}")
                print(f"Failed statement: {stmt}")
                success = False

        if success:
            return {
                "success": True,
                "message": f"CSV processed and loaded into table '{table_name}'",
                "llm_sql_code": llm_sql_code,
                "clean_sql": clean_sql,
                "table_name": table_name,
                "rows_inserted": len(df)
            }
        else:
            return {
                "success": False,
                "message": f"Failed to execute SQL for table '{table_name}'. See logs for details.",
                "llm_sql_code": llm_sql_code,
                "clean_sql": clean_sql
            }
