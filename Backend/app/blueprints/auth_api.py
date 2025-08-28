from flask import Blueprint, request, jsonify, session
from auth import auth

auth_api_bp = Blueprint('auth_api', __name__)

@auth_api_bp.route('/signup', methods=['POST'])
def api_signup():
    """API endpoint for user registration."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    
    result = auth.register_user(username, password, email)
    return jsonify(result)

@auth_api_bp.route('/login', methods=['POST'])
def api_login():
    """API endpoint for user login."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    result = auth.login_user(username, password)
    
    if result['success']:
        session['username'] = username
        session['user_data_dir'] = result['data_directory']
    
    return jsonify(result)

@auth_api_bp.route('/logout', methods=['POST'])
def api_logout():
    """API endpoint for user logout."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

# ===== STANDALONE HTML CHATBOT API ENDPOINTS =====

@auth_api_bp.route('/standalone/login', methods=['POST'])
def standalone_login():
    """API endpoint for standalone HTML chatbot login (token-based)."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    result = auth.login_user(username, password)
    
    if result['success']:
        # Return session token for standalone use
        return jsonify({
            "success": True,
            "username": username,
            "session_token": result['session_token'],
            "data_directory": result['data_directory'],
            "is_admin": result.get('is_admin', False)
        })
    
    return jsonify(result)

@auth_api_bp.route('/standalone/balance', methods=['GET'])
def standalone_get_balance():
    """Get user balance for standalone HTML chatbot."""
    # Get token from header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header required"}), 401
    
    token = auth_header.split(' ')[1]
    
    # Validate token and get user info
    # For now, we'll use a simple approach - you can enhance this later
    try:
        # Get username from request args (temporary solution)
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        # Get balance using existing balance manager
        from balance_manager import balance_manager
        balance = balance_manager.get_balance(username)
        return jsonify({"balance": balance})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_api_bp.route('/standalone/model', methods=['GET'])
def standalone_get_model():
    """Get user model for standalone HTML chatbot."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header required"}), 401
    
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        # Get model from model manager
        from model_manager import model_manager
        model_config = model_manager.get_model_config(username)
        return jsonify({"model": model_config.get('model', 'GPT-4')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_api_bp.route('/standalone/clear', methods=['POST'])
def standalone_clear_chat():
    """Clear chat history for standalone HTML chatbot."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header required"}), 401
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    try:
        # Import standalone chatbot service
        from standalone_chatbot_service import standalone_chatbot_service
        
        # Clear user session
        standalone_chatbot_service.clear_user_session(username)
        
        return jsonify({"success": True, "message": "История чата очищена"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_api_bp.route('/standalone/chatbot', methods=['POST'])
def standalone_chatbot():
    """Chatbot API for standalone HTML chatbot."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header required"}), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    username = data.get('username', '').strip()
    
    if not message or not username:
        return jsonify({"error": "Message and username required"}), 400
    
    try:
        # Import standalone chatbot service
        from standalone_chatbot_service import standalone_chatbot_service
        
        # Use standalone chatbot service
        response = standalone_chatbot_service.generate_response(username, message)
        
        # Get updated balance
        from balance_manager import balance_manager
        balance = balance_manager.get_balance(username)
        
        return jsonify({
            "response": response,
            "balance": balance
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
