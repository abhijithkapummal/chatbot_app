from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.llm_service import LLMService
from services.vector_service import VectorService

user_bp = Blueprint('user', __name__)

@user_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        data = request.get_json()
        message = data.get('message')

        if not message:
            return jsonify({"message": "No message provided"}), 400

        # Initialize services
        llm_service = LLMService()
        vector_service = VectorService()

        # Search for relevant context in vector database
        context = vector_service.search(message, top_k=3)

        # Generate response using LLM
        response = llm_service.generate_chat_response(message, context)

        return jsonify({"response": response}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
