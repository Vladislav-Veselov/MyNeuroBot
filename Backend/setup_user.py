#!/usr/bin/env python3
"""
Script to set up user alexey123 for standalone chatbot testing.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "user_data" / "users.json"
USERNAME = "alexey123"
PASSWORD = "tlnzl*4920"

from session_manager import ip_session_manager

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_user():
    """Set up the user with proper directory structure."""
    print(f"Setting up user: {USERNAME}")
    
    # Ensure user_data directory exists
    user_data_dir = BASE_DIR / "user_data"
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing users or create new
    users = {}
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            users = {}
    
    # Create user data
    user_data_directory = str(user_data_dir / USERNAME)
    users[USERNAME] = {
        "password_hash": hash_password(PASSWORD),
        "email": "",
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "data_directory": user_data_directory,
        "is_admin": False
    }
    
    # Save users
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        print(f"✓ Users saved to {USERS_FILE}")
    except Exception as e:
        print(f"✗ Error saving users: {e}")
        return False
    
    # Create user directory structure
    user_dir = Path(user_data_directory)
    user_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ User directory created: {user_dir}")
    
    # Create knowledge_bases directory
    kb_dir = user_dir / "knowledge_bases"
    kb_dir.mkdir(exist_ok=True)
    print(f"✓ Knowledge bases directory created: {kb_dir}")
    
    # Create default knowledge base
    default_kb_id = "default"
    default_kb_dir = kb_dir / default_kb_id
    default_kb_dir.mkdir(exist_ok=True)
    print(f"✓ Default KB directory created: {default_kb_dir}")
    
    # Create KB info
    kb_info = {
        "name": "База знаний по умолчанию",
        "description": "Основная база знаний",
        "created_at": datetime.now().isoformat(),
        "document_count": 0
    }
    
    kb_info_file = default_kb_dir / "kb_info.json"
    with open(kb_info_file, 'w', encoding='utf-8') as f:
        json.dump(kb_info, f, ensure_ascii=False, indent=2)
    print(f"✓ KB info created: {kb_info_file}")
    
    # Create knowledge file
    knowledge_file = default_kb_dir / "knowledge.txt"
    if not knowledge_file.exists():
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            f.write("Вопрос: Как вас зовут?\nОтвет: Меня зовут NeuroBot Assistant. Я готов помочь вам с вопросами.")
        print(f"✓ Knowledge file created: {knowledge_file}")
    
    # Create current KB file
    current_kb_file = user_dir / "current_kb.json"
    with open(current_kb_file, 'w', encoding='utf-8') as f:
        json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
    print(f"✓ Current KB file created: {current_kb_file}")
    
    # Create system prompt file
    system_prompt_file = default_kb_dir / "system_prompt.txt"
    if not system_prompt_file.exists():
        settings = {
            'tone': 2,
            'humor': 2,
            'brevity': 2,
            'additional_prompt': ''
        }
        with open(system_prompt_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print(f"✓ System prompt file created: {system_prompt_file}")
    
    # Create vector_KB directory
    vector_kb_dir = default_kb_dir / "vector_KB"
    vector_kb_dir.mkdir(exist_ok=True)
    print(f"✓ Vector KB directory created: {vector_kb_dir}")
    
    # Create empty index and docstore files
    index_file = vector_kb_dir / "index.faiss"
    docstore_file = vector_kb_dir / "docstore.json"
    
    if not index_file.exists():
        # Create a minimal FAISS index
        import numpy as np
        import faiss
        dimension = 1536  # OpenAI text-embedding-3-large dimension
        index = faiss.IndexFlatL2(dimension)
        faiss.write_index(index, str(index_file))
        print(f"✓ FAISS index created: {index_file}")
    
    if not docstore_file.exists():
        with open(docstore_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print(f"✓ Docstore file created: {docstore_file}")
    
    print(f"\n✓ User {USERNAME} setup completed successfully!")
    print(f"Username: {USERNAME}")
    print(f"Password: {PASSWORD}")
    print(f"Data directory: {user_data_directory}")
    
    return True

if __name__ == "__main__":
    try:
        setup_user()
    except Exception as e:
        print(f"Error setting up user: {e}")
        import traceback
        traceback.print_exc()
