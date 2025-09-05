from flask import Blueprint, request, jsonify
from auth import admin_required, auth
import json

admin_api_bp = Blueprint('admin_api', __name__)

@admin_api_bp.route('/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    """API endpoint to get all users (admin only)."""
    try:
        users = auth.get_all_users()
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        print(f"Error in admin_get_users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/admin/stop-user-bots', methods=['POST'])
@admin_required
def admin_stop_user_bots():
    """API endpoint to stop all bots for a specific user (admin only)."""
    try:
        data = request.get_json()
        username = data.get('username')
        message = data.get('message', 'Все ваши боты приостановлены админом')
        
        if not username:
            return jsonify({'error': 'Имя пользователя не указано'}), 400
        
        # Check if user exists
        if not auth.user_exists(username):
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Import here to avoid circular imports
        from chatbot_status_manager import ChatbotStatusManager
        
        # Create a temporary status manager for the specific user
        class AdminChatbotStatusManager(ChatbotStatusManager):
            def __init__(self, target_username):
                self.target_username = target_username
                self.status_file_name = "chatbot_status.json"
            
            def get_status_file_path(self):
                """Get the path to the chatbot status file for the target user."""
                try:
                    from auth import BASE_DIR
                    user_data_dir = BASE_DIR / "user_data" / self.target_username
                    return user_data_dir / self.status_file_name
                except Exception as e:
                    print(f"Error getting status file path: {str(e)}")
                    return None
        
        # Stop bots for the target user
        status_manager = AdminChatbotStatusManager(username)
        success = status_manager.stop_chatbots(stopped_by="admin", message=message)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Все боты пользователя {username} успешно остановлены'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при остановке ботов пользователя'
            }), 500
            
    except Exception as e:
        print(f"Error in admin_stop_user_bots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/admin/start-user-bots', methods=['POST'])
@admin_required
def admin_start_user_bots():
    """API endpoint to start all bots for a specific user (admin only)."""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Имя пользователя не указано'}), 400
        
        # Check if user exists
        if not auth.user_exists(username):
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Import here to avoid circular imports
        from chatbot_status_manager import ChatbotStatusManager
        
        # Create a temporary status manager for the specific user
        class AdminChatbotStatusManager(ChatbotStatusManager):
            def __init__(self, target_username):
                self.target_username = target_username
                self.status_file_name = "chatbot_status.json"
            
            def get_status_file_path(self):
                """Get the path to the chatbot status file for the target user."""
                try:
                    from auth import BASE_DIR
                    user_data_dir = BASE_DIR / "user_data" / self.target_username
                    return user_data_dir / self.status_file_name
                except Exception as e:
                    print(f"Error getting status file path: {str(e)}")
                    return None
            
            def start_chatbots_admin_override(self) -> bool:
                """Start all chatbots for the target user (admin override - bypasses admin stop restriction)."""
                try:
                    status_file = self.get_status_file_path()
                    if not status_file:
                        return False
                    
                    status = {
                        "stopped": False,
                        "stopped_at": None,
                        "stopped_by": None,
                        "message": None
                    }
                    
                    # Ensure directory exists
                    status_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(status_file, 'w', encoding='utf-8') as f:
                        json.dump(status, f, ensure_ascii=False, indent=2)
                    
                    return True
                except Exception as e:
                    print(f"Error starting chatbots (admin override): {str(e)}")
                    return False
        
        # Start bots for the target user (admin override)
        status_manager = AdminChatbotStatusManager(username)
        success = status_manager.start_chatbots_admin_override()
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Все боты пользователя {username} успешно запущены'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при запуске ботов пользователя'
            }), 500
            
    except Exception as e:
        print(f"Error in admin_start_user_bots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/admin/bot-status', methods=['GET'])
@admin_required
def admin_get_all_bot_status():
    """API endpoint to get bot status for all users (admin only)."""
    try:
        from chatbot_status_manager import ChatbotStatusManager
        import os
        
        # Get all users
        users = auth.get_all_users()
        bot_status = {}
        
        for username in users.keys():
            if username == 'admin':  # Skip admin user
                continue
                
            # Create a temporary status manager for each user
            class AdminChatbotStatusManager(ChatbotStatusManager):
                def __init__(self, target_username):
                    self.target_username = target_username
                    self.status_file_name = "chatbot_status.json"
                
                def get_status_file_path(self):
                    """Get the path to the chatbot status file for the target user."""
                    try:
                        from auth import BASE_DIR
                        user_data_dir = BASE_DIR / "user_data" / self.target_username
                        return user_data_dir / self.status_file_name
                    except Exception as e:
                        print(f"Error getting status file path: {str(e)}")
                        return None
            
            status_manager = AdminChatbotStatusManager(username)
            status = status_manager.get_chatbot_status()
            
            bot_status[username] = {
                'stopped': status.get('stopped', False),
                'stopped_by': status.get('stopped_by'),
                'message': status.get('message'),
                'stopped_at': status.get('stopped_at')
            }
        
        return jsonify({
            'success': True,
            'bot_status': bot_status
        })
        
    except Exception as e:
        print(f"Error in admin_get_all_bot_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/admin/balances', methods=['GET'])
@admin_required
def admin_get_all_balances():
    """API endpoint to get all user balances (admin only)."""
    try:
        from balance_manager import balance_manager
        result = balance_manager.admin_get_all_balances()
        return jsonify(result)
    except Exception as e:
        print(f"Error in admin_get_all_balances: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/admin/balance/increase', methods=['POST'])
@admin_required
def admin_increase_balance():
    """API endpoint to increase user balance (admin only)."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        amount_rub = data.get('amount_rub', 0.0)
        reason = data.get('reason', 'Manual balance increase')
        
        if not username:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        
        if amount_rub <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        from balance_manager import balance_manager
        result = balance_manager.admin_increase_balance(username, amount_rub, reason)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in admin_increase_balance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_api_bp.route('/admin/user/<username>/balance', methods=['GET'])
@admin_required
def admin_get_user_balance(username):
    """API endpoint to get specific user balance (admin only)."""
    try:
        if not auth.user_exists(username):
            return jsonify({'success': False, 'error': f'User {username} does not exist'}), 404
        
        from balance_manager import balance_manager
        balance_data = balance_manager.get_balance(username)
        transactions = balance_manager.get_transactions(10, username)  # Last 10 transactions
        
        return jsonify({
            'success': True,
            'balance': balance_data,
            'recent_transactions': transactions
        })
    except Exception as e:
        print(f"Error in admin_get_user_balance: {str(e)}")
        return jsonify({'error': str(e)}), 500
