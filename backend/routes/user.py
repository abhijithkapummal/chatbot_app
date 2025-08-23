from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from agents.workflow import get_workflow

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

        # Get the agentic workflow instance
        workflow = get_workflow()

        # Process the query through the agentic workflow
        result = workflow.process_query(message)

        # Return the response
        return jsonify({
            "success": result.get("success", True),
            "response": result.get("response"),
            "agent": result.get("agent"),
            "confidence": result.get("confidence"),
            "metadata": result.get("metadata", {}),
            "routed_to": result.get("routed_to")
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}",
            "agent": "Error",
            "confidence": 0.0
        }), 500

@user_bp.route('/chat/legacy', methods=['POST'])
@jwt_required()
def chat_legacy():
    """Legacy chat endpoint for backwards compatibility."""
    try:
        from services.llm_service import LLMService
        from services.vector_service import VectorService

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
