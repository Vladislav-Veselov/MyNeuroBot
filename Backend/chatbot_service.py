import os
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from vectorize import rebuild_vector_store
import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from dialogue_storage import get_dialogue_storage
from session_manager import ip_session_manager
from data_masking import data_masker
from model_manager import model_manager
from balance_manager import balance_manager
from tenant_context import get_widget_settings_override  # NEW import

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

class ChatbotService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.conversation_history = []
        
    def get_settings(self) -> Dict[str, Any]:
        """Get chatbot settings from file for current KB, with optional per-request overrides."""
        try:
            from auth import get_current_user_data_dir
            user_data_dir = get_current_user_data_dir()
            current_kb_id, _ = self.get_current_kb_info()

            # Use current KB's settings file
            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            system_prompt_file = kb_dir / "system_prompt.txt"

            # defaults
            settings = {
                "tone": 2,
                "humor": 2,
                "brevity": 2,
                "additional_prompt": ""
            }

            if system_prompt_file.exists():
                with open(system_prompt_file, "r", encoding="utf-8") as f:
                    file_settings = json.load(f)
                # Handle legacy string tone in file
                if isinstance(file_settings.get("tone"), str):
                    tone_mapping = {"formal": 0, "friendly": 2, "casual": 4}
                    file_settings["tone"] = tone_mapping.get(file_settings["tone"], 2)
                settings.update(file_settings)

            # NEW: apply per-request override from custom widget (tone/humor/brevity only)
            override = get_widget_settings_override()
            if override:
                def _coerce_0_4(v, default):
                    try:
                        iv = int(v)
                        return max(0, min(4, iv))
                    except (TypeError, ValueError):
                        return default
                if "tone" in override:
                    settings["tone"] = _coerce_0_4(override["tone"], settings["tone"])
                if "humor" in override:
                    settings["humor"] = _coerce_0_4(override["humor"], settings["humor"])
                if "brevity" in override:
                    settings["brevity"] = _coerce_0_4(override["brevity"], settings["brevity"])
                # NOTE: additional_prompt is intentionally NOT overridden

            return settings

        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            return {
                "tone": 2,
                "humor": 2,
                "brevity": 2,
                "additional_prompt": ""
            }
    
    def get_vector_store(self):
        """Initialize and return the vector store components."""
        try:
            from auth import get_current_user_data_dir
            user_data_dir = get_current_user_data_dir()
            current_kb_id, _ = self.get_current_kb_info()
            
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
    
    def parse_knowledge_file(self) -> List[Dict[str, Any]]:
        """Parse knowledge.json of the current KB into Q&A pairs."""
        try:
            from auth import get_current_user_data_dir
            user_data_dir = get_current_user_data_dir()
            current_kb_id, _ = self.get_current_kb_info()

            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            knowledge_file = kb_dir / "knowledge.json"
            if not knowledge_file.exists():
                return []

            data = json.loads(knowledge_file.read_text(encoding='utf-8'))
            out = []
            for i, item in enumerate(data):
                q = (item.get("question") or "").strip()
                a = (item.get("answer") or "").strip()
                out.append({"id": i, "question": q, "answer": a, "content": f"Вопрос: {q}\n{a}"})
            return out
        except Exception as e:
            print(f"Error parsing knowledge file: {str(e)}")
            return []
    
    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information."""
        try:
            # Load vector store
            index, docstore = self.get_vector_store()
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
                    docs = self.parse_knowledge_file()
                    matching_doc = next((doc for doc in docs if doc['question'] == question), None)
                    if matching_doc:
                        matching_doc['similarity_score'] = float(1 / (1 + distance))
                        results.append(matching_doc)
            
            return results
        except Exception as e:
            print(f"Error searching knowledge base: {str(e)}")
            return []
    
    def build_system_prompt(self, settings: Dict[str, Any]) -> str:
        """Build the system prompt based on settings."""
        tone = settings.get('tone', 2)
        humor = settings.get('humor', 2)
        brevity = settings.get('brevity', 2)
        additional_prompt = settings.get('additional_prompt', '')
        
        # Get current KB info
        try:
            _, kb_name = self.get_current_kb_info()
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
    
    def generate_response(self, user_message: str, session_id: Optional[str] = None) -> str:
        """Generate a response using OpenAI GPT with RAG."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your-openai-api-key-here":
                return "⚠️ OpenAI API ключ не настроен. Пожалуйста, добавьте ваш API ключ в файл .env в папке Backend. Получить ключ можно на https://platform.openai.com/api-keys"

            dialogue_storage = get_dialogue_storage()
            client_ip = ip_session_manager.get_client_ip()

            # Enforce 1 session per IP: always check storage for existing session for this IP
            existing_session = dialogue_storage.get_session_by_ip(client_ip)
            if session_id:
                # If a session_id is provided, use it (but only if it matches the IP session)
                if existing_session and existing_session['session_id'] == session_id:
                    self.set_current_session_id(session_id)
                else:
                    # Provided session_id does not match the IP session, use the IP session
                    if existing_session:
                        self.set_current_session_id(existing_session['session_id'])
                    else:
                        # No session for this IP, create one with KB info
                        kb_id, kb_name = self.get_current_kb_info()
                        new_session_id = dialogue_storage.create_session(
                            ip_address=client_ip,
                            kb_id=kb_id,
                            kb_name=kb_name
                        )
                        self.set_current_session_id(new_session_id)
            else:
                # No session_id provided
                if existing_session:
                    self.set_current_session_id(existing_session['session_id'])
                else:
                    # No session for this IP, create one with KB info
                    kb_id, kb_name = self.get_current_kb_info()
                    new_session_id = dialogue_storage.create_session(
                        ip_address=client_ip,
                        kb_id=kb_id,
                        kb_name=kb_name
                    )
                    self.set_current_session_id(new_session_id)

            # Get settings
            settings = self.get_settings()
            
            # Mask personal information in user message before sending to OpenAI
            masked_user_message, mask_info = data_masker.mask_all_personal_data(user_message)
            
            # Log masking information if any personal data was found
            if mask_info.get('total_masked', 0) > 0:
                print(f"\n🔒 PERSONAL DATA MASKED:")
                print(f"   Emails: {len(mask_info.get('emails', []))}")
                print(f"   Phones: {len(mask_info.get('phones', []))}")
                print(f"   Credit Cards: {len(mask_info.get('credit_cards', []))}")
                print(f"   Passports: {len(mask_info.get('passports', []))}")
                print(f"   SSNs: {len(mask_info.get('ssns', []))}")
                print(f"   Total masked items: {mask_info.get('total_masked', 0)}")
                print(f"   Original message: {user_message}")
                print(f"   Masked message: {masked_user_message}")
            
            # Search knowledge base using masked message
            relevant_docs = self.search_knowledge_base(masked_user_message)
            
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
            system_prompt = self.build_system_prompt(settings)
            full_system_prompt = system_prompt + context
            
            # Prepare conversation history
            messages = [
                {"role": "system", "content": full_system_prompt}
            ]
            
            # Get conversation history from dialogue storage (last 20 messages)
            conversation_history = []
            if self.get_current_session_id():
                session_data = dialogue_storage.get_session(self.get_current_session_id())
                if session_data and session_data.get('messages'):
                    # Get last 20 messages from the session
                    last_messages = session_data['messages'][-20:]
                    conversation_history = [
                        {"role": msg['role'], "content": msg['content']} 
                        for msg in last_messages
                    ]
            
            # Mask personal information in conversation history before sending to OpenAI
            masked_history = data_masker.mask_conversation_history(conversation_history)
            messages.extend(masked_history)
            
            # Add current user message (masked version for OpenAI)
            messages.append({"role": "user", "content": masked_user_message})
            
            # Print the complete information sent to OpenAI
            print("================================================")
            print("COMPLETE INFORMATION SENT TO OPENAI:")
            for i, msg in enumerate(messages):
                print(f"\n--- MESSAGE {i+1} ({msg['role'].upper()}) ---")
                print(f"Content:\n{msg['content']}")
                print("-" * 100)
            print("================================================")
            
            # Get the current model for the user
            current_model = model_manager.get_current_model()
            
            # Log model selection for debugging
            print(f"🤖 MODEL SELECTED: {current_model}")
            print(f"📝 USER MESSAGE: {user_message}")
            
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
                print(f"Token usage tracked: {input_tokens} input, {output_tokens} output tokens")
            except Exception as e:
                print(f"Error tracking token usage: {e}")
            
            # Update conversation history with original (unmasked) user message
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            # Keep only last 20 messages to manage memory (for backward compatibility)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Save messages to dialogue storage (original unmasked message)
            if self.get_current_session_id():
                dialogue_storage = get_dialogue_storage()
                dialogue_storage.add_message(self.get_current_session_id(), "user", user_message)
                dialogue_storage.add_message(self.get_current_session_id(), "assistant", bot_response)
            
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
                print(f"Error generating response: {error_msg}")
                return "Извините, произошла ошибка при обработке вашего вопроса. Попробуйте еще раз."
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        # Start a new session to clear the dialogue storage history
        self.start_new_session()
    
    def reset_session(self):
        """Reset the current session ID to force creation of a new session."""
        self.clear_current_session()
    
    def start_new_session(self) -> str:
        """Start a new dialogue session."""
        self.conversation_history = []
        dialogue_storage = get_dialogue_storage()
        client_ip = ip_session_manager.get_client_ip()
        kb_id, kb_name = self.get_current_kb_info()
        new_session_id = dialogue_storage.create_session(
            ip_address=client_ip,
            kb_id=kb_id,
            kb_name=kb_name
        )
        self.set_current_session_id(new_session_id)
        return self.get_current_session_id()
    
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID for the requesting IP."""
        return ip_session_manager.get_current_ip_session_id()
    
    def set_current_session_id(self, session_id: str) -> None:
        """Set the current session ID for the requesting IP."""
        ip_session_manager.set_current_ip_session_id(session_id)
    
    def clear_current_session(self) -> None:
        """Clear the current session for the requesting IP."""
        ip_session_manager.clear_current_ip_session()
    
    def get_current_kb_info(self) -> tuple[str, str]:
        """Resolve current KB from the ACTIVE SESSION first; fallback to current_kb.json (dashboard only)."""
        try:
            dialogue_storage = get_dialogue_storage()
            current_session_id = self.get_current_session_id()
            if current_session_id:
                session = dialogue_storage.get_session(current_session_id)
                if session:
                    kb_id = session.get("kb_id") or session.get("metadata", {}).get("kb_id")
                    kb_name = session.get("kb_name") or session.get("metadata", {}).get("kb_name")
                    if kb_id:
                        if not kb_name:
                            from auth import get_current_user_data_dir
                            user_data_dir = get_current_user_data_dir()
                            kb_dir = user_data_dir / "knowledge_bases" / kb_id
                            kb_info_file = kb_dir / "kb_info.json"
                            kb_name = kb_id
                            if kb_info_file.exists():
                                with open(kb_info_file, 'r', encoding='utf-8') as f:
                                    info = json.load(f)
                                    kb_name = info.get('name', kb_id)
                        return kb_id, kb_name or kb_id

            # Fallback for authenticated dashboard / legacy
            from auth import get_current_user_data_dir
            user_data_dir = get_current_user_data_dir()
            current_kb_file = user_data_dir / "current_kb.json"
            if current_kb_file.exists():
                with open(current_kb_file, 'r', encoding='utf-8') as f:
                    current_kb_data = json.load(f)
                    current_kb_id = current_kb_data.get('current_kb_id', 'default')
            else:
                current_kb_id = "default"

            kb_dir = user_data_dir / "knowledge_bases" / current_kb_id
            kb_info_file = kb_dir / "kb_info.json"
            kb_name = current_kb_id
            if kb_info_file.exists():
                with open(kb_info_file, 'r', encoding='utf-8') as f:
                    kb_info = json.load(f)
                    kb_name = kb_info.get('name', current_kb_id)

            return current_kb_id, kb_name
        except Exception as e:
            print(f"Error getting current KB info: {str(e)}")
            return "default", "База знаний по умолчанию"

# Global instance
chatbot_service = ChatbotService() 