#!/usr/bin/env python3
"""
Test to check KB filtering and existing sessions
"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dialogue_storage import get_dialogue_storage

def test_existing_sessions():
    """Check what sessions exist and their KB information"""
    print("Checking existing sessions...")
    
    try:
        dialogue_storage = get_dialogue_storage()
        all_sessions = dialogue_storage.get_all_sessions()
        
        print(f"Total sessions found: {len(all_sessions)}")
        
        if all_sessions:
            print("\nSession details:")
            for i, session in enumerate(all_sessions[:5]):  # Show first 5 sessions
                print(f"Session {i+1}:")
                print(f"  ID: {session['session_id'][:8]}...")
                print(f"  KB ID: {session.get('kb_id', 'None')}")
                print(f"  KB Name: {session.get('kb_name', 'None')}")
                print(f"  Messages: {session.get('total_messages', 0)}")
                print(f"  Last Updated: {session.get('last_updated', 'Unknown')}")
                print()
        else:
            print("No sessions found.")
            
        # Check KB distribution
        kb_counts = {}
        for session in all_sessions:
            kb_id = session.get('kb_id', 'unknown')
            kb_counts[kb_id] = kb_counts.get(kb_id, 0) + 1
            
        print("KB distribution:")
        for kb_id, count in kb_counts.items():
            print(f"  {kb_id}: {count} sessions")
            
    except Exception as e:
        print(f"Error checking sessions: {str(e)}")

if __name__ == "__main__":
    test_existing_sessions() 