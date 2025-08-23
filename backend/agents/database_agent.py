"""
Database Agent - Handles queries requiring SQL database operations.
"""

import json
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from .base_agent import BaseAgent, AgentResponse
from models.database import db


class DatabaseAgent(BaseAgent):
    """
    Database Agent that analyzes queries and generates SQL to answer them.
    Dynamically inspects PostgreSQL tables and executes optimized queries.
    """

    def __init__(self):
        super().__init__("DatabaseAgent")
        self.db = db
        self._setup_tools()

    def _setup_tools(self):
        """Setup LangChain tools for database operations."""
        self.tools = [
            Tool(
                name="inspect_database_schema",
                description="Get information about available tables and their columns in the database",
                func=self._inspect_database_schema
            ),
            Tool(
                name="execute_sql_query",
                description="Execute a SQL query on the PostgreSQL database and return results",
                func=self._execute_sql_query
            ),
            Tool(
                name="validate_sql_query",
                description="Validate SQL query syntax before execution",
                func=self._validate_sql_query
            )
        ]

    def get_prompt_template(self) -> ChatPromptTemplate:
        """Return the database query analysis prompt template."""
        return ChatPromptTemplate.from_template("""
You are a Database Agent specialized in analyzing user queries and generating SQL queries to answer them.

Your process:
1. First, inspect the database schema to understand available tables and columns
2. Analyze if the user query can be answered with the available data
3. If yes, generate an optimized SQL query
4. Execute the query and format the results for the user
5. Provide a natural language response with the data

Available tools:
- inspect_database_schema: Get database table and column information
- validate_sql_query: Check SQL syntax before execution
- execute_sql_query: Run the SQL query and get results

User Query: "{query}"

Context: {context}

Instructions:
- Always inspect the schema first to understand what data is available
- Generate safe, read-only SQL queries (SELECT only, no INSERT/UPDATE/DELETE)
- Handle errors gracefully and explain what went wrong
- Format results in a user-friendly way
- If the query cannot be answered with available data, explain why

Begin by inspecting the database schema.
""")

    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this query requires database operations.
        Returns confidence score based on query analysis.
        """
        # Keywords that suggest database queries
        db_keywords = [
            'how many', 'count', 'total', 'sum', 'average', 'mean',
            'show', 'list', 'find', 'search', 'get', 'retrieve',
            'data', 'records', 'table', 'database', 'report',
            'statistics', 'stats', 'analysis', 'breakdown',
            'users', 'files', 'uploads', 'recent', 'latest'
        ]

        query_lower = query.lower()

        # Check for database-related keywords
        keyword_matches = sum(1 for keyword in db_keywords if keyword in query_lower)

        if keyword_matches >= 2:
            return 0.9
        elif keyword_matches == 1:
            return 0.6
        else:
            return 0.2

    def _inspect_database_schema(self) -> str:
        """Inspect database schema and return table/column information."""
        try:
            if not self.db.is_connected():
                return "Database is not connected"

            # Get all tables
            tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """

            tables = self.db.execute_query(tables_query, fetch=True)
            if not tables:
                return "No tables found in database"

            schema_info = {}

            for table in tables:
                table_name = table['table_name']

                # Get columns for each table
                columns_query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
                """

                columns = self.db.execute_query(columns_query, params=(table_name,), fetch=True)

                if columns:
                    schema_info[table_name] = {
                        'columns': [
                            {
                                'name': col['column_name'],
                                'type': col['data_type'],
                                'nullable': col['is_nullable'],
                                'default': col['column_default']
                            }
                            for col in columns
                        ]
                    }

                    # Get row count
                    count_query = f"SELECT COUNT(*) as count FROM {table_name};"
                    count_result = self.db.execute_query(count_query, fetch='one')
                    if count_result:
                        schema_info[table_name]['row_count'] = count_result['count']

            return json.dumps(schema_info, indent=2)

        except Exception as e:
            return f"Error inspecting database schema: {str(e)}"

    def _validate_sql_query(self, query: str) -> str:
        """Validate SQL query syntax and safety."""
        try:
            # Basic safety checks
            query_upper = query.upper().strip()

            # Only allow SELECT queries
            if not query_upper.startswith('SELECT'):
                return "Error: Only SELECT queries are allowed"

            # Check for dangerous keywords
            dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return f"Error: {keyword} operations are not allowed"

            return "Query validation passed"

        except Exception as e:
            return f"Query validation error: {str(e)}"

    def _execute_sql_query(self, query: str) -> str:
        """Execute SQL query and return formatted results."""
        try:
            # Validate first
            validation_result = self._validate_sql_query(query)
            if "Error:" in validation_result:
                return validation_result

            if not self.db.is_connected():
                return "Error: Database is not connected"

            # Execute query
            results = self.db.execute_query(query, fetch=True)

            if not results:
                return "Query executed successfully but returned no results"

            if isinstance(results, list) and len(results) > 0:
                # Format results as JSON for structured output
                formatted_results = {
                    "query": query,
                    "row_count": len(results),
                    "data": results[:100]  # Limit to first 100 rows
                }

                if len(results) > 100:
                    formatted_results["note"] = f"Showing first 100 rows out of {len(results)} total"

                return json.dumps(formatted_results, indent=2, default=str)
            else:
                return json.dumps({"query": query, "result": results}, default=str)

        except Exception as e:
            return f"Error executing SQL query: {str(e)}"

    def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process database-related query using agent tools.
        """
        try:
            if not self.llm_available:
                return AgentResponse(
                    agent_name=self.agent_name,
                    content="Database Agent is currently unavailable due to LLM service issues.",
                    confidence=0.0
                )

            # Create the prompt
            prompt_template = self.get_prompt_template()
            formatted_prompt = self._create_prompt(
                prompt_template,
                query=query,
                context=context or {}
            )

            # For now, let's implement a simplified version without ReActAgent
            # as it requires more complex setup

            # Step 1: Inspect database schema
            schema_info = self._inspect_database_schema()

            # Step 2: Generate SQL query using LLM
            sql_generation_prompt = f"""
Based on the database schema below, generate a SQL query to answer the user's question.

Database Schema:
{schema_info}

User Question: {query}

Rules:
- Only generate SELECT queries
- Use proper table and column names from the schema
- Include appropriate WHERE, GROUP BY, ORDER BY clauses as needed
- Limit results to reasonable amounts (use LIMIT if needed)

Generate only the SQL query, no explanations:
"""

            sql_query = self._invoke_llm(sql_generation_prompt).strip()

            # Clean up the SQL query (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()

            # Step 3: Execute the query
            query_results = self._execute_sql_query(sql_query)

            # Step 4: Generate natural language response
            response_prompt = f"""
The user asked: "{query}"

The SQL query generated was: {sql_query}

The query results were: {query_results}

Please provide a natural language response to the user's question based on these results.
If there was an error, explain it clearly. If the results are empty, explain that no data was found.
Format any data in a readable way.
"""

            natural_response = self._invoke_llm(response_prompt)

            return AgentResponse(
                agent_name=self.agent_name,
                content=natural_response,
                metadata={
                    "sql_query": sql_query,
                    "raw_results": query_results,
                    "schema_used": schema_info[:500] + "..." if len(schema_info) > 500 else schema_info
                },
                confidence=0.8
            )

        except Exception as e:
            return AgentResponse(
                agent_name=self.agent_name,
                content=f"I encountered an error while processing your database query: {str(e)}",
                metadata={"error": str(e)},
                confidence=0.0
            )
