from flask import Blueprint, request, jsonify, session
from auth import login_required, get_current_user_data_dir
from chatbot_service import chatbot_service
from chatbot_status_manager import chatbot_status_manager
from model_manager import model_manager
from balance_manager import balance_manager
from dialogue_storage import get_dialogue_storage
from session_manager import ip_session_manager
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from pathlib import Path

chatbot_api_bp = Blueprint('chatbot_api', __name__)

# Initialize OpenAI client
load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def find_kb_by_password(password: str) -> str:
    """Find knowledge base by password."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases"
        
        if not kb_dir.exists():
            return None
        
        for kb_folder in kb_dir.iterdir():
            if kb_folder.is_dir():
                password_file = kb_folder / "password.txt"
                if password_file.exists():
                    with open(password_file, 'r', encoding='utf-8') as f:
                        kb_password = f.read().strip()
                    if kb_password == password:
                        return kb_folder.name
        
        return None
    except Exception as e:
        print(f"Error finding KB by password: {str(e)}")
        return None

def analyze_unread_sessions_for_potential_clients():
    """
    Analyze all unread sessions to determine if they are potential clients.
    Uses OpenAI to analyze the conversation content.
    """
    try:
        # Get dialogue storage for current user
        dialogue_storage = get_dialogue_storage()
        
        # Get all sessions
        all_sessions = dialogue_storage.get_all_sessions()
        unread_sessions = []
        
        # Filter for unread sessions that haven't been analyzed yet
        for session in all_sessions:
            if session.get('unread', False) and session.get('potential_client') is None:
                unread_sessions.append(session)
        
        if not unread_sessions:
            return {"analyzed": 0, "potential_clients": 0, "not_potential": 0}
        
        analyzed_count = 0
        potential_clients_count = 0
        not_potential_count = 0
        
        for session in unread_sessions:
            session_id = session['session_id']
            
            # Get full session data
            full_session = dialogue_storage.get_session(session_id)
            if not full_session:
                continue
            
            # Check if the session's KB allows client analysis
            kb_id = full_session.get('metadata', {}).get('kb_id')
            if kb_id:
                # Get KB info to check analyze_clients setting
                user_data_dir = get_current_user_data_dir()
                kb_dir = user_data_dir / "knowledge_bases" / kb_id
                kb_info_file = kb_dir / "kb_info.json"
                
                if kb_info_file.exists():
                    with open(kb_info_file, 'r', encoding='utf-8') as f:
                        kb_info = json.load(f)
                        analyze_clients = kb_info.get('analyze_clients', True)  # Default to True for backward compatibility
                        
                        # Skip analysis if KB is configured to not analyze clients
                        if not analyze_clients:
                            print(f"Skipping analysis for session {session_id} - KB {kb_id} has analyze_clients=False")
                            continue
            
            # Prepare conversation text for analysis
            conversation_text = ""
            
            for message in full_session['messages']:
                role = "Пользователь" if message['role'] == 'user' else "Бот"
                conversation_text += f"{role}: {message['content']}\n"
            
            # Analyze with OpenAI
            analysis_prompt = f"""
            Проанализируй следующий диалог и определи, является ли пользователь лидом для компании.

            Лид - это пользователь, который оставил свои контакты, или свой сайт, или запросил коммерческое предложение или демо. 

            Диалог:
            {conversation_text}

            Твой ответ должен состоять из одного слова капсом. Ответь только "ДА" если пользователь скорее является лидом, или "НЕТ" если скорее не является.
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Ты - аналитик, который определяет лидов для компании на основе диалогов с чат-ботом. Отвечай только ДА или НЕТ."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=10,
                    temperature=0.1
                )
                
                result = response.choices[0].message.content.strip().upper()
                is_potential_client = result == "ДА"
                
                # Track token usage for balance
                try:
                    input_tokens = response.usage.prompt_tokens
                    output_tokens = response.usage.completion_tokens
                    balance_manager.consume_tokens(input_tokens, output_tokens, "gpt-4o-mini", "client_analysis")
                    print(f"Token usage tracked for client analysis: {input_tokens} input, {output_tokens} output tokens")
                except Exception as e:
                    print(f"Error tracking token usage for client analysis: {e}")
                
                # Mark the session accordingly
                dialogue_storage.mark_session_as_potential_client(session_id, is_potential_client)
                
                analyzed_count += 1
                if is_potential_client:
                    potential_clients_count += 1
                else:
                    not_potential_count += 1
                    
            except Exception as e:
                print(f"Error analyzing session {session_id}: {str(e)}")
                continue
        
        return {
            "analyzed": analyzed_count,
            "potential_clients": potential_clients_count,
            "not_potential": not_potential_count
        }
        
    except Exception as e:
        print(f"Error in analyze_unread_sessions_for_potential_clients: {str(e)}")
        return {"analyzed": 0, "potential_clients": 0, "not_potential": 0}

# API Routes

@chatbot_api_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    """API endpoint for chatbot responses."""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id', None)
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Check if chatbots are stopped
        if chatbot_status_manager.is_chatbot_stopped():
            stop_message = chatbot_status_manager.get_stop_message()
            return jsonify({
                'success': False,
                'error': stop_message,
                'chatbot_stopped': True
            }), 503
        
        # Check for password-based KB switching
        if message == "__RESET__":
            # Reset to default KB
            user_data_dir = get_current_user_data_dir()
            with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
                json.dump({'current_kb_id': 'default'}, f, ensure_ascii=False, indent=2)
            try:
                session['current_kb_id'] = 'default'
            except Exception:
                pass
            
            # Create new session for KB switch
            dialogue_storage = get_dialogue_storage()
            client_ip = ip_session_manager.get_client_ip()
            new_session_id = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id="default",
                kb_name="База знаний по умолчанию"
            )
            chatbot_service.set_current_session_id(new_session_id)
            
            response = "✅ Переключение на базу знаний по умолчанию выполнено."
            current_session_id = chatbot_service.get_current_session_id()
            
            return jsonify({
                'success': True,
                'response': response,
                'session_id': current_session_id
            })
        
        # Check if message is a KB password
        kb_id = find_kb_by_password(message)
        if kb_id:
            # Switch to the found KB
            user_data_dir = get_current_user_data_dir()
            with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
                json.dump({'current_kb_id': kb_id}, f, ensure_ascii=False, indent=2)
            try:
                session['current_kb_id'] = kb_id
            except Exception:
                pass
            
            # Get KB name for response
            kb_dir = user_data_dir / "knowledge_bases" / kb_id
            kb_info_file = kb_dir / "kb_info.json"
            kb_name = kb_id
            if kb_info_file.exists():
                with open(kb_info_file, 'r', encoding='utf-8') as f:
                    kb_info = json.load(f)
                    kb_name = kb_info.get('name', kb_id)
            
            # Create new session for KB switch
            dialogue_storage = get_dialogue_storage()
            client_ip = ip_session_manager.get_client_ip()
            new_session_id = dialogue_storage.create_session(
                ip_address=client_ip,
                kb_id=kb_id,
                kb_name=kb_name
            )
            chatbot_service.set_current_session_id(new_session_id)
            
            response = f"✅ Переключение на базу знаний '{kb_name}' выполнено."
            current_session_id = chatbot_service.get_current_session_id()
            
            return jsonify({
                'success': True,
                'response': response,
                'session_id': current_session_id
            })
        
        # Generate response using chatbot service
        response = chatbot_service.generate_response(message, session_id)
        current_session_id = chatbot_service.get_current_session_id()
        
        return jsonify({
            'success': True,
            'response': response,
            'session_id': current_session_id
        })
        
    except Exception as e:
        print(f"Error in chatbot endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/chatbot/clear', methods=['POST'])
@login_required
def clear_chatbot_history():
    """API endpoint to clear chatbot conversation history."""
    try:
        chatbot_service.clear_history()
        return jsonify({'success': True, 'message': 'История разговора очищена'})
        
    except Exception as e:
        print(f"Error clearing chatbot history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/chatbot/new-session', methods=['POST'])
@login_required
def start_new_session():
    """API endpoint to start a new dialogue session."""
    try:
        session_id = chatbot_service.start_new_session()
        return jsonify({
            'success': True, 
            'message': 'Новая сессия создана',
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Error starting new session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/chatbot/status', methods=['GET'])
@login_required
def get_chatbot_status():
    """API endpoint to get current chatbot status."""
    try:
        status = chatbot_status_manager.get_chatbot_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        print(f"Error in get_chatbot_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/chatbot/stop', methods=['POST'])
@login_required
def stop_chatbots():
    """API endpoint to stop all chatbots for the current user."""
    try:
        data = request.get_json() or {}
        message = data.get('message', 'Чатбот временно остановлен')
        
        success = chatbot_status_manager.stop_chatbots(message=message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Чатботы успешно остановлены'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при остановке чатботов'
            }), 500
    except Exception as e:
        print(f"Error in stop_chatbots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/chatbot/start', methods=['POST'])
@login_required
def start_chatbots():
    """API endpoint to start all chatbots for the current user."""
    try:
        # Check if bots were stopped by admin
        current_status = chatbot_status_manager.get_chatbot_status()
        if current_status.get("stopped", False) and current_status.get("stopped_by") == "admin":
            return jsonify({
                'success': False,
                'error': 'Все ваши боты приостановлены админом',
                'admin_stopped': True
            }), 403
        
        success = chatbot_status_manager.start_chatbots()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Чатботы успешно запущены'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при запуске чатботов'
            }), 500
    except Exception as e:
        print(f"Error in start_chatbots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/model/config', methods=['GET'])
@login_required
def get_model_config():
    """API endpoint to get current model configuration."""
    try:
        config = model_manager.get_model_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        print(f"Error in get_model_config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/model/set', methods=['POST'])
@login_required
def set_model():
    """API endpoint to set the model for the current user."""
    try:
        data = request.get_json() or {}
        model = data.get('model')
        
        if not model:
            return jsonify({
                'success': False,
                'error': 'Модель не указана'
            }), 400
        
        success = model_manager.set_model(model)
        
        if success:
            # Refresh balance to update the current model
            balance_manager.refresh_balance_model()
            
            config = model_manager.get_model_config()
            return jsonify({
                'success': True,
                'message': f'Модель изменена на {config["current_model_name"]}',
                'config': config
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при изменении модели'
            }), 500
    except Exception as e:
        print(f"Error in set_model: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/analyze-unread-sessions', methods=['POST'])
@login_required
def analyze_unread_sessions():
    """API endpoint to analyze unread sessions for potential clients."""
    try:
        stats = analyze_unread_sessions_for_potential_clients()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error in analyze_unread_sessions endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/balance', methods=['GET'])
@login_required
def get_balance():
    """API endpoint to get current balance information."""
    try:
        balance_data = balance_manager.get_balance()
        return jsonify({
            'success': True,
            'balance': balance_data
        })
    except Exception as e:
        print(f"Error in get_balance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@chatbot_api_bp.route('/balance/transactions', methods=['GET'])
@login_required
def get_transactions():
    """API endpoint to get recent transactions."""
    try:
        limit = request.args.get('limit', 50, type=int)
        transactions = balance_manager.get_transactions(limit)
        return jsonify({
            'success': True,
            'transactions': transactions
        })
    except Exception as e:
        print(f"Error in get_transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500
