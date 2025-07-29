#!/usr/bin/env python3
"""
Test script to reproduce the vladis12345 session issue.
"""

import json
import os
from pathlib import Path
from dialogue_storage import DialogueStorage
from session_manager import IPSessionManager

def test_vladis12345_session():
    """Test session creation for vladis12345 account."""
    
    # Test with vladis12345 user's dialogues.json
    test_file = Path("../user_data/vladis12345/dialogues.json")
    
    print(f"Testing session creation for vladis12345 with file: {test_file}")
    print(f"File exists: {test_file.exists()}")
    
    # Create test storage instance
    storage = DialogueStorage(str(test_file))
    
    # Create test session manager
    session_manager = IPSessionManager()
    
    # Check current state
    print("\n1. Current state:")
    all_data = storage._load_all_sessions()
    print(f"Total sessions: {all_data['metadata']['total_sessions']}")
    print(f"Sessions: {list(all_data['sessions'].keys())}")
    
    # Simulate a new conversation
    print("\n2. Simulating new conversation...")
    
    # Test IP address
    test_ip = "192.168.1.100"
    
    # Check if there's already a session for this IP
    existing_session = storage.get_session_by_ip(test_ip)
    if existing_session:
        print(f"Found existing session for IP {test_ip}: {existing_session['session_id'][:8]}...")
        session_id = existing_session['session_id']
    else:
        print(f"No existing session for IP {test_ip}, creating new one...")
        session_id = storage.create_session(ip_address=test_ip)
        print(f"Created new session: {session_id[:8]}...")
    
    # Set the session in the session manager
    session_manager.set_session_id_for_ip(test_ip, session_id)
    
    # Add a test message
    print("\n3. Adding test message...")
    success = storage.add_message(session_id, "user", "Test message from vladis12345")
    print(f"Add message success: {success}")
    
    # Add bot response
    success2 = storage.add_message(session_id, "assistant", "Test response to vladis12345")
    print(f"Add bot response success: {success2}")
    
    # Check final state
    print("\n4. Final state:")
    all_data = storage._load_all_sessions()
    print(f"Total sessions: {all_data['metadata']['total_sessions']}")
    print(f"Sessions: {list(all_data['sessions'].keys())}")
    
    # Get the session data
    session_data = storage.get_session(session_id)
    if session_data:
        print(f"Session has {session_data['metadata']['total_messages']} messages")
        print(f"Session IP: {session_data['metadata'].get('ip_address', 'None')}")
        for msg in session_data['messages']:
            print(f"  {msg['role']}: {msg['content']}")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_vladis12345_session() 