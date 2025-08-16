# Chatbot Application

A Flask-based chatbot application with file processing capabilities, vector search, and user management.

## Features

- User authentication and authorization
- File upload and processing (Excel, text files)
- Vector-based document search using FAISS
- AI-powered chat responses using Groq API
- Admin panel for file management

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd chatbot_app
```

### 2. Create Virtual Environment

```bash
python -m venv chatbotenv
# On Windows:
chatbotenv\Scripts\activate
# On macOS/Linux:
source chatbotenv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

**Important:** Make sure PostgreSQL is running on port 5432 (default port).

#### Quick Setup Check

Run the database setup helper to check your configuration:

```bash
python database_setup_helper.py
```

#### Option A: Automated Setup (Recommended)

1. Install PostgreSQL if not already installed
2. Start PostgreSQL service
3. Run the database setup script as postgres user:

```bash
psql -U postgres -f setup_database.sql
```

#### Option B: Manual Database Setup

1. Connect to PostgreSQL as superuser:

```bash
psql -U postgres
```

2. Run the following commands:

```sql
CREATE DATABASE chatbot_db;
CREATE USER chatbot_user WITH PASSWORD 'chatbot_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;
\c chatbot_db;
GRANT ALL ON SCHEMA public TO chatbot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chatbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chatbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chatbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO chatbot_user;
```

#### Troubleshooting Database Issues

1. **Port Issues**: PostgreSQL typically runs on port 5432. If you're using a different port, update the `DATABASE_URL` in your configuration.

2. **Connection Test**: Use the helper script to test your database connection:

   ```bash
   python database_setup_helper.py
   ```

3. **Password Authentication**: If you get "password authentication failed", ensure:
   - PostgreSQL is configured to accept password authentication
   - The user and password are correct
   - The database exists

### 5. Environment Configuration

Create a `.env` file in the root directory (or set environment variables):

```env
# Application Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
JWT_SECRET_KEY=jwt-secret-string-change-this-in-production

# Database Configuration
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_db

# Groq API Configuration
GROQ_API_KEY=your-groq-api-key-here

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=True
```

### 6. Get Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Create an account or sign in
3. Generate an API key
4. Add it to your `.env` file or `api_keys.txt`

## Running the Application

### Backend (Flask API)

```bash
cd backend
python app.py
```

The backend will start on `http://localhost:5000`

### Frontend (Streamlit)

```bash
cd frontend
streamlit run app.py
```

The frontend will start on `http://localhost:8501`

## API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### User Routes

- `GET /user/profile` - Get user profile
- `POST /user/upload` - Upload file
- `POST /user/chat` - Chat with AI

### Admin Routes

- `GET /admin/files` - List all uploaded files
- `DELETE /admin/files/{id}` - Delete file
- `GET /admin/users` - List all users

## Troubleshooting

### Common Issues

1. **Database Connection Error**

   **Symptoms:** "password authentication failed" or "could not connect to server"

   **Solutions:**

   - Run `python database_setup_helper.py` to diagnose the issue
   - Ensure PostgreSQL is running on port 5432: `sudo systemctl status postgresql` (Linux) or check Windows Services
   - Check database credentials in `backend/config.py` - default port should be 5432, not 5433
   - Verify database and user exist by running `setup_database.sql`
   - For Windows users: ensure PostgreSQL service is started

   **Quick fix:** If you see port 5433 in the error, the configuration has been updated to use the correct port 5432.

2. **Import Error with sentence-transformers**

   - This has been fixed with compatible package versions
   - Reinstall requirements: `pip install -r requirements.txt --upgrade`

3. **Missing API Key**

   - Add your Groq API key to `.env` file or `api_keys.txt`

4. **Port Already in Use**
   - Change port in `backend/app.py` (line 37)
   - Or stop the process using the port

### Database Reset

If you need to reset the database:

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS chatbot_db;"
psql -U postgres -f setup_database.sql
```

## Project Structure

```
chatbot_app/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   ├── models/
│   │   ├── database.py     # Database connection and models
│   │   └── user.py         # User model
│   ├── routes/
│   │   ├── auth.py         # Authentication routes
│   │   ├── admin.py        # Admin routes
│   │   └── user.py         # User routes
│   └── services/
│       ├── file_processor.py  # File processing service
│       ├── llm_service.py     # LLM integration
│       └── vector_service.py  # Vector database service
├── frontend/
│   └── app.py              # Streamlit frontend
├── uploads/                # File upload directory
├── vector_db/              # Vector database storage
├── requirements.txt        # Python dependencies
├── setup_database.sql      # Database setup script
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.
