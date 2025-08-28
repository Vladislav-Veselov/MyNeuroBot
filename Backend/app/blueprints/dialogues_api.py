from flask import Blueprint, request, jsonify, Response
from auth import login_required
from dialogue_storage import get_dialogue_storage
from session_manager import ip_session_manager

dialogues_api_bp = Blueprint('dialogues_api', __name__)

@dialogues_api_bp.route('/dialogues', methods=['GET'])
@login_required
def get_dialogues():
    """API endpoint to get all dialogue sessions."""
    try:
        dialogue_storage = get_dialogue_storage()
        sessions = dialogue_storage.get_all_sessions()
        return jsonify({
            'success': True,
            'sessions': sessions
        })
        
    except Exception as e:
        print(f"Error getting dialogues: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/<session_id>', methods=['GET'])
@login_required
def get_dialogue(session_id):
    """Get a specific dialogue session."""
    try:
        dialogue_storage = get_dialogue_storage()
        session = dialogue_storage.get_session(session_id)
        if session:
            # Mark the session as read when it's opened
            dialogue_storage.mark_session_as_read(session_id)
            return jsonify(session)
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        print(f"Error getting dialogue session {session_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/<session_id>', methods=['DELETE'])
@login_required
def delete_dialogue(session_id):
    """API endpoint to delete a specific dialogue session."""
    try:
        dialogue_storage = get_dialogue_storage()
        success = dialogue_storage.delete_session(session_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Сессия удалена'
            })
        else:
            return jsonify({'error': 'Сессия не найдена'}), 404
            
    except Exception as e:
        print(f"Error deleting dialogue {session_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/clear-all', methods=['DELETE'])
@login_required
def clear_all_dialogues():
    """API endpoint to clear all dialogue sessions."""
    try:
        dialogue_storage = get_dialogue_storage()
        success = dialogue_storage.clear_all_sessions()
        if success:
            # Reset chatbot service session to ensure new dialogues are created
            from chatbot_service import chatbot_service
            chatbot_service.reset_session()
            return jsonify({
                'success': True,
                'message': 'Все сессии удалены'
            })
        else:
            return jsonify({'error': 'Ошибка при удалении сессий'}), 500
            
    except Exception as e:
        print(f"Error clearing all dialogues: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/stats', methods=['GET'])
@login_required
def get_dialogue_stats():
    """API endpoint to get dialogue storage statistics."""
    try:
        dialogue_storage = get_dialogue_storage()
        stats = dialogue_storage.get_storage_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error getting dialogue stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/<session_id>/potential-client', methods=['PUT'])
@login_required
def mark_potential_client(session_id):
    """API endpoint to mark a session as a potential client."""
    try:
        data = request.get_json()
        is_potential_client = data.get('potential_client', True)
        
        dialogue_storage = get_dialogue_storage()
        success = dialogue_storage.mark_session_as_potential_client(session_id, is_potential_client)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session marked as potential client' if is_potential_client else 'Session unmarked as potential client'
            })
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        print(f"Error marking session {session_id} as potential client: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/by-ip/<ip_address>', methods=['GET'])
@login_required
def get_dialogues_by_ip(ip_address):
    """Get all dialogue sessions for a specific IP address."""
    try:
        dialogue_storage = get_dialogue_storage()
        all_sessions = dialogue_storage.get_all_sessions()
        
        # Filter sessions by IP address
        ip_sessions = []
        for session in all_sessions:
            session_data = dialogue_storage.get_session(session['session_id'])
            if session_data and session_data['metadata'].get('ip_address') == ip_address:
                ip_sessions.append(session)
        
        return jsonify({
            'success': True,
            'sessions': ip_sessions,
            'ip_address': ip_address
        })
        
    except Exception as e:
        print(f"Error getting dialogues by IP {ip_address}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/current-ip', methods=['GET'])
@login_required
def get_current_ip_dialogues():
    """Get all dialogue sessions for the current request's IP address."""
    try:
        current_ip = ip_session_manager.get_client_ip()
        dialogue_storage = get_dialogue_storage()
        all_sessions = dialogue_storage.get_all_sessions()
        
        # Filter sessions by current IP address
        ip_sessions = []
        for session in all_sessions:
            session_data = dialogue_storage.get_session(session['session_id'])
            if session_data and session_data['metadata'].get('ip_address') == current_ip:
                ip_sessions.append(session)
        
        return jsonify({
            'success': True,
            'sessions': ip_sessions,
            'ip_address': current_ip
        })
        
    except Exception as e:
        print(f"Error getting current IP dialogues: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dialogues_api_bp.route('/dialogues/<session_id>/download', methods=['GET'])
@login_required
def download_dialogue(session_id):
    """Download a dialogue session as a text file."""
    try:
        dialogue_storage = get_dialogue_storage()
        session = dialogue_storage.get_session(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Format the dialogue as text
        dialogue_text = f"Сессия: {session['session_id']}\n"
        dialogue_text += f"Создано: {session['created_at']}\n"
        dialogue_text += f"Обновлено: {session['metadata']['last_updated']}\n"
        dialogue_text += f"IP адрес: {session['metadata'].get('ip_address', 'Неизвестно')}\n"
        dialogue_text += f"Всего сообщений: {session['metadata']['total_messages']}\n"
        dialogue_text += "=" * 50 + "\n\n"
        
        if session['messages']:
            for message in session['messages']:
                role = "Пользователь" if message['role'] == 'user' else "Бот"
                timestamp = message['timestamp']
                content = message['content']
                dialogue_text += f"[{timestamp}] {role}:\n{content}\n\n"
        else:
            dialogue_text += "Нет сообщений в этой сессии.\n"
        
        # Create response with proper headers for file download
        response = Response(dialogue_text, mimetype='text/plain; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename=dialogue_{session_id[:8]}.txt'
        return response
        
    except Exception as e:
        print(f"Error downloading dialogue {session_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
