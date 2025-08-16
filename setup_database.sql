-- Database setup script for chatbot application
-- Run this script as a PostgreSQL superuser (e.g., postgres user)

-- Create database
CREATE DATABASE chatbot_db;

-- Create user
CREATE USER chatbot_user WITH PASSWORD 'chatbot_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO chatbot_user;

-- Connect to the database and grant schema privileges
\c chatbot_db;
GRANT ALL ON SCHEMA public TO chatbot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chatbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chatbot_user;

-- Make future table permissions automatic
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chatbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO chatbot_user;
