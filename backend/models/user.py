from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db

class User:
    def __init__(self, username, email, password, user_type='regular'):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.user_type = user_type

    def save(self):
        query = """
        INSERT INTO users (username, email, password_hash, user_type)
        VALUES (%s, %s, %s, %s) RETURNING id;
        """
        result = db.execute_query(
            query,
            (self.username, self.email, self.password_hash, self.user_type),
            fetch='one'
        )
        return result['id'] if result else None

    @staticmethod
    def find_by_username(username):
        query = "SELECT * FROM users WHERE username = %s;"
        return db.execute_query(query, (username,), fetch='one')

    @staticmethod
    def verify_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)
