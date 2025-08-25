# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
# from agents.workflow import get_workflow

# user_bp = Blueprint('user', __name__)

# @user_bp.route('/chat', methods=['POST'])
# @jwt_required()
# def chat():
#     try:
#         user_id = get_jwt_identity()
#         claims = get_jwt()
#         data = request.get_json()
#         message = data.get('message')

#         if not message:
#             return jsonify({"message": "No message provided"}), 400

#         # Get the agentic workflow instance
#         workflow = get_workflow()

#         # Process the query through the agentic workflow
#         result = workflow.process_query(message)

#         # Return the response
#         return jsonify({
#             "success": result.get("success", True),
#             "response": result.get("response"),
#             "agent": result.get("agent"),
#             "confidence": result.get("confidence"),
#             "metadata": result.get("metadata", {}),
#             "routed_to": result.get("routed_to")
#         }), 200

#     except Exception as e:
#         return jsonify({
#             "success": False,
#             "message": f"Error: {str(e)}",
#             "agent": "Error",
#             "confidence": 0.0
#         }), 500

# @user_bp.route('/chat/legacy', methods=['POST'])
# @jwt_required()
# def chat_legacy():
#     """Legacy chat endpoint for backwards compatibility."""
#     try:
#         from services.llm_service import LLMService
#         from services.vector_service import VectorService

#         user_id = get_jwt_identity()
#         claims = get_jwt()
#         data = request.get_json()
#         message = data.get('message')

#         if not message:
#             return jsonify({"message": "No message provided"}), 400

#         # Initialize services
#         llm_service = LLMService()
#         vector_service = VectorService()

#         # Search for relevant context in vector database
#         context = vector_service.search(message, top_k=3)

#         # Generate response using LLM
#         response = llm_service.generate_chat_response(message, context)

#         return jsonify({"response": response}), 200

#     except Exception as e:
#         return jsonify({"message": f"Error: {str(e)}"}), 500


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from agents.workflow import get_workflow
import json
import os
from datetime import datetime

user_bp = Blueprint('user', __name__)

# Directory to store chat histories
CHAT_HISTORY_DIR = 'chat_histories'
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def get_chat_history_file(user_id):
    """Get the file path for user's chat history"""
    return os.path.join(CHAT_HISTORY_DIR, f'user_{user_id}_chat_history.json')

def load_chat_history(user_id):
    """Load existing chat history for a user"""
    file_path = get_chat_history_file(user_id)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading chat history: {e}")
            return {"user_id": user_id, "history": [], "created_at": datetime.now().isoformat()}
    else:
        return {"user_id": user_id, "history": [], "created_at": datetime.now().isoformat()}

def save_chat_history(user_id, chat_data):
    """Save chat history to JSON file"""
    file_path = get_chat_history_file(user_id)
    try:
        chat_data["last_updated"] = datetime.now().isoformat()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving chat history: {e}")
        return False

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

        # Load existing chat history
        chat_data = load_chat_history(user_id)

        # Add user message to history
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        chat_data["history"].append(user_message)

        # Get the agentic workflow instance
        workflow = get_workflow()

        # Process the query through the agentic workflow
        result = workflow.process_query(message)

        # Add bot response to history
        bot_message = {
            "role": "assistant",
            "content": result.get("response"),
            "timestamp": datetime.now().isoformat(),
            "agent": result.get("agent"),
            "confidence": result.get("confidence"),
            "routed_to": result.get("routed_to")
        }
        chat_data["history"].append(bot_message)

        # Save updated chat history
        save_chat_history(user_id, chat_data)

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

@user_bp.route('/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get chat history for the current user"""
    try:
        user_id = get_jwt_identity()
        chat_data = load_chat_history(user_id)
        return jsonify(chat_data), 200
    except Exception as e:
        return jsonify({"message": f"Error retrieving chat history: {str(e)}"}), 500

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
