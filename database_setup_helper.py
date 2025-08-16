#!/usr/bin/env python3
"""
Database Setup Helper for Chatbot Application

This script helps with common database setup tasks.
"""

import psycopg2
import sys
import os

def check_postgresql_running():
    """Check if PostgreSQL is running and accessible"""
    try:
        # Try to connect to default PostgreSQL database
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            database="postgres"
        )
        conn.close()
        print("✓ PostgreSQL is running and accessible")
        return True
    except psycopg2.OperationalError as e:
        print(f"✗ Cannot connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Check if PostgreSQL is running on port 5432")
        print("3. Verify your PostgreSQL installation")
        return False

def check_database_exists():
    """Check if the chatbot database and user exist"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            database="postgres"
        )
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='chatbot_db'")
        db_exists = cursor.fetchone() is not None

        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='chatbot_user'")
        user_exists = cursor.fetchone() is not None

        conn.close()

        if db_exists and user_exists:
            print("✓ Database and user already exist")
            return True
        else:
            print(f"Database exists: {db_exists}")
            print(f"User exists: {user_exists}")
            return False

    except Exception as e:
        print(f"Error checking database: {e}")
        return False

def test_chatbot_connection():
    """Test connection with chatbot credentials"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="chatbot_user",
            password="chatbot_password",
            database="chatbot_db"
        )
        conn.close()
        print("✓ Chatbot database connection successful")
        return True
    except psycopg2.OperationalError as e:
        print(f"✗ Chatbot database connection failed: {e}")
        return False

def main():
    print("Chatbot Database Setup Helper")
    print("=" * 40)

    # Check PostgreSQL
    if not check_postgresql_running():
        sys.exit(1)

    # Check database setup
    if not check_database_exists():
        print("\nTo set up the database, run the following commands as PostgreSQL superuser:")
        print("psql -U postgres -f setup_database.sql")
        print("\nOr run each command manually:")
        print("1. psql -U postgres")
        print("2. Run the commands from setup_database.sql")
        sys.exit(1)

    # Test connection
    if test_chatbot_connection():
        print("\n✓ All database checks passed! Your setup is ready.")
    else:
        print("\n✗ Database connection test failed. Please check your setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()
