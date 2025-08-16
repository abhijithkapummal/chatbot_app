import pandas as pd
import os
from groq import Groq
from config import Config

class LLMService:
    def __init__(self):
        # Clear any proxy-related environment variables that might interfere
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os.environ:
                del os.environ[var]

        self.client = None
        self.model = "mixtral-8x7b-32768"
        self.groq_available = False

        try:
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            self.groq_available = True
            print("Groq client initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            print("Falling back to basic responses")

    def generate_create_table(self, df, table_name):
        # Analyze DataFrame structure
        schema_info = []
        for col in df.columns:
            dtype = df[col].dtype
            if dtype == 'object':
                max_length = df[col].astype(str).str.len().max()
                sql_type = f"VARCHAR({min(max_length + 50, 255)})"
            elif dtype in ['int64', 'int32']:
                sql_type = "INTEGER"
            elif dtype in ['float64', 'float32']:
                sql_type = "DECIMAL(10,2)"
            elif dtype == 'bool':
                sql_type = "BOOLEAN"
            else:
                sql_type = "TEXT"

            schema_info.append(f"{col} {sql_type}")

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            {', '.join(schema_info)}
        );
        """

        return create_sql

    def generate_insert_statements(self, df, table_name):
        # Generate INSERT statement
        columns = ', '.join(df.columns)
        values_list = []

        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append('NULL')
                elif isinstance(val, str):
                    values.append(f"'{val.replace(chr(39), chr(39)+chr(39))}'")  # Escape single quotes
                else:
                    values.append(str(val))
            values_list.append(f"({', '.join(values)})")

        insert_sql = f"""
        INSERT INTO {table_name} ({columns}) VALUES
        {', '.join(values_list)};
        """

        return insert_sql

    def generate_chat_response(self, message, context):
        try:
            # Prepare context from vector search results
            context_text = ""
            if context:
                context_text = "\n".join([doc.get('content', '') for doc in context])

            prompt = f"""
            You are a helpful AI assistant. Use the following context to answer the user's question.
            If the context doesn't contain relevant information, provide a general helpful response.

            Context:
            {context_text}

            User Question: {message}

            Please provide a helpful and informative response:
            """

            if self.groq_available and self.client:
                try:
                    response = self.client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=self.model,
                        max_tokens=1024,
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as groq_error:
                    print(f"Groq API error: {groq_error}")
                    self.groq_available = False  # Disable Groq for future requests

            # Fallback response when Groq is not available
            if context_text:
                return f"Based on the available information: {context_text[:500]}...\n\nRegarding your question '{message}', I found some relevant context above that might help answer your question."
            else:
                return f"Thank you for your question: '{message}'. I'm here to help! Unfortunately, the AI service is currently unavailable, but I can provide basic responses. Could you please rephrase your question or try again later?"

        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
