from flask import Blueprint, request, jsonify
from pathlib import Path
from chatbot_service import chatbot_service
from chatbot_status_manager import chatbot_status_manager
from dialogue_storage import get_dialogue_storage
from session_manager import ip_session_manager
from widget_registry import resolve_widget
from tenant_context import (
    set_user_data_dir, clear_user_data_dir,
    set_current_kb_id, clear_current_kb_id,
    set_current_tenant_id
)
from auth import get_current_user_data_dir
from app.blueprints.kb_api import get_current_kb_id  # now respects overrides

public_chatbot_api_bp = Blueprint('public_chatbot_api', __name__)

@public_chatbot_api_bp.route('/public/widget/<widget_id>/chatbot', methods=['POST'])
def public_chatbot(widget_id):
    payload = request.get_json() or {}
    message = (payload.get('message') or '').strip()
    session_id = payload.get('session_id')  # optional; rule is IP=1 session per widget

    if not message:
        return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400

    widget = resolve_widget(widget_id)
    if not widget:
        return jsonify({'success': False, 'error': 'Widget not found'}), 404

    # Set tenant context for this request
    set_current_tenant_id(widget['tenant_id'])
    set_user_data_dir(Path(widget['user_data_dir']))
    # Do NOT set current_kb_id override; we use the owner’s current_kb.json

    try:
        if chatbot_status_manager.is_chatbot_stopped():
            return jsonify({
                'success': False,
                'error': chatbot_status_manager.get_stop_message(),
                'chatbot_stopped': True
            }), 503

        # 1) Ensure the FIRST public interaction starts on "default"
        dialogue_storage = get_dialogue_storage()
        client_ip = ip_session_manager.get_client_ip()
        existing = dialogue_storage.get_session_by_ip(client_ip)
        if not existing:
            sid = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id="default",
                kb_name="База знаний по умолчанию"
            )
            chatbot_service.set_current_session_id(sid)

        # 2) __RESET__ -> new session on default (do NOT touch files)
        if message == "__RESET__":
            new_session_id = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id="default",
                kb_name="База знаний по умолчанию"
            )
            chatbot_service.set_current_session_id(new_session_id)
            return jsonify({
                'success': True,
                'response': '✅ Switched to default knowledge base (session-scoped).',
                'session_id': new_session_id
            })

        # 3) KB password -> find KB and create a NEW session on it (no file writes)
        from kb_locator import find_kb_by_password_in_dir
        kb_id = find_kb_by_password_in_dir(Path(widget['user_data_dir']), message)
        if kb_id:
            user_data_dir = Path(widget['user_data_dir'])
            kb_dir = user_data_dir / "knowledge_bases" / kb_id
            kb_name = kb_id
            kb_info_file = kb_dir / "kb_info.json"
            if kb_info_file.exists():
                import json
                info = json.loads(kb_info_file.read_text(encoding="utf-8"))
                kb_name = info.get('name', kb_id)

            new_session_id = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id=kb_id,
                kb_name=kb_name
            )
            chatbot_service.set_current_session_id(new_session_id)

            return jsonify({
                'success': True,
                'response': f"✅ Switched to knowledge base '{kb_name}' (session-scoped).",
                'session_id': new_session_id
            })

        # Normal chat
        response_text = chatbot_service.generate_response(message, session_id)
        return jsonify({
            'success': True,
            'response': response_text,
            'session_id': chatbot_service.get_current_session_id()
        })

    finally:
        # Avoid context leaking across requests
        clear_user_data_dir()
        clear_current_kb_id()
