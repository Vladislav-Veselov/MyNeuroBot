#!/usr/bin/env python3
"""
Shared utility for locating knowledge bases by password.
This avoids circular imports between blueprints and services.
"""

from pathlib import Path
from typing import Optional

def find_kb_by_password_in_dir(user_data_dir: Path, password: str) -> Optional[str]:
    """
    Find a knowledge base by password in a specific user data directory.
    
    Args:
        user_data_dir: Path to the user's data directory
        password: Password to search for
        
    Returns:
        Knowledge base ID if found, None otherwise
    """
    kb_dir = user_data_dir / "knowledge_bases"
    if not kb_dir.exists():
        return None
        
    for sub in kb_dir.iterdir():
        if not sub.is_dir():
            continue
            
        pw_file = sub / "password.txt"
        if pw_file.exists() and pw_file.read_text(encoding="utf-8").strip() == password:
            return sub.name
            
    return None
