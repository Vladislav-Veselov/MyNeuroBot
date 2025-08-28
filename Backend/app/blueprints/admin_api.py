from flask import Blueprint, request, jsonify
from auth import admin_required, auth

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
