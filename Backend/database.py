#!/usr/bin/env python3
"""
Database models and configuration for NeuroBot.
Provides persistent storage using PostgreSQL.
"""

import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and user management."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    balance = db.relationship('UserBalance', backref='user', uselist=False, cascade='all, delete-orphan')
    dialogues = db.relationship('Dialogue', backref='user', cascade='all, delete-orphan')
    knowledge_bases = db.relationship('KnowledgeBase', backref='user', cascade='all, delete-orphan')

class UserBalance(db.Model):
    """User balance and pricing information."""
    __tablename__ = 'user_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance_rub = db.Column(db.Float, default=0.0)
    total_cost_usd = db.Column(db.Float, default=0.0)
    total_cost_rub = db.Column(db.Float, default=0.0)
    total_input_tokens = db.Column(db.Integer, default=0)
    total_output_tokens = db.Column(db.Integer, default=0)
    current_model = db.Column(db.String(50), default='gpt-4o-mini')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class Dialogue(db.Model):
    """Dialogue storage for chat conversations."""
    __tablename__ = 'dialogues'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False)
    dialogue_data = db.Column(db.Text)  # JSON string of dialogue data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_dialogue_data(self, data):
        """Set dialogue data as JSON string."""
        self.dialogue_data = json.dumps(data)
    
    def get_dialogue_data(self):
        """Get dialogue data from JSON string."""
        if self.dialogue_data:
            return json.loads(self.dialogue_data)
        return {}

class KnowledgeBase(db.Model):
    """Knowledge base storage for user documents."""
    __tablename__ = 'knowledge_bases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    kb_id = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    documents = db.Column(db.Text)  # JSON string of documents
    vector_data = db.Column(db.LargeBinary)  # FAISS index data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_documents(self, docs):
        """Set documents as JSON string."""
        self.documents = json.dumps(docs)
    
    def get_documents(self):
        """Get documents from JSON string."""
        if self.documents:
            return json.loads(self.documents)
        return []

class Transaction(db.Model):
    """Transaction history for user activities."""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Float, default=0.0)
    cost_rub = db.Column(db.Float, default=0.0)
    is_credit = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='transactions')

def init_database(app):
    """Initialize database with Flask app."""
    # Configure database URL
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        # Fix for SQLAlchemy 1.4+ compatibility
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if not database_url:
        # Fallback to SQLite for local development
        database_url = 'sqlite:///neurobot.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            from auth import ADMIN_PASSWORD_HASH
            admin_user = User(
                username='admin',
                password_hash=ADMIN_PASSWORD_HASH,
                email='admin@neurobot.local',
                is_admin=True
            )
            db.session.add(admin_user)
            
            # Create admin balance
            admin_balance = UserBalance(user=admin_user, balance_rub=1000.0)
            db.session.add(admin_balance)
            
            db.session.commit()
    
    return db

def migrate_file_data_to_database():
    """Migrate existing file-based data to database."""
    from pathlib import Path
    import json
    
    # Get base directory
    base_dir = Path(__file__).resolve().parent.parent
    users_file = base_dir / "user_data" / "users.json"
    
    if not users_file.exists():
        return
    
    try:
        # Load existing users
        with open(users_file, 'r', encoding='utf-8') as f:
            existing_users = json.load(f)
        
        for username, user_data in existing_users.items():
            # Check if user already exists in database
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                continue
            
            # Create new user
            new_user = User(
                username=username,
                password_hash=user_data['password_hash'],
                email=user_data.get('email', ''),
                created_at=datetime.fromisoformat(user_data['created_at']),
                last_login=datetime.fromisoformat(user_data['last_login'])
            )
            db.session.add(new_user)
            db.session.flush()  # Get user ID
            
            # Create user balance
            user_balance = UserBalance(user_id=new_user.id)
            db.session.add(user_balance)
            
            # Migrate user directory data if exists
            user_dir = Path(user_data.get('data_directory', ''))
            if user_dir.exists():
                # Migrate dialogues
                dialogues_file = user_dir / "dialogues.json"
                if dialogues_file.exists():
                    try:
                        with open(dialogues_file, 'r', encoding='utf-8') as f:
                            dialogues_data = json.load(f)
                        
                        dialogue = Dialogue(
                            user_id=new_user.id,
                            session_id=f"{username}_migrated",
                            dialogue_data=json.dumps(dialogues_data)
                        )
                        db.session.add(dialogue)
                    except Exception as e:
                        print(f"Error migrating dialogues for {username}: {e}")
        
        db.session.commit()
        print("Data migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback()
