import pandas as pd
import os
from services.llm_service import LLMService
from services.vector_service import VectorService
from models.database import db

class FileProcessor:
    def __init__(self):
        self.llm_service = LLMService()
        self.vector_service = VectorService()

    def process_csv(self, file_path, filename):
        try:
            # Read CSV file
            try:
                df = pd.read_csv(file_path)
            except pd.errors.EmptyDataError:
                return {
                    "success": False,
                    "message": "CSV file is empty."
                }
            except pd.errors.ParserError as e:
                return {
                    "success": False,
                    "message": f"CSV parsing error: {str(e)}"
                }

            # Check if DataFrame is empty
            if df.empty:
                return {
                    "success": False,
                    "message": "CSV file contains no data rows."
                }

            # Generate table name from filename
            table_name = filename.replace('.csv', '').lower().replace(' ', '_').replace('-', '_')

            # Remove any non-alphanumeric characters except underscores
            import re
            table_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name)

            # Ensure table name starts with a letter
            if not table_name[0].isalpha():
                table_name = 'table_' + table_name

            # Generate CREATE TABLE statement using LLM
            create_sql = self.llm_service.generate_create_table(df, table_name)

            if not create_sql:
                return {
                    "success": False,
                    "message": "Failed to generate CREATE TABLE statement."
                }

            # Execute CREATE TABLE (only if database is connected)
            if not db.connected:
                return {
                    "success": False,
                    "message": "Database not connected. CSV processing requires database connection."
                }

            create_result = db.execute_query(create_sql)
            if not create_result:
                return {
                    "success": False,
                    "message": "Failed to create database table."
                }

            # Generate and execute INSERT statements
            insert_sql = self.llm_service.generate_insert_statements(df, table_name)

            if not insert_sql:
                return {
                    "success": False,
                    "message": "Failed to generate INSERT statements."
                }

            insert_result = db.execute_query(insert_sql)
            if not insert_result:
                return {
                    "success": False,
                    "message": "Failed to insert data into database table."
                }

            return {
                "success": True,
                "message": f"CSV file processed successfully. Table '{table_name}' created with {len(df)} rows.",
                "table_name": table_name,
                "rows_inserted": len(df)
            }

        except FileNotFoundError:
            return {
                "success": False,
                "message": "File not found after upload."
            }
        except PermissionError:
            return {
                "success": False,
                "message": "Permission denied when reading file."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing CSV: {str(e)}"
            }

    def process_txt(self, file_path, filename):
        try:
            # Read text file with multiple encoding attempts
            content = None
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return {
                    "success": False,
                    "message": "Could not decode file. Please ensure it's a valid text file."
                }

            # Check if file is empty
            if not content.strip():
                return {
                    "success": False,
                    "message": "Text file is empty or contains only whitespace."
                }

            # Get file metadata
            file_size = os.path.getsize(file_path)

            # Store in vector database
            success = self.vector_service.add_document(
                content=content,
                metadata={
                    "filename": filename,
                    "file_size": file_size,
                    "upload_date": str(pd.Timestamp.now())
                }
            )

            if not success:
                return {
                    "success": False,
                    "message": "Failed to store content in vector database."
                }

            return {
                "success": True,
                "message": f"Text file processed successfully. Content stored in vector database.",
                "filename": filename,
                "content_length": len(content)
            }

        except FileNotFoundError:
            return {
                "success": False,
                "message": "File not found after upload."
            }
        except PermissionError:
            return {
                "success": False,
                "message": "Permission denied when reading file."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing TXT: {str(e)}"
            }
