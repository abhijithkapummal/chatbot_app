import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
from config import Config

class Database:
    def __init__(self):
        self.connection = None
        self.connected = False
        self.connect()

    def connect(self, max_retries=3, retry_delay=2):
        """Connect to database with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to database... (attempt {attempt + 1}/{max_retries})")
                self.connection = psycopg2.connect(
                    Config.DATABASE_URL,
                    cursor_factory=RealDictCursor
                )
                self.connection.autocommit = True
                self.connected = True
                print("Database connected successfully!")
                return True
            except psycopg2.OperationalError as e:
                error_msg = str(e).lower()
                if "password authentication failed" in error_msg:
                    print(f"Database authentication error: {e}")
                    print("Please check your database credentials in the configuration.")
                elif "could not connect to server" in error_msg:
                    print(f"Database server connection error: {e}")
                    print("Please make sure PostgreSQL is running.")
                else:
                    print(f"Database operational error: {e}")

                print(f"Connection string: {Config.DATABASE_URL}")

                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Database connection failed.")
                    self.connected = False
                    return False
            except Exception as e:
                print(f"Unexpected database error: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Database connection failed.")
                    self.connected = False
                    return False

    def execute_query(self, query, params=None, fetch=False):
        if not self.connected or not self.connection:
            print("Database not connected. Attempting to reconnect...")
            if not self.reconnect():
                print("Failed to reconnect to database. Cannot execute query.")
                return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)

            if fetch:
                if fetch == 'one':
                    return cursor.fetchone()
                else:
                    return cursor.fetchall()
            return True
        except psycopg2.OperationalError as e:
            print(f"Database connection lost during query: {e}")
            print("Attempting to reconnect...")
            if self.reconnect():
                # Retry the query once after reconnection
                try:
                    cursor = self.connection.cursor()
                    cursor.execute(query, params)
                    if fetch:
                        if fetch == 'one':
                            return cursor.fetchone()
                        else:
                            return cursor.fetchall()
                    return True
                except Exception as retry_e:
                    print(f"Query failed after reconnection: {retry_e}")
                    return None
            else:
                print("Failed to reconnect. Query execution failed.")
                return None
        except Exception as e:
            print(f"Query execution error: {e}")
            return None

    def reconnect(self):
        """Reconnect to database if connection is lost"""
        self.close()
        return self.connect()

    def is_connected(self):
        """Check if database connection is still alive"""
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT 1;')
            return True
        except:
            return False

    def close(self):
        if self.connection:
            self.connection.close()
            self.connected = False

# Global database instance
db = Database()

def init_db():
    if not db.connected:
        print("Skipping database initialization - no database connection")
        return False

    # Create users table
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(80) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        user_type VARCHAR(20) NOT NULL DEFAULT 'regular',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Create file_uploads table
    create_uploads_table = """
    CREATE TABLE IF NOT EXISTS file_uploads (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        file_type VARCHAR(10) NOT NULL,
        file_size INTEGER NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        uploaded_by INTEGER REFERENCES users(id),
        processing_status VARCHAR(20) DEFAULT 'pending'
    );
    """

    success1 = db.execute_query(create_users_table)
    success2 = db.execute_query(create_uploads_table)

    if success1 and success2:
        print("Database tables initialized successfully!")
        return True
    else:
        print("Failed to initialize some database tables")
        return False
