from flask import Flask, render_template, jsonify, request, send_from_directory
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
from dialogue_storage import dialogue_storage
from openai import OpenAI

# Load environment variables
load_dotenv(override=True)

# Initialize Flask app
app = Flask(__name__, 
            template_folder=r'C:\PARTNERS\NeuroBot\Frontend\templates',
            static_folder=r'C:\PARTNERS\NeuroBot\Frontend\static')
CORS(app)

# Initialize services
chatbot_service = chatbot_service

# File paths
KNOWLEDGE_FILE = Path(r"C:\PARTNERS\NeuroBot\Backend\knowledge.txt")
SYSTEM_PROMPT_FILE = Path(r"C:\PARTNERS\NeuroBot\Backend\system_prompt.txt")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
ITEMS_PER_PAGE = 10

# Add these constants at the top with other configs
VECTOR_STORE_DIR = Path(r"C:\PARTNERS\NeuroBot\Backend\vector_KB")
INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
DOCSTORE_FILE = VECTOR_STORE_DIR / "docstore.json"

def parse_knowledge_file() -> List[Dict[str, Any]]:
    """Parse the knowledge.txt file into a list of Q&A pairs."""
    if not KNOWLEDGE_FILE.exists():
        return []
    
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
    return render_template('viewer.html')

@app.route('/viewer')
def viewer():
    """Render the knowledge base viewer page."""
    return render_template('viewer.html')

@app.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html')

@app.route('/contact')
def contact():
    """Render the contact page."""
    return render_template('contact.html')

@app.route('/api/documents')
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
        with open(KNOWLEDGE_FILE, 'a', encoding='utf-8') as f:
            f.write(new_block)
        
        # Rebuild vector store after adding new Q&A
        rebuild_vector_store()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f'Ошибка при добавлении: {str(e)}'}), 500

def save_knowledge_file(documents: List[Dict[str, Any]]) -> None:
    """Save the list of Q&A pairs back to the knowledge file."""
    content = '\n\n'.join(
        f"Вопрос: {doc['question']}\n{doc['answer']}"
        for doc in documents
    )
    
    with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
        f.write(content + '\n\n')  # Add final newlines for consistency

@app.route('/api/document/<int:doc_id>', methods=['PUT'])
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
    if not INDEX_FILE.exists() or not DOCSTORE_FILE.exists():
        return None, None
    
    try:
        index = faiss.read_index(str(INDEX_FILE))
        with open(DOCSTORE_FILE, 'r', encoding='utf-8') as f:
            docstore = json.load(f)
        return index, docstore
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")
        return None, None

@app.route('/api/semantic_search')
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
            
            # Prepare conversation text for analysis
            conversation_text = ""
            for message in full_session['messages']:
                role = "Пользователь" if message['role'] == 'user' else "Бот"
                conversation_text += f"{role}: {message['content']}\n"
            
            # Analyze with OpenAI
            analysis_prompt = f"""
            Проанализируй следующий диалог и определи, является ли пользователь потенциальным клиентом для NeuroBot.

            Критерии потенциального клиента:
            - Пользователь интересуется функциями NeuroBot
            - Задает вопросы о внедрении, настройке, возможностях
            - Проявляет деловой интерес к продукту
            - Не просто тестирует бота, а планирует использовать его

            Диалог:
            {conversation_text}

            Ответь только "ДА" если пользователь является потенциальным клиентом, или "НЕТ" если нет.
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты - аналитик, который определяет потенциальных клиентов на основе диалогов с чат-ботом. Отвечай только ДА или НЕТ."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=10,
                    temperature=0.1
                )
                
                result = response.choices[0].message.content.strip().upper()
                is_potential_client = result == "ДА"
                
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
def analytics():
    """Render the analytics page."""
    return render_template('analytics.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    """API endpoint to save chatbot settings."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('tone'):
            return jsonify({'error': 'Тон общения обязателен'}), 400
        
        # Validate ranges
        humor = data.get('humor', 2)
        brevity = data.get('brevity', 2)
        
        if not (0 <= humor <= 5):
            return jsonify({'error': 'Уровень юмора должен быть от 0 до 5'}), 400
        if not (0 <= brevity <= 5):
            return jsonify({'error': 'Уровень краткости должен быть от 0 до 5'}), 400
        
        # Create settings object
        settings = {
            'tone': data['tone'],
            'humor': humor,
            'brevity': brevity,
            'additional_prompt': data.get('additional_prompt', '')
        }
        
        # Save to file
        with open(SYSTEM_PROMPT_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error in save_settings endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_settings')
def get_settings():
    """API endpoint to get chatbot settings."""
    try:
        if not SYSTEM_PROMPT_FILE.exists():
            # Return default settings if file doesn't exist
            default_settings = {
                'tone': 'friendly',
                'humor': 2,
                'brevity': 2,
                'additional_prompt': ''
            }
            return jsonify({'success': True, 'settings': default_settings})
        
        with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        return jsonify({'success': True, 'settings': settings})
        
    except Exception as e:
        print(f"Error in get_settings endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """API endpoint for chatbot responses."""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id', None)
        
        if not message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
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
def clear_chatbot_history():
    """API endpoint to clear chatbot conversation history."""
    try:
        chatbot_service.clear_history()
        return jsonify({'success': True, 'message': 'История разговора очищена'})
        
    except Exception as e:
        print(f"Error clearing chatbot history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/new-session', methods=['POST'])
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
def get_dialogues():
    """API endpoint to get all dialogue sessions."""
    try:
        sessions = dialogue_storage.get_all_sessions()
        return jsonify({
            'success': True,
            'sessions': sessions
        })
        
    except Exception as e:
        print(f"Error getting dialogues: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dialogues/<session_id>', methods=['GET'])
def get_dialogue(session_id):
    """Get a specific dialogue session."""
    try:
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
def delete_dialogue(session_id):
    """API endpoint to delete a specific dialogue session."""
    try:
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
def clear_all_dialogues():
    """API endpoint to clear all dialogue sessions."""
    try:
        success = dialogue_storage.clear_all_sessions()
        if success:
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
def get_dialogue_stats():
    """API endpoint to get dialogue storage statistics."""
    try:
        stats = dialogue_storage.get_storage_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error getting dialogue stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dialogues/<session_id>/potential-client', methods=['PUT'])
def mark_potential_client(session_id):
    """API endpoint to mark a session as a potential client."""
    try:
        data = request.get_json()
        is_potential_client = data.get('potential_client', True)
        
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

@app.route('/Backend/<path:filename>')
def backend_static(filename):
    """Serve static files from the Backend folder."""
    backend_dir = Path(r"C:\PARTNERS\NeuroBot\Backend")
    file_path = backend_dir / filename
    print(f"Requested file: {filename}")
    print(f"Full path: {file_path}")
    print(f"File exists: {file_path.exists()}")
    return send_from_directory(backend_dir, filename)

@app.route('/test-logo')
def test_logo():
    """Test route to check if logo file exists."""
    logo_path = Path(r"C:\PARTNERS\NeuroBot\Frontend\static\logo.png")
    return jsonify({
        'logo_exists': logo_path.exists(),
        'logo_path': str(logo_path),
        'logo_size': logo_path.stat().st_size if logo_path.exists() else None
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001) 