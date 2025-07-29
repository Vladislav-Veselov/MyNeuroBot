#!/usr/bin/env python3
"""
Migration script to update existing users to the new knowledge base structure.
This script moves existing knowledge.txt files to the new knowledge_bases structure.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_DIR = BASE_DIR / "user_data"

def migrate_user(user_dir: Path):
    """Migrate a single user to the new KB structure."""
    try:
        # Check if user already has knowledge_bases directory
        kb_dir = user_dir / "knowledge_bases"
        if kb_dir.exists():
            print(f"  User {user_dir.name} already has KB structure, skipping...")
            return
        
        # Check if user has old knowledge.txt
        old_knowledge_file = user_dir / "knowledge.txt"
        if not old_knowledge_file.exists():
            print(f"  User {user_dir.name} has no knowledge.txt, creating default KB...")
            create_default_kb_for_user(user_dir)
            return
        
        print(f"  Migrating user {user_dir.name}...")
        
        # Create knowledge_bases directory
        kb_dir.mkdir(exist_ok=True)
        
        # Create default KB
        default_kb_id = "default"
        default_kb_dir = kb_dir / default_kb_id
        default_kb_dir.mkdir(exist_ok=True)
        
        # Move old knowledge.txt to new location
        new_knowledge_file = default_kb_dir / "knowledge.txt"
        shutil.move(str(old_knowledge_file), str(new_knowledge_file))
        
        # Create KB info
        kb_info = {
            'name': 'Основная база знаний',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'document_count': 0,  # Will be updated when KB is accessed
            'analyze_clients': True  # Default to True for potential client analysis
        }
        
        with open(default_kb_dir / "kb_info.json", 'w', encoding='utf-8') as f:
            json.dump(kb_info, f, ensure_ascii=False, indent=2)
        
        # Create vector store directory
        (default_kb_dir / "vector_KB").mkdir(exist_ok=True)
        
        # Set as current KB
        with open(user_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
        
        # Remove old vector_KB directory if it exists
        old_vector_dir = user_dir / "vector_KB"
        if old_vector_dir.exists():
            shutil.rmtree(old_vector_dir)
        
        print(f"  Successfully migrated user {user_dir.name}")
        
    except Exception as e:
        print(f"  Error migrating user {user_dir.name}: {str(e)}")

def create_default_kb_for_user(user_dir: Path):
    """Create a default KB for a user who doesn't have one."""
    try:
        # Create knowledge_bases directory
        kb_dir = user_dir / "knowledge_bases"
        kb_dir.mkdir(exist_ok=True)
        
        # Create default KB
        default_kb_id = "default"
        default_kb_dir = kb_dir / default_kb_id
        default_kb_dir.mkdir(exist_ok=True)
        
        # Create empty knowledge file
        with open(default_kb_dir / "knowledge.txt", 'w', encoding='utf-8') as f:
            f.write("")
        
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
        
        # Create vector store directory
        (default_kb_dir / "vector_KB").mkdir(exist_ok=True)
        
        # Set as current KB
        with open(user_dir / "current_kb.json", 'w', encoding='utf-8') as f:
            json.dump({'current_kb_id': default_kb_id}, f, ensure_ascii=False, indent=2)
        
        print(f"  Created default KB for user {user_dir.name}")
        
    except Exception as e:
        print(f"  Error creating default KB for user {user_dir.name}: {str(e)}")

def main():
    """Main migration function."""
    print("Starting migration to new knowledge base structure...")
    
    if not USER_DATA_DIR.exists():
        print("User data directory not found!")
        return
    
    # Get all user directories
    user_dirs = [d for d in USER_DATA_DIR.iterdir() if d.is_dir() and d.name != "__pycache__"]
    
    if not user_dirs:
        print("No user directories found!")
        return
    
    print(f"Found {len(user_dirs)} user directories:")
    for user_dir in user_dirs:
        print(f"  - {user_dir.name}")
    
    print("\nStarting migration...")
    for user_dir in user_dirs:
        migrate_user(user_dir)
    
    print("\nMigration completed!")

if __name__ == "__main__":
    main() 