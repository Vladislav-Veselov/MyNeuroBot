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
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, session, redirect, url_for


# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "user_data" / "users.json"
SESSION_SECRET = "your-secret-key-change-this-in-production"

# Admin configuration - CHANGE THESE TO YOUR CREDENTIALS
ADMIN_USERNAME = "admin"  # Change this to your admin username
ADMIN_PASSWORD_HASH = "b94e20e6a1355e03db7ca65282836bd2ad92b8b975b3e2181f7baa6e6a8a9a5f"  # Password: linoleum787898!

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
    
    def is_admin(self, username: str) -> bool:
        """Check if user is admin."""
        return username == ADMIN_USERNAME
    
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
        
        # Debug: Print user directory creation
        print(f"Creating user directory: {user_data_dir}")
        print(f"User directory exists: {user_data_dir.exists()}")
        print(f"User directory parent: {user_data_dir.parent}")
        print(f"User directory parent exists: {user_data_dir.parent.exists()}")
        
        # Create knowledge_bases directory structure
        kb_dir = user_data_dir / "knowledge_bases"
        kb_dir.mkdir(exist_ok=True)
        
        # Create default knowledge base
        default_kb_id = "default"
        default_kb_dir = kb_dir / default_kb_id
        default_kb_dir.mkdir(exist_ok=True)
        
        # Create KB info
        kb_info = {
            'name': 'База знаний по умолчанию',
            'created_at': datetime.now(timezone(timedelta(hours=3))).isoformat(),
            'updated_at': datetime.now(timezone(timedelta(hours=3))).isoformat(),
            'document_count': 0,
            'analyze_clients': True  # Default to True for potential client analysis
        }
        
        with open(default_kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        # Create empty knowledge file
        with open(default_kb_dir / "knowledge.json", 'w', encoding='utf-8') as f:
            f.write("[]")
        
        # Create vector store directory
        (default_kb_dir / "vector_KB").mkdir(exist_ok=True)
        
        # Set as current KB
        with open(user_data_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
        
        # Create default files for new user
        default_files = {
            "dialogues.json": json.dumps({
                "metadata": {
                    "created_at": datetime.now(timezone(timedelta(hours=3))).isoformat(),
                    "last_updated": datetime.now(timezone(timedelta(hours=3))).isoformat(),
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
            "created_at": datetime.now(timezone(timedelta(hours=3))).isoformat(),
            "last_login": None,
            "data_directory": str(user_data_dir)
        }
        
        print(f"About to save users.json to: {self.users_file}")
        print(f"Users data: {list(self.users.keys())}")
        self._save_users()
        print(f"Users.json saved successfully. File exists: {self.users_file.exists()}")
        
        # Debug: Check file sizes in user directory
        import os
        for root, dirs, files in os.walk(user_data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                print(f"File: {file_path}, Size: {size} bytes")
        
        return {"success": True, "message": "User registered successfully"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login a user."""
        # Check if this is admin login
        if username == ADMIN_USERNAME:
            if self._hash_password(password) == ADMIN_PASSWORD_HASH:
                return {
                    "success": True,
                    "username": username,
                    "session_token": self._generate_session_token(),
                    "data_directory": str(BASE_DIR / "user_data" / "admin"),
                    "is_admin": True
                }
            else:
                return {"success": False, "error": "Invalid username or password"}
        
        # Regular user login
        if username not in self.users:
            return {"success": False, "error": "Invalid username or password"}
        
        user = self.users[username]
        if user["password_hash"] != self._hash_password(password):
            return {"success": False, "error": "Invalid username or password"}
        
        # Update last login
        user["last_login"] = datetime.now(timezone(timedelta(hours=3))).isoformat()
        self._save_users()
        
        # Generate session token
        session_token = self._generate_session_token()
        
        return {
            "success": True,
            "username": username,
            "session_token": session_token,
            "data_directory": user["data_directory"],
            "is_admin": False
        }
    
    def get_user_data_directory(self, username: str) -> Optional[Path]:
        """Get the data directory for a specific user."""
        if username == ADMIN_USERNAME:
            return BASE_DIR / "user_data" / "admin"
        if username in self.users:
            return Path(self.users[username]["data_directory"])
        return None
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        return username == ADMIN_USERNAME or username in self.users
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all users (for admin purposes)."""
        users_copy = {username: {**user, "password_hash": "***"} for username, user in self.users.items()}
        # Add admin user
        users_copy[ADMIN_USERNAME] = {
            "password_hash": "***",
            "email": "",
            "created_at": "admin",
            "last_login": None,
            "data_directory": str(BASE_DIR / "user_data" / "admin"),
            "is_admin": True
        }
        return users_copy

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

def admin_required(f):
    """Decorator to require admin privileges for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Login required"}), 401
        if not auth.is_admin(session['username']):
            return jsonify({"error": "Admin privileges required"}), 403
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

def admin_required_web(f):
    """Decorator to require admin privileges for web routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if not auth.is_admin(session['username']):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_data_dir() -> Path:
    """Get the current user's data directory."""
    from tenant_context import get_user_data_dir_override
    
    # Check for tenant context override first
    override = get_user_data_dir_override()
    if override:
        return Path(override)
    
    # Fallback: existing logged-in user logic
    username = session.get('username')
    if not username:
        raise ValueError("No user logged in")
    
    user_dir = auth.get_user_data_directory(username)
    if not user_dir:
        raise ValueError(f"User data directory not found for {username}")
    
    return user_dir 