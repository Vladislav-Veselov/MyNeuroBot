from flask import Blueprint, request, jsonify, send_from_directory, session
from auth import login_required, get_current_user_data_dir
from pathlib import Path
import json
import re
import uuid
from datetime import datetime, timezone, timedelta
from vectorize import rebuild_vector_store

kb_api_bp = Blueprint('kb_api', __name__)

# Configuration
ITEMS_PER_PAGE = 50

# Helper functions
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

def get_current_kb_id() -> str:
    """Get the currently selected knowledge base ID."""
    from tenant_context import get_current_kb_id_override
    
    # Check for tenant context override first
    override = get_current_kb_id_override()
    if override:
        return override
    
    # Then prefer the Flask session (per-user/browser isolation)
    try:
        current_from_session = session.get('current_kb_id')
        if current_from_session:
            return current_from_session
    except Exception:
        pass

    # Fallback: existing logic that reads current_kb.json (account-wide)
    try:
        user_data_dir = get_current_user_data_dir()
        current_kb_file = user_data_dir / "current_kb.json"
        
        if current_kb_file.exists():
            with open(current_kb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('current_kb_id', 'default')
        else:
            return 'default'
    except Exception as e:
        print(f"Error getting current KB ID: {str(e)}")
        return 'default'

def get_knowledge_file_path(kb_id: str = None) -> Path:
    """Get the path to the knowledge file for the specified KB."""
    if kb_id is None:
        kb_id = get_current_kb_id()
    
    user_data_dir = get_current_user_data_dir()
    kb_dir = user_data_dir / "knowledge_bases" / kb_id
    return kb_dir / "knowledge.json"

def read_knowledge_file(kb_id: str = None) -> list[dict]:
    """Read Q&A list from JSON file (no parsing, no splitting)."""
    path = get_knowledge_file_path(kb_id)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        out = []
        for i, item in enumerate(data):
            q = (item.get("question") or "").strip()
            a = (item.get("answer") or "").strip()
            out.append({"id": i, "question": q, "answer": a, "content": f"Вопрос: {q}\n{a}"})
        return out
    except Exception as e:
        print(f"Error reading knowledge file: {str(e)}")
        return []

def write_knowledge_file(documents: list[dict], kb_id: str | None = None) -> None:
    """Write Q&A list to JSON file and update the last modified timestamp."""
    path = get_knowledge_file_path(kb_id)
    # keep only the fields we need to persist
    payload = [{"question": d["question"], "answer": d["answer"]} for d in documents]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Update the updated_at timestamp in kb_info.json
    kb_info_file = path.parent / "kb_info.json"
    if kb_info_file.exists():
        try:
            with open(kb_info_file, 'r', encoding='utf-8') as f:
                kb_info = json.load(f)
        except:
            kb_info = {}
    else:
        kb_info = {}
    
    # Update timestamp and document count
    moscow_tz = timezone(timedelta(hours=3))
    kb_info['updated_at'] = datetime.now(moscow_tz).isoformat()
    kb_info['document_count'] = len(documents)
    
    # Preserve other fields if they exist
    if 'name' not in kb_info:
        kb_info['name'] = kb_id or get_current_kb_id()
    if 'created_at' not in kb_info:
        moscow_tz = timezone(timedelta(hours=3))
        kb_info['created_at'] = datetime.now(moscow_tz).isoformat()
    if 'analyze_clients' not in kb_info:
        kb_info['analyze_clients'] = True
    
    with open(kb_info_file, 'w', encoding='utf-8') as f:
        json.dump(kb_info, f, ensure_ascii=False, indent=2)

def get_all_documents() -> list:
    """Get all Q&A pairs from the knowledge file."""
    return read_knowledge_file()

# API Routes
@kb_api_bp.route('/documents')
@login_required
def get_documents():
    """API endpoint to get paginated documents with optional search."""
    page = int(request.args.get('page', 1))
    search_query = request.args.get('search', '').strip().lower()
    
    try:
        documents = get_all_documents()
        
        if search_query:
            documents = [
                doc for doc in documents
                if search_query in doc['question'].lower() or 
                   search_query in doc['answer'].lower()
            ]
        
        total_docs = len(documents)
        total_pages = (total_docs + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        
        page_docs = documents[start_idx:end_idx]
        
        return jsonify({
            'documents': page_docs,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_documents': total_docs,
                'items_per_page': ITEMS_PER_PAGE
            }
        })
    
    except Exception as e:
        print(f"Error in get_documents endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/document/<int:doc_id>')
@login_required
def get_document(doc_id: int):
    """API endpoint to get a specific document by ID."""
    try:
        docs = get_all_documents()
        if 0 <= doc_id < len(docs):
            return jsonify(docs[doc_id])
        return jsonify({'error': 'Document not found'}), 404
    except Exception as e:
        print(f"Error in get_document endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases', methods=['GET'])
@login_required
def get_knowledge_bases_api():
    """API endpoint to get list of knowledge bases for current user."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases"
        
        if not kb_dir.exists():
            return jsonify({'success': True, 'knowledge_bases': [], 'current_kb_id': 'default'})
        
        kb_list = []
        for kb_folder in kb_dir.iterdir():
            if kb_folder.is_dir():
                kb_id = kb_folder.name
                kb_info_file = kb_folder / "kb_info.json"
                if kb_info_file.exists():
                    with open(kb_info_file, 'r', encoding='utf-8') as f:
                        kb_info = json.load(f)
                    
                    kb_list.append({
                        'id': kb_id,
                        'name': kb_info.get('name', kb_id),
                        'created_at': kb_info.get('created_at', ''),
                        'updated_at': kb_info.get('updated_at', ''),
                        'document_count': kb_info.get('document_count', 0),
                        'analyze_clients': kb_info.get('analyze_clients', True)
                    })
        
        current_kb_id = get_current_kb_id()
        
        return jsonify({
            'success': True,
            'knowledge_bases': sorted(kb_list, key=lambda x: x['updated_at'], reverse=True),
            'current_kb_id': current_kb_id
        })
    except Exception as e:
        print(f"Error in get_knowledge_bases_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases', methods=['POST'])
@login_required
def create_knowledge_base():
    """API endpoint to create a new knowledge base."""
    try:
        data = request.get_json()
        kb_name = (data.get('name') or '').strip()
        kb_password = (data.get('password') or '').strip()
        analyze_clients = data.get('analyze_clients', True)
        
        if not kb_name:
            return jsonify({'error': 'Пожалуйста, введите название базы знаний.'}), 400
        
        if not kb_password:
            return jsonify({'error': 'Пожалуйста, введите пароль для базы знаний.'}), 400
        
        kb_id = str(uuid.uuid4())[:8]
        
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        password_file = kb_dir / "password.txt"
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write(kb_password)
        
        moscow_tz = timezone(timedelta(hours=3))
        kb_info = {
            'name': kb_name,
            'created_at': datetime.now(moscow_tz).isoformat(),
            'updated_at': datetime.now(moscow_tz).isoformat(),
            'document_count': 0,
            'analyze_clients': analyze_clients
        }
        
        with open(kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        with open(kb_dir / "knowledge.json", 'w', encoding='utf-8') as f:
            f.write("[]")
        
        vector_dir = kb_dir / "vector_KB"
        vector_dir.mkdir(exist_ok=True)
        
        return jsonify({
            'success': True,
            'kb_id': kb_id,
            'kb_name': kb_name
        })
    except Exception as e:
        print(f"Error in create_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/<kb_id>', methods=['PUT'])
@login_required
def switch_knowledge_base(kb_id):
    """API endpoint to switch to a different knowledge base."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        # Check if KB has password protection (not default KB)
        if kb_id != 'default':
            password_file = kb_dir / "password.txt"
            if password_file.exists():
                # Get password from request
                data = request.get_json() or {}
                provided_password = data.get('password', '').strip()
                
                if not provided_password:
                    return jsonify({'error': 'Требуется пароль для переключения на эту базу знаний'}), 400
                
                # Read stored password
                with open(password_file, 'r', encoding='utf-8') as f:
                    stored_password = f.read().strip()
                
                # Validate password
                if provided_password != stored_password:
                    return jsonify({'error': 'Неверный пароль'}), 401
        
        with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': kb_id}, f, ensure_ascii=False, indent=2)
        # Also set per-session selection to avoid conflicts across concurrent users
        try:
            session['current_kb_id'] = kb_id
        except Exception:
            pass
        
        return jsonify({'success': True, 'kb_id': kb_id})
    except Exception as e:
        print(f"Error in switch_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/default', methods=['PUT'])
@login_required
def switch_to_default_knowledge_base():
    """API endpoint to switch to the default knowledge base."""
    try:
        user_data_dir = get_current_user_data_dir()
        
        with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': 'default'}, f, ensure_ascii=False, indent=2)
        try:
            session['current_kb_id'] = 'default'
        except Exception:
            pass
        
        return jsonify({'success': True, 'kb_id': 'default'})
    except Exception as e:
        print(f"Error in switch_to_default_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/<kb_id>', methods=['DELETE'])
@login_required
def delete_knowledge_base(kb_id):
    """API endpoint to delete a knowledge base."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        current_kb_id = get_current_kb_id()
        
        # If trying to delete the current KB, switch to default first
        if kb_id == current_kb_id:
            # Switch to default KB before deletion
            with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
                json.dump({'current_kb_id': 'default'}, f, ensure_ascii=False, indent=2)
            try:
                session['current_kb_id'] = 'default'
            except Exception:
                pass
        
        import shutil
        shutil.rmtree(kb_dir)
        
        return jsonify({'success': True, 'switched_to_default': kb_id == current_kb_id})
    except Exception as e:
        print(f"Error in delete_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/<kb_id>/rename', methods=['PUT'])
@login_required
def rename_knowledge_base(kb_id):
    """API endpoint to rename a knowledge base."""
    try:
        data = request.get_json()
        new_name = (data.get('name') or '').strip()
        
        if not new_name:
            return jsonify({'error': 'Пожалуйста, введите новое название.'}), 400
        
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        kb_info_file = kb_dir / "kb_info.json"
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        if kb_info_file.exists():
            with open(kb_info_file, 'r', encoding='utf-8') as f:
                kb_info = json.load(f)
        else:
            kb_info = {}
        
        kb_info['name'] = new_name
        moscow_tz = timezone(timedelta(hours=3))
        kb_info['updated_at'] = datetime.now(moscow_tz).isoformat()
        
        with open(kb_info_file, 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'new_name': new_name})
    except Exception as e:
        print(f"Error in rename_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/<kb_id>/password', methods=['PUT'])
@login_required
def change_kb_password(kb_id):
    """API endpoint to change knowledge base password."""
    try:
        data = request.get_json()
        new_password = (data.get('password') or '').strip()
        
        if not new_password:
            return jsonify({'error': 'Пожалуйста, введите новый пароль.'}), 400
        
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        password_file = kb_dir / "password.txt"
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write(new_password)
        
        return jsonify({
            'success': True,
            'message': 'Пароль базы знаний успешно изменен'
        })
    except Exception as e:
        print(f"Error in change_kb_password: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/<kb_id>/analyze-clients', methods=['PUT'])
@login_required
def change_kb_analyze_clients(kb_id):
    """API endpoint to change knowledge base analyze_clients setting."""
    try:
        data = request.get_json()
        analyze_clients = data.get('analyze_clients', True)
        
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        kb_info_file = kb_dir / "kb_info.json"
        
        if not kb_dir.exists() or not kb_info_file.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        with open(kb_info_file, 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
        
        kb_info['analyze_clients'] = analyze_clients
        moscow_tz = timezone(timedelta(hours=3))
        kb_info['updated_at'] = datetime.now(moscow_tz).isoformat()
        
        with open(kb_info_file, 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Настройка анализа клиентов изменена на {"включено" if analyze_clients else "отключено"}'
        })
    except Exception as e:
        print(f"Error in change_kb_analyze_clients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/<kb_id>', methods=['GET'])
@login_required
def get_knowledge_base_details(kb_id):
    """API endpoint to get knowledge base details including password."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        kb_info_file = kb_dir / "kb_info.json"
        password_file = kb_dir / "password.txt"
        
        if not kb_dir.exists() or not kb_info_file.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        with open(kb_info_file, 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
        
        password = ""
        if password_file.exists():
            with open(password_file, 'r', encoding='utf-8') as f:
                password = f.read().strip()
        
        return jsonify({
            'success': True,
            'kb_id': kb_id,
            'name': kb_info.get('name', ''),
            'created_at': kb_info.get('created_at', ''),
            'updated_at': kb_info.get('updated_at', ''),
            'document_count': kb_info.get('document_count', 0),
            'password': password,
            'has_password': bool(password),
            'analyze_clients': kb_info.get('analyze_clients', True)
        })
    except Exception as e:
        print(f"Error in get_knowledge_base_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/knowledge-bases/check-password', methods=['POST'])
@login_required
def check_kb_password():
    """API endpoint to check if a password is already used by any KB."""
    try:
        data = request.get_json()
        password = (data.get('password') or '').strip()
        exclude_kb_id = data.get('exclude_kb_id', None)
        
        if not password:
            return jsonify({'error': 'Пожалуйста, введите пароль.'}), 400
        
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases"
        
        if not kb_dir.exists():
            return jsonify({'is_unique': True})
        
        for kb_folder in kb_dir.iterdir():
            if kb_folder.is_dir():
                if exclude_kb_id and kb_folder.name == exclude_kb_id:
                    continue
                    
                password_file = kb_folder / "password.txt"
                if password_file.exists():
                    with open(password_file, 'r', encoding='utf-8') as f:
                        kb_password = f.read().strip()
                    if kb_password == password:
                        return jsonify({'is_unique': False, 'error': 'Пароль уже используется в другой базе знаний'})
        
        return jsonify({'is_unique': True})
    except Exception as e:
        print(f"Error in check_kb_password: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/stats')
@login_required
def get_stats():
    """API endpoint to get knowledge base statistics."""
    try:
        docs = get_all_documents()
        total_docs = len(docs)
        
        # Calculate average question and answer lengths
        total_q_len = sum(len(doc['question']) for doc in docs)
        total_a_len = sum(len(doc['answer']) for doc in docs)
        
        # Get last update timestamp from current KB info
        current_kb_id = get_current_kb_id()
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
        kb_info_file = kb_dir / "kb_info.json"
        
        last_update = "Неизвестно"
        if kb_info_file.exists():
            with open(kb_info_file, 'r', encoding='utf-8') as f:
                kb_info = json.load(f)
                updated_at = kb_info.get('updated_at', '')
                if updated_at:
                    try:
                        # Parse ISO format and format for display in Moscow time
                        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        # Convert to Moscow timezone (UTC+3)
                        moscow_tz = timezone(timedelta(hours=3))
                        dt_moscow = dt.astimezone(moscow_tz)
                        last_update = dt_moscow.strftime('%d.%m.%Y %H:%M')
                    except:
                        last_update = "Неизвестно"
        
        stats = {
            'total_documents': total_docs,
            'last_update': last_update,
            'average_answer_length': total_a_len / total_docs if total_docs > 0 else 0
        }
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error in get_stats endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/add_qa', methods=['POST'])
@login_required
def add_qa():
    data = request.get_json()
    q = (data.get('question') or '').strip()
    a = (data.get('answer') or '').strip()
    if not q: return jsonify({'error': 'Пожалуйста, введите вопрос.'}), 400
    if not a: return jsonify({'error': 'Пожалуйста, введите ответ.'}), 400

    docs = read_knowledge_file()
    docs.append({'id': len(docs), 'question': q, 'answer': a})
    write_knowledge_file(docs)

    from vectorize import rebuild_vector_store_with_context
    user_dir = get_current_user_data_dir()
    kb_id = get_current_kb_id()
    rebuild_vector_store_with_context(str(user_dir), kb_id)
    return jsonify({'success': True})

@kb_api_bp.route('/document/<int:doc_id>', methods=['PUT'])
@login_required
def update_document(doc_id: int):
    data = request.get_json()
    q = (data.get('question') or '').strip()
    a = (data.get('answer') or '').strip()
    if not q: return jsonify({'error': 'Пожалуйста, введите вопрос.'}), 400
    if not a: return jsonify({'error': 'Пожалуйста, введите ответ.'}), 400

    docs = read_knowledge_file()
    if not (0 <= doc_id < len(docs)):
        return jsonify({'error': 'Документ не найден'}), 404

    docs[doc_id]['question'] = q
    docs[doc_id]['answer'] = a
    write_knowledge_file(docs)

    from vectorize import rebuild_vector_store_with_context
    user_dir = get_current_user_data_dir()
    kb_id = get_current_kb_id()
    rebuild_vector_store_with_context(str(user_dir), kb_id)
    return jsonify({'success': True})

@kb_api_bp.route('/document/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id: int):
    docs = read_knowledge_file()
    if not (0 <= doc_id < len(docs)):
        return jsonify({'error': 'Документ не найден'}), 404

    docs.pop(doc_id)
    for i, d in enumerate(docs):  # keep sequential ids for the UI
        d['id'] = i
    write_knowledge_file(docs)

    from vectorize import rebuild_vector_store_with_context
    user_dir = get_current_user_data_dir()
    kb_id = get_current_kb_id()
    rebuild_vector_store_with_context(str(user_dir), kb_id)
    return jsonify({'success': True})



@kb_api_bp.route('/knowledge-bases/<kb_id>/download', methods=['GET'])
@login_required
def download_knowledge_file(kb_id):
    user_data_dir = get_current_user_data_dir()
    kb_dir = user_data_dir / "knowledge_bases" / kb_id
    if not kb_dir.exists():
        return jsonify({'error': 'База знаний не найдена'}), 404

    knowledge_file = kb_dir / "knowledge.json"
    if not knowledge_file.exists():
        return jsonify({'error': 'Файл знаний не найден'}), 404

    kb_info_file = kb_dir / "kb_info.json"
    kb_name = kb_id
    if kb_info_file.exists():
        with open(kb_info_file, 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
            kb_name = kb_info.get('name', kb_id)

    safe = "".join(c for c in kb_name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
    return send_from_directory(
        kb_dir,
        'knowledge.json',
        as_attachment=True,
        download_name=f"{safe}_knowledge.json"
    )

@kb_api_bp.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    """API endpoint to save chatbot settings (legacy - uses current KB)."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('tone') is not None:
            return jsonify({'error': 'Тон общения обязателен'}), 400
        
        # Validate ranges (0-4 for all sliders)
        tone = data.get('tone', 2)
        humor = data.get('humor', 2)
        brevity = data.get('brevity', 2)
        
        if not (0 <= tone <= 4):
            return jsonify({'error': 'Тон общения должен быть от 0 до 4'}), 400
        if not (0 <= humor <= 4):
            return jsonify({'error': 'Уровень юмора должен быть от 0 до 4'}), 400
        if not (0 <= brevity <= 4):
            return jsonify({'error': 'Уровень краткости должен быть от 0 до 4'}), 400
        
        # Create settings object
        settings = {
            'tone': tone,
            'humor': humor,
            'brevity': brevity,
            'additional_prompt': data.get('additional_prompt', '')
        }
        
        # Save to file (legacy - uses current KB)
        try:
            user_data_dir = get_current_user_data_dir()
            current_kb_id = get_current_kb_id()
            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            kb_dir.mkdir(parents=True, exist_ok=True)
            system_prompt_file = kb_dir / "system_prompt.txt"
            
            with open(system_prompt_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return jsonify({'error': f'Error saving settings: {str(e)}'}), 500
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in save_settings endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/save_settings/<kb_id>', methods=['POST'])
@login_required
def save_settings_for_kb(kb_id):
    """API endpoint to save chatbot settings for a specific KB."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('tone') is not None:
            return jsonify({'error': 'Тон общения обязателен'}), 400
        
        # Validate ranges (0-4 for all sliders)
        tone = data.get('tone', 2)
        humor = data.get('humor', 2)
        brevity = data.get('brevity', 2)
        
        if not (0 <= tone <= 4):
            return jsonify({'error': 'Тон общения должен быть от 0 до 4'}), 400
        if not (0 <= humor <= 4):
            return jsonify({'error': 'Уровень юмора должен быть от 0 до 4'}), 400
        if not (0 <= brevity <= 4):
            return jsonify({'error': 'Уровень краткости должен быть от 0 до 4'}), 400
        
        # Create settings object
        settings = {
            'tone': tone,
            'humor': humor,
            'brevity': brevity,
            'additional_prompt': data.get('additional_prompt', '')
        }
        
        # Save to KB-specific file
        try:
            user_data_dir = get_current_user_data_dir()
            kb_dir = user_data_dir / "knowledge_bases" / kb_id
            
            if not kb_dir.exists():
                return jsonify({'error': 'База знаний не найдена'}), 404
            
            system_prompt_file = kb_dir / "system_prompt.txt"
            
            with open(system_prompt_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings for KB {kb_id}: {str(e)}")
            return jsonify({'error': f'Error saving settings: {str(e)}'}), 500
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in save_settings_for_kb endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/get_settings')
@login_required
def get_settings():
    """API endpoint to get chatbot settings (legacy - uses current KB)."""
    try:
        user_data_dir = get_current_user_data_dir()
        current_kb_id = get_current_kb_id()
        kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
        system_prompt_file = kb_dir / "system_prompt.txt"
        
        if not system_prompt_file.exists():
            # Return default settings if file doesn't exist
            default_settings = {
                'tone': 2,
                'humor': 2,
                'brevity': 2,
                'additional_prompt': ''
            }
            return jsonify({'success': True, 'settings': default_settings})
        
        with open(system_prompt_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Handle legacy settings (convert string tone to numeric)
        if isinstance(settings.get('tone'), str):
            tone_mapping = {'formal': 0, 'friendly': 2, 'casual': 4}
            settings['tone'] = tone_mapping.get(settings['tone'], 2)
        
        return jsonify({'success': True, 'settings': settings})
        
    except Exception as e:
        print(f"Error in get_settings endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/get_settings/<kb_id>')
@login_required
def get_settings_for_kb(kb_id):
    """API endpoint to get chatbot settings for a specific KB."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        system_prompt_file = kb_dir / "system_prompt.txt"
        
        if not system_prompt_file.exists():
            # Return default settings if file doesn't exist
            default_settings = {
                'tone': 2,
                'humor': 2,
                'brevity': 2,
                'additional_prompt': ''
            }
            return jsonify({'success': True, 'settings': default_settings})
        
        with open(system_prompt_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Handle legacy settings (convert string tone to numeric)
        if isinstance(settings.get('tone'), str):
            tone_mapping = {'formal': 0, 'friendly': 2, 'casual': 4}
            settings['tone'] = tone_mapping.get(settings['tone'], 2)
        
        return jsonify({'success': True, 'settings': settings})
        
    except Exception as e:
        print(f"Error in get_settings_for_kb endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@kb_api_bp.route('/semantic_search')
@login_required
def semantic_search():
    """API endpoint for semantic search using vector store."""
    try:
        query = request.args.get('query', '').strip()
        if not query:
            return jsonify({'documents': [], 'error': 'Empty search query'}), 400

        # Load vector store
        index, docstore = get_vector_store()
        if index is None or docstore is None:
            return jsonify({'documents': [], 'error': 'Vector store not available'}), 503

        # Get embeddings
        import os
        from dotenv import load_dotenv
        from langchain_openai import OpenAIEmbeddings
        import numpy as np
        
        load_dotenv(override=True)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({'documents': [], 'error': 'OpenAI API key not configured'}), 503
        
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # Get query vector
        query_vector = embeddings.embed_query(query)
        
        # Search in FAISS
        k = 5  # number of results to return
        distances, indices = index.search(np.array([query_vector], dtype="float32"), k)
        
        # Get matching documents
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            doc_id = str(idx)
            if doc_id in docstore:
                # Get the full document from knowledge file
                question = docstore[doc_id]
                docs = get_all_documents()
                matching_doc = next((doc for doc in docs if doc['question'] == question), None)
                if matching_doc:
                    matching_doc['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity score
                    results.append(matching_doc)
        
        return jsonify({
            'documents': results,
            'total_results': len(results)
        })

    except Exception as e:
        print(f"Error in semantic_search endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_vector_store():
    """Initialize and return the vector store components."""
    try:
        user_data_dir = get_current_user_data_dir()
        index_file = get_vector_store_dir() / "index.faiss"
        docstore_file = get_vector_store_dir() / "docstore.json"
        
        if not index_file.exists() or not docstore_file.exists():
            return None, None
        
        import faiss
        index = faiss.read_index(str(index_file))
        with open(docstore_file, 'r', encoding='utf-8') as f:
            docstore = json.load(f)
        return index, docstore
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")
        return None, None

def get_vector_store_dir(kb_id: str = None) -> Path:
    """Get the path to the vector store directory for the specified KB."""
    if kb_id is None:
        kb_id = get_current_kb_id()
    
    user_data_dir = get_current_user_data_dir()
    kb_dir = user_data_dir / "knowledge_bases" / kb_id
    return kb_dir / "vector_KB"
