from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
import os
from services.file_processor import FileProcessor
from services.llm_service import LLMService
from services.vector_service import VectorService
from models.database import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    print("current_user")
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()

        print(f"User ID: {user_id}, Claims: {claims}")
        if claims.get('user_type') != 'admin':
            return jsonify({"message": "Admin access required"}), 403

        if 'file' not in request.files:
            print(request.files)
            return jsonify({"message": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "No file selected"}), 400

        filename = secure_filename(file.filename)

        # Check if file has an extension
        if '.' not in filename:
            return jsonify({"message": "File must have an extension (.csv or .txt)"}), 400

        file_extension = filename.rsplit('.', 1)[1].lower()

        if file_extension not in ['csv', 'txt']:
            return jsonify({"message": "Unsupported file type. Only .csv and .txt files are allowed."}), 400

        # Save file
        upload_path = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(upload_path)

        # Process file based on type
        processor = FileProcessor()

        if file_extension == 'csv':
            result = processor.process_csv(upload_path, filename)
        else:  # txt
            result = processor.process_txt(upload_path, filename)

        # Log upload to database (optional - don't fail if DB is unavailable)
        try:
            if db.connected:
                log_query = """
                INSERT INTO file_uploads (filename, file_type, file_size, uploaded_by, processing_status)
                VALUES (%s, %s, %s, %s, %s);
                """
                db.execute_query(log_query, (
                    filename,
                    file_extension,
                    os.path.getsize(upload_path),
                    user_id,
                    'completed' if result['success'] else 'failed'
                ))
            else:
                print("Database not connected - skipping upload logging")
        except Exception as db_error:
            print(f"Database logging error: {db_error}")
            # Continue without failing the upload

        return jsonify(result), 200

    except FileNotFoundError as e:
        return jsonify({"message": f"File not found: {str(e)}"}), 400
    except PermissionError as e:
        return jsonify({"message": f"Permission denied: {str(e)}"}), 403
    except Exception as e:
        print(f"Upload error: {str(e)}")  # Log the error for debugging
        return jsonify({"message": f"Processing failed: {str(e)}"}), 500

@admin_bp.route('/tables', methods=['GET'])
@jwt_required()
def get_tables():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        if claims.get('user_type') != 'admin':
            return jsonify({"message": "Admin access required"}), 403

        if not db.connected:
            return jsonify({"message": "Database not connected", "tables": []}), 200

        query = """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """
        tables = db.execute_query(query, fetch=True)
        table_names = [table['table_name'] for table in tables] if tables else []

        return jsonify({"tables": table_names}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@admin_bp.route('/vectors', methods=['GET'])
@jwt_required()
def get_vector_info():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        if claims.get('user_type') != 'admin':
            return jsonify({"message": "Admin access required"}), 403

        vector_service = VectorService()
        info = vector_service.get_info()

        return jsonify(info), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@admin_bp.route('/init-model', methods=['POST'])
@jwt_required()
def initialize_model():
    """Initialize the vector model to avoid timeout on first txt upload"""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        if claims.get('user_type') != 'admin':
            return jsonify({"message": "Admin access required"}), 403

        print("Initializing vector model...")
        vector_service = VectorService()

        if vector_service.model_available:
            return jsonify({
                "success": True,
                "message": "Vector model is already initialized and ready"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Vector model initialization failed. Check server logs for details."
            }), 500

    except Exception as e:
        print(f"Model initialization error: {str(e)}")
        return jsonify({"message": f"Error initializing model: {str(e)}"}), 500