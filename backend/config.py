import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_db'

    # Groq API Configuration
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

    @staticmethod
    def validate_config():
        """Validate that required environment variables are set"""
        required_vars = ['GROQ_API_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        return True

    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Vector Database Configuration
    VECTOR_DB_PATH = 'vector_db'
