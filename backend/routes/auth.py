from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type', 'regular')

        if not all([username, email, password]):
            return jsonify({"message": "Missing required fields"}), 400

        # Check if user already exists
        existing_user = User.find_by_username(username)
        if existing_user:
            return jsonify({"message": "Username already exists"}), 400

        # Create new user
        user = User(username, email, password, user_type)
        user_id = user.save()

        if user_id:
            return jsonify({"message": "User created successfully", "user_id": user_id}), 201
        else:
            return jsonify({"message": "Failed to create user"}), 500

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user_type = data.get('user_type')

        if not all([username, password, user_type]):
            return jsonify({"message": "Missing required fields"}), 400

        # Find user
        user = User.find_by_username(username)
        if not user:
            return jsonify({"message": "Invalid credentials"}), 401

        # Verify password and user type
        if not User.verify_password(user['password_hash'], password):
            return jsonify({"message": "Invalid credentials"}), 401

        if user['user_type'] != user_type:
            return jsonify({"message": "Invalid user type"}), 401

        # Create access token
        access_token = create_access_token(
            identity=str(user['id']),
            additional_claims={'username': username, 'user_type': user_type}
        )

        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "user_type": user_type
        }), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
