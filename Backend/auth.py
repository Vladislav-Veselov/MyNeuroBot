#!/usr/bin/env python3
"""
Authentication module for NeuroBot.
Provides basic sign up and login functionality with user-specific data directories.
"""

import os
import json
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "user_data" / "users.json"
SESSION_SECRET = "your-secret-key-change-this-in-production"

class UserAuth:
    def __init__(self):
        self.users_file = USERS_FILE
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_users()
    
    def _load_users(self):
        """Load users from JSON file."""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
        else:
            self.users = {}
            self._save_users()
    
    def _save_users(self):
        """Save users to JSON file."""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    def register_user(self, username: str, password: str, email: str = "") -> Dict[str, Any]:
        """Register a new user."""
        # Validate input
        if not username or not password:
            return {"success": False, "error": "Username and password are required"}
        
        if len(username) < 3:
            return {"success": False, "error": "Username must be at least 3 characters"}
        
        if len(password) < 6:
            return {"success": False, "error": "Password must be at least 6 characters"}
        
        # Check if user already exists
        if username in self.users:
            return {"success": False, "error": "Username already exists"}
        
        # Create user directory
        user_data_dir = BASE_DIR / "user_data" / username
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create knowledge_bases directory structure
        kb_dir = user_data_dir / "knowledge_bases"
        kb_dir.mkdir(exist_ok=True)
        
        # Create default knowledge base
        default_kb_id = "default"
        default_kb_dir = kb_dir / default_kb_id
        default_kb_dir.mkdir(exist_ok=True)
        
        # Create KB info
        kb_info = {
            'name': 'Основная база знаний',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'document_count': 0,
            'analyze_clients': True  # Default to True for potential client analysis
        }
        
        with open(default_kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        # Create empty knowledge file
        with open(default_kb_dir / "knowledge.txt", 'w', encoding='utf-8') as f:
            f.write("")
        
        # Create vector store directory
        (default_kb_dir / "vector_KB").mkdir(exist_ok=True)
        
        # Set as current KB
        with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
        
        # Create default files for new user
        default_files = {
            "dialogues.json": json.dumps({
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_sessions": 0
                },
                "sessions": {}
            }, ensure_ascii=False, indent=2),
            "system_prompt.txt": json.dumps({
                "tone": "friendly",
                "humor": 2,
                "brevity": 2,
                "additional_prompt": ""
            }, ensure_ascii=False, indent=2),
            "last_fingerprint.json": json.dumps({}, ensure_ascii=False, indent=2)
        }
        
        for filename, content in default_files.items():
            file_path = user_data_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Add user to users.json
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "data_directory": str(user_data_dir)
        }
        
        self._save_users()
        
        return {"success": True, "message": "User registered successfully"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login a user."""
        if username not in self.users:
            return {"success": False, "error": "Invalid username or password"}
        
        user = self.users[username]
        if user["password_hash"] != self._hash_password(password):
            return {"success": False, "error": "Invalid username or password"}
        
        # Update last login
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        # Generate session token
        session_token = self._generate_session_token()
        
        return {
            "success": True,
            "username": username,
            "session_token": session_token,
            "data_directory": user["data_directory"]
        }
    
    def get_user_data_directory(self, username: str) -> Optional[Path]:
        """Get the data directory for a specific user."""
        if username in self.users:
            return Path(self.users[username]["data_directory"])
        return None
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        return username in self.users
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all users (for admin purposes)."""
        return {username: {**user, "password_hash": "***"} for username, user in self.users.items()}

# Global auth instance
auth = UserAuth()

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def login_required_web(f):
    """Decorator to require login for web routes (redirects to login page)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_data_dir() -> Path:
    """Get the current user's data directory."""
    username = session.get('username')
    if not username:
        raise ValueError("No user logged in")
    
    user_dir = auth.get_user_data_directory(username)
    if not user_dir:
        raise ValueError(f"User data directory not found for {username}")
    
    return user_dir 