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
from dialogue_storage import dialogue_storage

# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found in .env file.")
os.environ["OPENAI_API_KEY"] = api_key


# Configuration
KNOWLEDGE_FILE = Path(r"C:\PARTNERS\NeuroBot\Backend\knowledge.txt")
SYSTEM_PROMPT_FILE = Path(r"C:\PARTNERS\NeuroBot\Backend\system_prompt.txt")
VECTOR_STORE_DIR = Path(r"C:\PARTNERS\NeuroBot\Backend\vector_KB")
INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
DOCSTORE_FILE = VECTOR_STORE_DIR / "docstore.json"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatbotService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.conversation_history = []
        self.current_session_id = None
        
    def get_settings(self) -> Dict[str, Any]:
        """Get chatbot settings from file."""
        try:
            if not SYSTEM_PROMPT_FILE.exists():
                return {
                    'tone': 'friendly',
                    'humor': 2,
                    'brevity': 2,
                    'additional_prompt': ''
                }
            
            with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            return {
                'tone': 'friendly',
                'humor': 2,
                'brevity': 2,
                'additional_prompt': ''
            }
    
    def get_vector_store(self):
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
    
    def parse_knowledge_file(self) -> List[Dict[str, Any]]:
        """Parse the knowledge.txt file into a list of Q&A pairs."""
        if not KNOWLEDGE_FILE.exists():
            return []
        
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
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
    
    def search_knowledge_base(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
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
        tone = settings.get('tone', 'friendly')
        humor = settings.get('humor', 2)
        brevity = settings.get('brevity', 2)
        additional_prompt = settings.get('additional_prompt', '')
        
        # Tone mapping
        tone_instructions = {
            'friendly': 'Отвечай дружелюбно и тепло',
            'formal': 'Отвечай официально и профессионально',
            'casual': 'Отвечай неформально и расслабленно',
            'professional': 'Отвечай профессионально и компетентно'
        }
        
        # Humor level mapping
        humor_instructions = {
            0: 'Не используй юмор',
            1: 'Используй минимальный юмор',
            2: 'Используй умеренный юмор',
            3: 'Используй юмор по ситуации',
            4: 'Используй юмор активно',
            5: 'Используй юмор ОЧЕНЬ активно'
        }
        
        # Brevity level mapping
        brevity_instructions = {
            0: 'Отвечай ОЧЕНЬ подробно',
            1: 'Отвечай подробно',
            2: 'Отвечай умеренно',
            3: 'Отвечай кратко',
            4: 'Отвечай очень кратко',
            5: 'Отвечай МАКСИМАЛЬНО кратко'
        }
        
        base_prompt = f"""# ROLE: NeuroBot Assistant

Ты - умный помощник, который отвечает на вопросы пользователей на основе предоставленной базы знаний.

## PERSONALITY SETTINGS
- Тон общения: {tone_instructions.get(tone, 'Отвечай дружелюбно')}
- Уровень юмора: {humor_instructions.get(humor, 'Используй умеренный юмор')}
- Уровень краткости: {brevity_instructions.get(brevity, 'Отвечай умеренно')}

## CORE RULES
1. Отвечай ТОЛЬКО на основе предоставленной информации из базы знаний
2. Если в базе знаний нет информации по вопросу, честно скажи об этом
3. Не выдумывай информацию
4. Отвечай на русском языке
5. Будь полезным и информативным

## ADDITIONAL INSTRUCTIONS
{additional_prompt if additional_prompt else 'Нет дополнительных инструкций'}

## KNOWLEDGE BASE CONTEXT
"""
        
        return base_prompt
    
    def generate_response(self, user_message: str, session_id: Optional[str] = None) -> str:
        """Generate a response using OpenAI GPT with RAG."""
        try:
            # Check if OpenAI API key is configured
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your-openai-api-key-here":
                return "⚠️ OpenAI API ключ не настроен. Пожалуйста, добавьте ваш API ключ в файл .env в папке Backend. Получить ключ можно на https://platform.openai.com/api-keys"
            
            # Handle session management
            if session_id:
                self.current_session_id = session_id
            elif not self.current_session_id:
                # Create new session if none exists
                self.current_session_id = dialogue_storage.create_session()
            
            # Get settings
            settings = self.get_settings()
            
            # Search knowledge base
            relevant_docs = self.search_knowledge_base(user_message)
            
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
            
            # Add conversation history (last 10 messages to avoid token limits)
            for msg in self.conversation_history[-10:]:
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Print the complete information sent to OpenAI
            print("\n" + "="*100)
            print("COMPLETE INFORMATION SENT TO OPENAI")
            print("="*100)
            for i, msg in enumerate(messages):
                print(f"\n--- MESSAGE {i+1} ({msg['role'].upper()}) ---")
                print(f"Content:\n{msg['content']}")
                print("-" * 100)
            print("\n" + "="*100)
            print("END COMPLETE INFORMATION")
            print("="*100 + "\n")
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            # Keep only last 20 messages to manage memory
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Save messages to dialogue storage
            if self.current_session_id:
                dialogue_storage.add_message(self.current_session_id, "user", user_message)
                dialogue_storage.add_message(self.current_session_id, "assistant", bot_response)
            
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
        self.current_session_id = None
    
    def start_new_session(self) -> str:
        """Start a new dialogue session."""
        self.conversation_history = []
        self.current_session_id = dialogue_storage.create_session()
        return self.current_session_id
    
    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self.current_session_id

# Global instance
chatbot_service = ChatbotService() 