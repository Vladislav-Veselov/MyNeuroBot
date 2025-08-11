#!/usr/bin/env python3
"""
Standalone chatbot service for HTML chatbot.
This service handles user-specific sessions and knowledge bases properly.
"""

import os
import json
import re
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from dialogue_storage import get_dialogue_storage
from data_masking import data_masker
from model_manager import model_manager
from balance_manager import balance_manager
from auth import auth

# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found in .env file.")
os.environ["OPENAI_API_KEY"] = api_key

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StandaloneChatbotService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.conversation_history = []
        self.current_session_id = None
        
    def get_user_data_directory(self, username: str) -> Path:
        """Get the data directory for a specific user."""
        return auth.get_user_data_directory(username)
    
    def get_current_kb_id(self, username: str) -> str:
        """Get current knowledge base ID for user."""
        try:
            user_data_dir = self.get_user_data_directory(username)
            current_kb_file = user_data_dir / "current_kb.json"
            
            if current_kb_file.exists():
                with open(current_kb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('current_kb_id', 'default')
            else:
                # Create default KB if it doesn't exist
                return self.create_default_knowledge_base(username)
        except Exception as e:
            print(f"Error getting current KB ID: {str(e)}")
            return "default"
    
    def create_default_knowledge_base(self, username: str) -> str:
        """Create default knowledge base for user."""
        try:
            user_data_dir = self.get_user_data_directory(username)
            kb_dir = user_data_dir / "knowledge_bases"
            kb_dir.mkdir(parents=True, exist_ok=True)
            
            default_kb_id = "default"
            default_kb_dir = kb_dir / default_kb_id
            default_kb_dir.mkdir(exist_ok=True)
            
            # Create KB info
            kb_info = {
                "name": "База знаний по умолчанию",
                "description": "Основная база знаний",
                "created_at": "2024-01-01T00:00:00",
                "document_count": 0
            }
            
            kb_info_file = default_kb_dir / "kb_info.json"
            with open(kb_info_file, 'w', encoding='utf-8') as f:
                json.dump(kb_info, f, ensure_ascii=False, indent=2)
            
            # Create knowledge file
            knowledge_file = default_kb_dir / "knowledge.txt"
            if not knowledge_file.exists():
                with open(knowledge_file, 'w', encoding='utf-8') as f:
                    f.write("Вопрос: Как вас зовут?\nОтвет: Меня зовут NeuroBot Assistant. Я готов помочь вам с вопросами.")
            
            # Create current KB file
            current_kb_file = user_data_dir / "current_kb.json"
            with open(current_kb_file, 'w', encoding='utf-8') as f:
                json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
            
            return default_kb_id
        except Exception as e:
            print(f"Error creating default KB: {str(e)}")
            return "default"
    
    def get_settings(self, username: str) -> Dict[str, Any]:
        """Get chatbot settings from file for current KB."""
        try:
            user_data_dir = self.get_user_data_directory(username)
            current_kb_id = self.get_current_kb_id(username)
            
            # Use current KB's settings file
            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            system_prompt_file = kb_dir / "system_prompt.txt"
            
            if not system_prompt_file.exists():
                return {
                    'tone': 2,
                    'humor': 2,
                    'brevity': 2,
                    'additional_prompt': ''
                }
            
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # Handle legacy settings (convert string tone to numeric)
            if isinstance(settings.get('tone'), str):
                tone_mapping = {'formal': 0, 'friendly': 2, 'casual': 4}
                settings['tone'] = tone_mapping.get(settings['tone'], 2)
                
            return settings
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            return {
                'tone': 2,
                'humor': 2,
                'brevity': 2,
                'additional_prompt': ''
            }
    
    def get_vector_store(self, username: str):
        """Initialize and return the vector store components."""
        try:
            user_data_dir = self.get_user_data_directory(username)
            current_kb_id = self.get_current_kb_id(username)
            
            # Use current KB's vector store
            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            index_file = kb_dir / "vector_KB" / "index.faiss"
            docstore_file = kb_dir / "vector_KB" / "docstore.json"
            
            if not index_file.exists() or not docstore_file.exists():
                return None, None
            
            index = faiss.read_index(str(index_file))
            with open(docstore_file, 'r', encoding='utf-8') as f:
                docstore = json.load(f)
            return index, docstore
        except Exception as e:
            print(f"Error loading vector store: {str(e)}")
            return None, None
    
    def parse_knowledge_file(self, username: str) -> List[Dict[str, Any]]:
        """Parse the knowledge.txt file into a list of Q&A pairs."""
        try:
            user_data_dir = self.get_user_data_directory(username)
            current_kb_id = self.get_current_kb_id(username)
            
            # Use current KB's knowledge file
            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            knowledge_file = kb_dir / "knowledge.txt"
            
            if not knowledge_file.exists():
                return []
            
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error parsing knowledge file: {str(e)}")
            return []
        
        qa_pairs = []
        blocks = content.split('\n\n')
        
        for i, block in enumerate(blocks):
            if not block.strip():
                continue
                
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            if not lines:
                continue
                
            if not lines[0].startswith('Вопрос:'):
                continue
                
            question = lines[0][len('Вопрос:'):].strip()
            answer_lines = []
            for line in lines[1:]:
                line = line.strip()
                if line:
                    answer_lines.append(line)
            
            answer = '\n'.join(answer_lines)
            answer = re.sub(r'^(\s|\n)+', '', answer)
            answer = re.sub(r'(\s|\n)+$', '', answer)
            
            qa_pairs.append({
                'id': i,
                'question': question,
                'answer': answer,
                'content': f"Вопрос: {question}\n{answer}"
            })
        
        return qa_pairs
    
    def search_knowledge_base(self, username: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information."""
        try:
            # Load vector store
            index, docstore = self.get_vector_store(username)
            if index is None or docstore is None:
                return []
            
            # Get query vector
            query_vector = self.embeddings.embed_query(query)
            
            # Search in FAISS
            distances, indices = index.search(np.array([query_vector], dtype="float32"), top_k)
            
            # Get matching documents
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                doc_id = str(idx)
                if doc_id in docstore:
                    question = docstore[doc_id]
                    docs = self.parse_knowledge_file(username)
                    matching_doc = next((doc for doc in docs if doc['question'] == question), None)
                    if matching_doc:
                        matching_doc['similarity_score'] = float(1 / (1 + distance))
                        results.append(matching_doc)
            
            return results
        except Exception as e:
            print(f"Error searching knowledge base: {str(e)}")
            return []
    
    def build_system_prompt(self, username: str, settings: Dict[str, Any]) -> str:
        """Build the system prompt based on settings."""
        tone = settings.get('tone', 2)
        humor = settings.get('humor', 2)
        brevity = settings.get('brevity', 2)
        additional_prompt = settings.get('additional_prompt', '')
        
        # Get current KB info
        try:
            current_kb_id = self.get_current_kb_id(username)
            user_data_dir = self.get_user_data_directory(username)
            
            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            kb_info_file = kb_dir / "kb_info.json"
            kb_name = current_kb_id
            if kb_info_file.exists():
                with open(kb_info_file, 'r', encoding='utf-8') as f:
                    kb_info = json.load(f)
                    kb_name = kb_info.get('name', current_kb_id)
        except Exception as e:
            print(f"Error getting current KB info: {str(e)}")
            kb_name = "default"
        
        # Tone mapping (0-4 scale)
        tone_instructions = {
            0: 'Отвечай максимально формально и официально',
            1: 'Отвечай официально и профессионально',
            2: 'Отвечай дружелюбно и тепло',
            3: 'Отвечай неформально и расслабленно',
            4: 'Отвечай максимально неформально и разговорно'
        }
        
        # Humor level mapping (0-4 scale)
        humor_instructions = {
            0: 'Не используй юмор вообще',
            1: 'Используй совсем небольшой юмор',
            2: 'Используй умеренный юмор',
            3: 'Используй юмор, когда это уместно по ситуации',
            4: 'Используй юмор активно'
        }
        
        # Brevity level mapping (0-4 scale)
        brevity_instructions = {
            0: 'Отвечай МАКСИМАЛЬНО подробно',
            1: 'Отвечай подробно',
            2: 'Отвечай умеренно',
            3: 'Отвечай кратко',
            4: 'Отвечай МАКСИМАЛЬНО кратко'
        }
        
        base_prompt = f"""# ROLE: NeuroBot Assistant

Ты - умный помощник, который отвечает на вопросы пользователей на основе предоставленной базы знаний.

## CURRENT KNOWLEDGE BASE
Текущая база знаний: "{kb_name}"

## PERSONALITY SETTINGS
- Тон общения: {tone_instructions.get(tone, 'Отвечай дружелюбно')}
- Уровень юмора: {humor_instructions.get(humor, 'Используй умеренный юмор')}
- Уровень краткости: {brevity_instructions.get(brevity, 'Отвечай умеренно')}

## CORE RULES
1. Отвечай ТОЛЬКО на основе предоставленной информации из базы знаний
2. Если в базе знаний нет информации по вопросу, честно скажи об этом
3. Не выдумывай информацию
4. Если в сообщении есть маскированные данные, это значит, что пользователь отправил личные контакты. Сообщи пользователю, что контакты сохранены.

## ADDITIONAL INSTRUCTIONS
{additional_prompt if additional_prompt else 'Нет дополнительных инструкций'}

## KNOWLEDGE BASE CONTEXT
"""
        
        return base_prompt
    
    def get_or_create_session(self, username: str) -> str:
        """Get existing session or create new one for user - exactly like main site but with username."""
        try:
            dialogue_storage = get_dialogue_storage()
            kb_id = self.get_current_kb_id(username)
            
            # Get KB name
            try:
                user_data_dir = self.get_user_data_directory(username)
                kb_dir = user_data_dir / "knowledge_bases" / kb_id
                kb_info_file = kb_dir / "kb_info.json"
                kb_name = kb_id
                if kb_info_file.exists():
                    with open(kb_info_file, 'r', encoding='utf-8') as f:
                        kb_info = json.load(f)
                        kb_name = kb_info.get('name', kb_id)
            except Exception as e:
                print(f"Error getting KB name: {str(e)}")
                kb_name = kb_id
            
            # For standalone users, we use username as the "IP address" identifier
            # This ensures sessions are stored in the same format as main site
            user_identifier = f"standalone_{username}"
            
            # Check if session already exists for this user (like get_session_by_ip)
            existing_session = dialogue_storage.get_session_by_ip(user_identifier)
            
            if existing_session:
                # Use existing session
                session_id = existing_session['session_id']
                print(f"Using existing session {session_id} for user {username}")
            else:
                # Create new session exactly like main site does
                print(f"Creating new session for user {username} with KB {kb_id}")
                session_id = dialogue_storage.create_session(
                    ip_address=user_identifier,  # Use username as identifier
                    kb_id=kb_id,
                    kb_name=kb_name
                )
                print(f"Created new session {session_id} for user {username}")
            
            return session_id
            
        except Exception as e:
            print(f"Error in get_or_create_session for user {username}: {str(e)}")
            # Fallback to a simple session ID if there's an error
            return f"fallback_{username}_{kb_id}"
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID - like main site."""
        return self.current_session_id
    
    def set_current_session_id(self, session_id: str) -> None:
        """Set current session ID - like main site."""
        self.current_session_id = session_id
    
    def clear_current_session(self) -> None:
        """Clear current session ID - like main site."""
        self.current_session_id = None
    
    def generate_response(self, username: str, message: str) -> str:
        """Generate a response using OpenAI GPT with RAG - exactly like main site."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your-openai-api-key-here":
                return "⚠️ OpenAI API ключ не настроен. Пожалуйста, добавьте ваш API ключ в файл .env в папке Backend. Получить ключ можно на https://platform.openai.com/api-keys"

            dialogue_storage = get_dialogue_storage()

            # Get or create session exactly like main site does
            session_id = self.get_or_create_session(username)
            self.set_current_session_id(session_id)
            
            print(f"Using session {session_id} for user {username}")
            
            # Get settings
            settings = self.get_settings(username)
            
            # Mask personal information in user message before sending to OpenAI
            masked_user_message, mask_info = data_masker.mask_all_personal_data(message)
            
            # Log masking information if any personal data was found
            if mask_info.get('total_masked', 0) > 0:
                print(f"\n🔒 PERSONAL DATA MASKED for user {username}:")
                print(f"   Emails: {len(mask_info.get('emails', []))}")
                print(f"   Phones: {len(mask_info.get('phones', []))}")
                print(f"   Credit Cards: {len(mask_info.get('credit_cards', []))}")
                print(f"   Passports: {len(mask_info.get('passports', []))}")
                print(f"   SSNs: {len(mask_info.get('ssns', []))}")
                print(f"   Total masked items: {mask_info.get('total_masked', 0)}")
                print(f"   Original message: {message}")
                print(f"   Masked message: {masked_user_message}")
            
            # Search knowledge base using masked message
            relevant_docs = self.search_knowledge_base(username, masked_user_message)
            
            # Build context from relevant documents
            context = ""
            if relevant_docs:
                context_parts = []
                for i, doc in enumerate(relevant_docs, 1):
                    context_parts.append(f"### Q&A {i}")
                    context_parts.append(f"**Вопрос:** {doc['question']}")
                    context_parts.append(f"**Ответ:** {doc['answer']}")
                    context_parts.append("")  # Empty line for separation
                context = "\n".join(context_parts)
            else:
                context = "**Нет релевантной информации в базе знаний для данного вопроса.**"
            
            # Build system prompt
            system_prompt = self.build_system_prompt(username, settings)
            full_system_prompt = system_prompt + context
            
            # Prepare conversation history
            messages = [
                {"role": "system", "content": full_system_prompt}
            ]
            
            # Get conversation history from dialogue storage (last 10 messages) - exactly like main site
            conversation_history = []
            if self.get_current_session_id():
                session_data = dialogue_storage.get_session(self.get_current_session_id())
                if session_data and session_data.get('messages'):
                    # Get last 10 messages from the session
                    last_messages = session_data['messages'][-10:]
                    conversation_history = [
                        {"role": msg['role'], "content": msg['content']} 
                        for msg in last_messages
                    ]
                    print(f"Loaded {len(conversation_history)} messages from history for user {username}")
                else:
                    print(f"No conversation history found for user {username} in session {session_id}")
            else:
                print(f"No current session ID for user {username}")
            
            # Mask personal information in conversation history before sending to OpenAI
            masked_history = data_masker.mask_conversation_history(conversation_history)
            messages.extend(masked_history)
            
            # Add current user message (masked version for OpenAI)
            messages.append({"role": "user", "content": masked_user_message})
            
            # Print the complete information sent to OpenAI
            print("================================================")
            print(f"COMPLETE INFORMATION SENT TO OPENAI for user {username}:")
            for i, msg in enumerate(messages):
                print(f"\n--- MESSAGE {i+1} ({msg['role'].upper()}) ---")
                print(f"Content:\n{msg['content']}")
                print("-" * 100)
            print("================================================")
            
            # Get the current model for the user
            current_model = model_manager.get_current_model()
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=current_model,
                messages=messages
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Track token usage for balance
            try:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                balance_manager.consume_tokens(input_tokens, output_tokens, current_model, "chatbot")
                print(f"Token usage tracked for user {username}: {input_tokens} input, {output_tokens} output tokens")
            except Exception as e:
                print(f"Error tracking token usage: {e}")
            
            # Update conversation history with original (unmasked) user message - exactly like main site
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            # Keep only last 20 messages to manage memory (for backward compatibility) - exactly like main site
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Save messages to dialogue storage (original unmasked message) - exactly like main site
            if self.get_current_session_id():
                dialogue_storage = get_dialogue_storage()
                dialogue_storage.add_message(self.get_current_session_id(), "user", message)
                dialogue_storage.add_message(self.get_current_session_id(), "assistant", bot_response)
                print(f"Messages saved to dialogue storage for user {username} in session {session_id}")
            else:
                print(f"Warning: No session ID to save messages for user {username}")
            
            return bot_response
            
        except Exception as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "invalid api key" in error_msg.lower():
                return "❌ Ошибка аутентификации OpenAI API. Проверьте правильность вашего API ключа."
            elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                return "⚠️ Превышен лимит запросов к OpenAI API. Попробуйте позже."
            elif "api" in error_msg.lower():
                return f"❌ Ошибка OpenAI API: {error_msg}"
            else:
                print(f"Error generating response for user {username}: {error_msg}")
                return "Извините, произошла ошибка при обработке вашего вопроса. Попробуйте еще раз."
    
    def clear_user_session(self, username: str):
        """Clear user session and start new one - exactly like main site."""
        try:
            # Clear current session
            self.clear_current_session()
            
            # Start a new session
            dialogue_storage = get_dialogue_storage()
            kb_id = self.get_current_kb_id(username)
            
            # Get KB name
            try:
                user_data_dir = self.get_user_data_directory(username)
                kb_dir = user_data_dir / "knowledge_bases" / kb_id
                kb_info_file = kb_dir / "kb_info.json"
                kb_name = kb_id
                if kb_info_file.exists():
                    with open(kb_info_file, 'r', encoding='utf-8') as f:
                        kb_info = json.load(f)
                        kb_name = kb_info.get('name', kb_id)
            except Exception as e:
                print(f"Error getting KB name: {str(e)}")
                kb_name = kb_id
            
            # Create new session exactly like main site
            user_identifier = f"standalone_{username}"
            new_session_id = dialogue_storage.create_session(
                ip_address=user_identifier,
                kb_id=kb_id,
                kb_name=kb_name
            )
            
            self.set_current_session_id(new_session_id)
            print(f"Started new session {new_session_id} for user {username}")
            
        except Exception as e:
            print(f"Error clearing session for user {username}: {str(e)}")
    
    def get_user_session_id(self, username: str) -> Optional[str]:
        """Get current session ID for user."""
        return self.get_current_session_id()

# Global instance
standalone_chatbot_service = StandaloneChatbotService()
