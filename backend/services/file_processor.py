import pandas as pd
import os
from services.llm_service import LLMService
from services.vector_service import VectorService
from models.database import db
from services.groq_csv_sql import GroqCSVSQLService

class FileProcessor:
    def __init__(self):
        self.llm_service = LLMService()
        self.vector_service = VectorService()
        self.groq_csv_sql = GroqCSVSQLService()


    def process_csv(self, file_path, filename):
        # Use Groq-based CSV/SQL logic
        return self.groq_csv_sql.process_csv_with_llm(file_path, filename)

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
