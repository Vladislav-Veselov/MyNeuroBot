from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from pathlib import Path
import os
from typing import List, Dict, Any, Optional
import re
from vectorize import rebuild_vector_store
import json
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from chatbot_service import chatbot_service
from dialogue_storage import get_dialogue_storage
from session_manager import ip_session_manager
from data_masking import data_masker
from openai import OpenAI
from auth import auth, login_required, login_required_web, get_current_user_data_dir, admin_required, admin_required_web
from datetime import datetime
from chatbot_status_manager import chatbot_status_manager
from model_manager import model_manager
from balance_manager import balance_manager

# Load environment variables
load_dotenv(override=True)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='../Frontend/templates',
            static_folder='../Frontend/static')
CORS(app)

# Configure session
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

# Initialize services
chatbot_service = chatbot_service

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
ITEMS_PER_PAGE = 10

def find_kb_by_password(password: str) -> Optional[str]:
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

def update_kb_document_count(kb_id: str) -> int:
    """Update the document count for a specific knowledge base."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        kb_info_file = kb_dir / "kb_info.json"
        knowledge_file = kb_dir / "knowledge.txt"
        
        # Count actual documents
        document_count = 0
        if knowledge_file.exists():
            documents = parse_knowledge_file(kb_id)
            document_count = len(documents)
        
        # Update KB info
        if kb_info_file.exists():
            with open(kb_info_file, 'r', encoding='utf-8') as f:
                kb_info = json.load(f)
        else:
            kb_info = {}
        
        kb_info['document_count'] = document_count
        kb_info['updated_at'] = datetime.now().isoformat()
        
        with open(kb_info_file, 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return document_count
    except Exception as e:
        print(f"Error updating document count for KB {kb_id}: {str(e)}")
        return 0

def get_knowledge_bases() -> List[Dict[str, Any]]:
    """Get list of knowledge bases for current user."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases"
        
        if not kb_dir.exists():
            return []
        
        kb_list = []
        for kb_folder in kb_dir.iterdir():
            if kb_folder.is_dir():
                kb_id = kb_folder.name
                kb_info_file = kb_folder / "kb_info.json"
                if kb_info_file.exists():
                    with open(kb_info_file, 'r', encoding='utf-8') as f:
                        kb_info = json.load(f)
                    
                    # Update document count to ensure it's accurate
                    actual_document_count = update_kb_document_count(kb_id)
                    
                    kb_list.append({
                        'id': kb_id,
                        'name': kb_info.get('name', kb_id),
                        'created_at': kb_info.get('created_at', ''),
                        'updated_at': kb_info.get('updated_at', ''),
                        'document_count': actual_document_count,
                        'analyze_clients': kb_info.get('analyze_clients', True)  # Default to True for backward compatibility
                    })
        
        return sorted(kb_list, key=lambda x: x['updated_at'], reverse=True)
    except Exception as e:
        print(f"Error getting knowledge bases: {str(e)}")
        return []

def get_current_kb_id() -> str:
    """Get the currently selected knowledge base ID."""
    try:
        user_data_dir = get_current_user_data_dir()
        current_kb_file = user_data_dir / "current_kb.json"
        
        if current_kb_file.exists():
            with open(current_kb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('current_kb_id', 'default')
        else:
            # Create default KB if none exists
            return create_default_knowledge_base()
    except Exception as e:
        print(f"Error getting current KB ID: {str(e)}")
        return 'default'

def create_default_knowledge_base() -> str:
    """Create a default knowledge base for the user."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases"
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        default_kb_id = "default"
        default_kb_dir = kb_dir / default_kb_id
        default_kb_dir.mkdir(exist_ok=True)
        
        # Store default password as plain text
        password_file = default_kb_dir / "password.txt"
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write("123456")
        
        # Create KB info
        kb_info = {
            'name': 'База знаний для клиентов',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'document_count': 0,
            'analyze_clients': True  # Default to True for potential client analysis
        }
        
        with open(default_kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        # Update document count to ensure it's accurate
        update_kb_document_count(default_kb_id)
        
        # Create empty knowledge file
        with open(default_kb_dir / "knowledge.txt", 'w', encoding='utf-8') as f:
            f.write("")
        
        # Set as current KB
        with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
        
        return default_kb_id
    except Exception as e:
        print(f"Error creating default knowledge base: {str(e)}")
        return 'default'

def get_knowledge_file_path(kb_id: str = None) -> Path:
    """Get the path to the knowledge file for the specified KB."""
    if kb_id is None:
        kb_id = get_current_kb_id()
    
    user_data_dir = get_current_user_data_dir()
    kb_dir = user_data_dir / "knowledge_bases" / kb_id
    return kb_dir / "knowledge.txt"

def get_vector_store_dir(kb_id: str = None) -> Path:
    """Get the path to the vector store directory for the specified KB."""
    if kb_id is None:
        kb_id = get_current_kb_id()
    
    user_data_dir = get_current_user_data_dir()
    kb_dir = user_data_dir / "knowledge_bases" / kb_id
    return kb_dir / "vector_KB"

def parse_knowledge_file(kb_id: str = None) -> List[Dict[str, Any]]:
    """Parse the knowledge.txt file into a list of Q&A pairs."""
    try:
        knowledge_file = get_knowledge_file_path(kb_id)
        
        if not knowledge_file.exists():
            return []
        
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error parsing knowledge file: {str(e)}")
        return []
    
    # Split content into Q&A pairs
    qa_pairs = []
    
    # Split by double newlines to get individual Q&A blocks
    blocks = content.split('\n\n')
    
    for i, block in enumerate(blocks):
        if not block.strip():
            continue
            
        # Split into lines and clean them
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        # First line should be the question (starts with "Вопрос:")
        if not lines[0].startswith('Вопрос:'):
            continue
            
        # Extract question (remove "Вопрос:" prefix and clean)
        question = lines[0][len('Вопрос:'):].strip()
        
        # Process answer lines
        answer_lines = []
        for line in lines[1:]:
            # Remove all leading/trailing whitespace
            line = line.strip()
            if line:  # Only add non-empty lines
                answer_lines.append(line)
        
        # Join lines with single newlines, no extra spaces
        answer = '\n'.join(answer_lines)
        # Remove all leading whitespace and empty lines from the answer block
        answer = re.sub(r'^(\s|\n)+', '', answer)
        # Remove all trailing whitespace and empty lines from the answer block
        answer = re.sub(r'(\s|\n)+$', '', answer)
        
        qa_pairs.append({
            'id': i,
            'question': question,
            'answer': answer,
            'content': f"Вопрос: {question}\n{answer}"  # Full text for search
        })
    
    return qa_pairs

def get_all_documents() -> List[Dict[str, Any]]:
    """Get all Q&A pairs from the knowledge file."""
    return parse_knowledge_file()

@app.route('/')
def home():
    """Redirect to the viewer page."""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('viewer.html')

@app.route('/login')
def login():
    """Render the login page."""
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup')
def signup():
    """Render the signup page."""
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout the user."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/viewer')
@login_required_web
def viewer():
    """Render the knowledge base viewer page."""
    return render_template('viewer.html')

@app.route('/settings')
@login_required_web
def settings():
    """Render the settings page."""
    return render_template('settings.html')

@app.route('/balance')
@login_required_web
def balance():
    """Render the balance page."""
    return render_template('balance.html')

@app.route('/contact')
@login_required_web
def contact():
    """Render the contact page."""
    return render_template('contact.html')

@app.route('/api/signup', methods=['POST'])
def api_signup():
    """API endpoint for user registration."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    
    result = auth.register_user(username, password, email)
    return jsonify(result)

@app.route('/api/login', methods=['POST'])
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

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API endpoint for user logout."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route('/api/documents')
@login_required
def get_documents():
    """API endpoint to get paginated documents with optional search."""
    page = int(request.args.get('page', 1))
    search_query = request.args.get('search', '').strip().lower()
    
    try:
        documents = get_all_documents()
        
        # Apply search if query provided
        if search_query:
            documents = [
                doc for doc in documents
                if search_query in doc['question'].lower() or 
                   search_query in doc['answer'].lower()
            ]
        
        # Calculate pagination
        total_docs = len(documents)
        total_pages = (total_docs + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        
        # Get page of documents
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

@app.route('/api/document/<int:doc_id>')
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

@app.route('/api/stats')
@login_required
def get_stats():
    """API endpoint to get knowledge base statistics."""
    try:
        docs = get_all_documents()
        total_docs = len(docs)
        
        # Calculate average question and answer lengths
        total_q_len = sum(len(doc['question']) for doc in docs)
        total_a_len = sum(len(doc['answer']) for doc in docs)
        
        stats = {
            'total_documents': total_docs,
            'average_question_length': total_q_len / total_docs if total_docs > 0 else 0,
            'average_answer_length': total_a_len / total_docs if total_docs > 0 else 0
        }
        
        return jsonify(stats)
    except Exception as e:
        print(f"Error in get_stats endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_qa', methods=['POST'])
@login_required
def add_qa():
    data = request.get_json()
    question = (data.get('question') or '').strip()
    answer = (data.get('answer') or '').strip()

    # Validate input
    if not question:
        return jsonify({'error': 'Пожалуйста, введите вопрос.'}), 400
    if not answer:
        return jsonify({'error': 'Пожалуйста, введите ответ.'}), 400

    # Format the new Q&A block
    new_block = f"Вопрос: {question}\n{answer}\n\n"
    try:
        user_data_dir = get_current_user_data_dir()
        current_kb_id = get_current_kb_id()
        knowledge_file = get_knowledge_file_path()
        
        with open(knowledge_file, 'a', encoding='utf-8') as f:
            f.write(new_block)
        
        # Update document count
        update_kb_document_count(current_kb_id)
        
        # Rebuild vector store after adding new Q&A
        rebuild_vector_store()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Ошибка при добавлении: {str(e)}'}), 500

def save_knowledge_file(documents: List[Dict[str, Any]]) -> None:
    """Save the list of Q&A pairs back to the knowledge file."""
    try:
        user_data_dir = get_current_user_data_dir()
        current_kb_id = get_current_kb_id()
        knowledge_file = get_knowledge_file_path()
        
        content = '\n\n'.join(
            f"Вопрос: {doc['question']}\n{doc['answer']}"
            for doc in documents
        )
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            f.write(content + '\n\n')  # Add final newlines for consistency
        
        # Update document count using the new function
        update_kb_document_count(current_kb_id)
    except Exception as e:
        print(f"Error saving knowledge file: {str(e)}")

@app.route('/api/document/<int:doc_id>', methods=['PUT'])
@login_required
def update_document(doc_id: int):
    """API endpoint to update a specific document."""
    try:
        data = request.get_json()
        question = (data.get('question') or '').strip()
        answer = (data.get('answer') or '').strip()

        # Validate input
        if not question:
            return jsonify({'error': 'Пожалуйста, введите вопрос.'}), 400
        if not answer:
            return jsonify({'error': 'Пожалуйста, введите ответ.'}), 400

        # Get current documents
        documents = get_all_documents()
        
        # Validate document ID
        if not (0 <= doc_id < len(documents)):
            return jsonify({'error': 'Документ не найден'}), 404

        # Update the document
        documents[doc_id] = {
            'id': doc_id,
            'question': question,
            'answer': answer
        }

        # Save back to file
        save_knowledge_file(documents)

        # Rebuild vector store
        rebuild_vector_store()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in update_document endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id: int):
    """API endpoint to delete a specific document."""
    try:
        # Get current documents
        documents = get_all_documents()
        
        # Validate document ID
        if not (0 <= doc_id < len(documents)):
            return jsonify({'error': 'Документ не найден'}), 404

        # Remove the document
        documents.pop(doc_id)

        # Update IDs for remaining documents
        for i, doc in enumerate(documents):
            doc['id'] = i

        # Save back to file
        save_knowledge_file(documents)

        # Rebuild vector store
        rebuild_vector_store()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error in delete_document endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_vector_store():
    """Initialize and return the vector store components."""
    try:
        user_data_dir = get_current_user_data_dir()
        index_file = get_vector_store_dir() / "index.faiss"
        docstore_file = get_vector_store_dir() / "docstore.json"
        
        if not index_file.exists() or not docstore_file.exists():
            return None, None
        
        index = faiss.read_index(str(index_file))
        with open(docstore_file, 'r', encoding='utf-8') as f:
            docstore = json.load(f)
        return index, docstore
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")
        return None, None

@app.route('/api/semantic_search')
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
            
            # Prepare conversation text for analysis with data masking
            conversation_text = ""
            masked_items_count = 0
            
            for message in full_session['messages']:
                role = "Пользователь" if message['role'] == 'user' else "Бот"
                
                # Apply data masking to user messages only
                if message['role'] == 'user':
                    masked_content, mask_info = data_masker.mask_all_personal_data(message['content'])
                    masked_items_count += mask_info.get('total_masked', 0)
                    conversation_text += f"{role}: {masked_content}\n"
                else:
                    # Bot messages don't need masking
                    conversation_text += f"{role}: {message['content']}\n"
            
            # Log masking information if any personal data was found
            if masked_items_count > 0:
                print(f"\n🔒 PERSONAL DATA MASKED DURING CLIENT ANALYSIS:")
                print(f"   Session ID: {session_id}")
                print(f"   Total masked items: {masked_items_count}")
            
            # Analyze with OpenAI
            analysis_prompt = f"""
            Проанализируй следующий диалог и определи, является ли пользователь потенциальным клиентом для компании.

            Критерии потенциального клиента:
            - Пользователь интересуется товарами или услугами компании
            - Задает уточняющие вопросы о продукте или услуге
            - Просит связаться с человеком

            Диалог:
            {conversation_text}

            Твой ответ должен состоять из одного слова капсом. Ответь только "ДА" если пользователь является потенциальным клиентом, или "НЕТ" если нет.
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Ты - аналитик, который определяет потенциальных клиентов на основе диалогов с чат-ботом. Отвечай только ДА или НЕТ."},
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

@app.route('/analytics')
@login_required_web
def analytics():
    """Render the analytics page."""
    return render_template('analytics.html')

@app.route('/about')
@login_required_web
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/chatbot')
@login_required_web
def chatbot():
    """Render the chatbot page."""
    return render_template('chatbot.html')

@app.route('/api/save_settings', methods=['POST'])
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

@app.route('/api/save_settings/<kb_id>', methods=['POST'])
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

@app.route('/api/get_settings')
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

@app.route('/api/get_settings/<kb_id>')
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

@app.route('/api/chatbot', methods=['POST'])
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

@app.route('/api/chatbot/clear', methods=['POST'])
@login_required
def clear_chatbot_history():
    """API endpoint to clear chatbot conversation history."""
    try:
        chatbot_service.clear_history()
        return jsonify({'success': True, 'message': 'История разговора очищена'})
        
    except Exception as e:
        print(f"Error clearing chatbot history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/new-session', methods=['POST'])
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

@app.route('/api/dialogues', methods=['GET'])
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

@app.route('/api/dialogues/<session_id>', methods=['GET'])
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

@app.route('/api/dialogues/<session_id>', methods=['DELETE'])
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

@app.route('/api/dialogues/clear-all', methods=['DELETE'])
@login_required
def clear_all_dialogues():
    """API endpoint to clear all dialogue sessions."""
    try:
        dialogue_storage = get_dialogue_storage()
        success = dialogue_storage.clear_all_sessions()
        if success:
            # Reset chatbot service session to ensure new dialogues are created
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

@app.route('/api/dialogues/stats', methods=['GET'])
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

@app.route('/api/dialogues/<session_id>/potential-client', methods=['PUT'])
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

@app.route('/api/analyze-unread-sessions', methods=['POST'])
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

@app.route('/api/dialogues/by-ip/<ip_address>', methods=['GET'])
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

@app.route('/api/dialogues/current-ip', methods=['GET'])
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

@app.route('/api/dialogues/<session_id>/download', methods=['GET'])
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
        from flask import Response
        response = Response(dialogue_text, mimetype='text/plain; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename=dialogue_{session_id[:8]}.txt'
        return response
        
    except Exception as e:
        print(f"Error downloading dialogue {session_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases', methods=['GET'])
@login_required
def get_knowledge_bases_api():
    """API endpoint to get list of knowledge bases for current user."""
    try:
        kb_list = get_knowledge_bases()
        current_kb_id = get_current_kb_id()
        
        return jsonify({
            'success': True,
            'knowledge_bases': kb_list,
            'current_kb_id': current_kb_id
        })
    except Exception as e:
        print(f"Error in get_knowledge_bases_api: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases', methods=['POST'])
@login_required
def create_knowledge_base():
    """API endpoint to create a new knowledge base."""
    try:
        data = request.get_json()
        kb_name = (data.get('name') or '').strip()
        kb_password = (data.get('password') or '').strip()
        analyze_clients = data.get('analyze_clients', True)  # Default to True for backward compatibility
        
        if not kb_name:
            return jsonify({'error': 'Пожалуйста, введите название базы знаний.'}), 400
        
        if not kb_password:
            return jsonify({'error': 'Пожалуйста, введите пароль для базы знаний.'}), 400
        
        # Generate unique KB ID
        import uuid
        kb_id = str(uuid.uuid4())[:8]
        
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        # Store password as plain text
        password_file = kb_dir / "password.txt"
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write(kb_password)
        
        # Create KB info
        kb_info = {
            'name': kb_name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'document_count': 0,
            'analyze_clients': analyze_clients
        }
        
        with open(kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        # Create empty knowledge file
        with open(kb_dir / "knowledge.txt", 'w', encoding='utf-8') as f:
            f.write("")
        
        # Update document count to ensure it's accurate
        update_kb_document_count(kb_id)
        
        # Create vector store directory
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

@app.route('/api/knowledge-bases/<kb_id>', methods=['PUT'])
@login_required
def switch_knowledge_base(kb_id):
    """API endpoint to switch to a different knowledge base."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        # Update current KB
        with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': kb_id}, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'kb_id': kb_id})
    except Exception as e:
        print(f"Error in switch_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<kb_id>', methods=['DELETE'])
@login_required
def delete_knowledge_base(kb_id):
    """API endpoint to delete a knowledge base."""
    try:
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases" / kb_id
        
        if not kb_dir.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        # Check if this is the current KB
        current_kb_id = get_current_kb_id()
        if kb_id == current_kb_id:
            return jsonify({'error': 'Нельзя удалить активную базу знаний'}), 400
        
        # Delete the KB directory
        import shutil
        shutil.rmtree(kb_dir)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in delete_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<kb_id>/rename', methods=['PUT'])
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
        
        # Update KB info
        if kb_info_file.exists():
            with open(kb_info_file, 'r', encoding='utf-8') as f:
                kb_info = json.load(f)
        else:
            kb_info = {}
        
        kb_info['name'] = new_name
        kb_info['updated_at'] = datetime.now().isoformat()
        
        with open(kb_info_file, 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'new_name': new_name})
    except Exception as e:
        print(f"Error in rename_knowledge_base: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<kb_id>/password', methods=['PUT'])
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
        kb_info_file = kb_dir / "kb_info.json"
        password_file = kb_dir / "password.txt"
        
        if not kb_dir.exists() or not kb_info_file.exists():
            return jsonify({'error': 'База знаний не найдена'}), 404
        
        # Read current KB info
        with open(kb_info_file, 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
        
        # Store new password as plain text
        with open(password_file, 'w', encoding='utf-8') as f:
            f.write(new_password)
        
        # Update KB info
        kb_info['updated_at'] = datetime.now().isoformat()
        
        with open(kb_info_file, 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Пароль базы знаний успешно изменен'
        })
    except Exception as e:
        print(f"Error in change_kb_password: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge-bases/<kb_id>/analyze-clients', methods=['PUT'])
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
        
        # Read current KB info
        with open(kb_info_file, 'r', encoding='utf-8') as f:
            kb_info = json.load(f)
        
        # Update analyze_clients setting
        kb_info['analyze_clients'] = analyze_clients
        kb_info['updated_at'] = datetime.now().isoformat()
        
        with open(kb_info_file, 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Настройка анализа клиентов изменена на {"включено" if analyze_clients else "отключено"}'
        })
    except Exception as e:
        print(f"Error in change_kb_analyze_clients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/Backend/<path:filename>')
def backend_static(filename):
    """Serve static files from the Backend folder."""
    backend_dir = Path(__file__).resolve().parent
    file_path = backend_dir / filename
    print(f"Requested file: {filename}")
    print(f"Full path: {file_path}")
    print(f"File exists: {file_path.exists()}")
    return send_from_directory(backend_dir, filename)

@app.route('/test-logo')
def test_logo():
    """Test route to check if logo file exists."""
    logo_path = Path(__file__).resolve().parent.parent / "Frontend" / "static" / "logo.png"
    return jsonify({
        'logo_exists': logo_path.exists(),
        'logo_path': str(logo_path),
        'logo_size': logo_path.stat().st_size if logo_path.exists() else None
    })

@app.route('/api/knowledge-bases/<kb_id>', methods=['GET'])
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
        
        # Read password from file
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
            'analyze_clients': kb_info.get('analyze_clients', True)  # Default to True for backward compatibility
        })
    except Exception as e:
        print(f"Error in get_knowledge_base_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/status', methods=['GET'])
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

@app.route('/api/chatbot/stop', methods=['POST'])
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

@app.route('/api/chatbot/start', methods=['POST'])
@login_required
def start_chatbots():
    """API endpoint to start all chatbots for the current user."""
    try:
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

@app.route('/api/model/config', methods=['GET'])
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

@app.route('/api/model/set', methods=['POST'])
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

@app.route('/api/balance', methods=['GET'])
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

@app.route('/api/balance/transactions', methods=['GET'])
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

# Admin routes
@app.route('/admin')
@admin_required_web
def admin_panel():
    """Render the admin panel page."""
    return render_template('admin.html')

@app.route('/api/admin/users', methods=['GET'])
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

@app.route('/api/admin/balances', methods=['GET'])
@admin_required
def admin_get_all_balances():
    """API endpoint to get all user balances (admin only)."""
    try:
        result = balance_manager.admin_get_all_balances()
        return jsonify(result)
    except Exception as e:
        print(f"Error in admin_get_all_balances: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/balance/increase', methods=['POST'])
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
        
        result = balance_manager.admin_increase_balance(username, amount_rub, reason)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in admin_increase_balance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/<username>/balance', methods=['GET'])
@admin_required
def admin_get_user_balance(username):
    """API endpoint to get specific user balance (admin only)."""
    try:
        if not auth.user_exists(username):
            return jsonify({'success': False, 'error': f'User {username} does not exist'}), 404
        
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

@app.route('/api/knowledge-bases/check-password', methods=['POST'])
@login_required
def check_kb_password():
    """API endpoint to check if a password is already used by any KB."""
    try:
        data = request.get_json()
        password = (data.get('password') or '').strip()
        
        if not password:
            return jsonify({'error': 'Пожалуйста, введите пароль.'}), 400
        
        # Check if password is already used by any KB
        user_data_dir = get_current_user_data_dir()
        kb_dir = user_data_dir / "knowledge_bases"
        
        if not kb_dir.exists():
            return jsonify({'is_unique': True})
        
        for kb_folder in kb_dir.iterdir():
            if kb_folder.is_dir():
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

if __name__ == '__main__':
    # Check if we're in production (Render sets PORT environment variable)
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    if debug_mode:
        # Development mode - use Flask's built-in server
        # Use localhost only to avoid the warning and multiple addresses
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        # Production mode - use Gunicorn (this should be called by gunicorn)
        app.run(host='0.0.0.0', port=port, debug=False) 