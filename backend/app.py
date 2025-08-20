from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from datetime import timedelta

from models.database import init_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user import user_bp
from config import Config
from services.vector_service import VectorService
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)

    # Initialize database
    init_db()
    try:
        print("Initializing vector model at startup...")
        VectorService()  # This triggers model download/initialization
        print("Vector model initialized successfully (or already available).")
    except Exception as e:
        print(f"Warning: Failed to initialize vector model at startup: {e}")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
