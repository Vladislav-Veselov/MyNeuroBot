#!/usr/bin/env python3
"""
Test script for dialogue storage functionality.
"""

import json
from dialogue_storage import dialogue_storage
from chatbot_service import chatbot_service

def test_dialogue_storage():
    """Test the dialogue storage functionality."""
    print("Testing dialogue storage...")
    
    # Test 1: Create a new session
    print("\n1. Creating new session...")
    session_id = dialogue_storage.create_session()
    print(f"Created session: {session_id}")
    
    # Test 2: Add messages to the session
    print("\n2. Adding messages to session...")
    messages = [
        ("user", "Привет! Как дела?"),
        ("assistant", "Привет! У меня все хорошо, спасибо! Как я могу вам помочь?"),
        ("user", "Расскажи мне о NeuroBot"),
        ("assistant", "NeuroBot - это умный помощник, который отвечает на вопросы на основе базы знаний.")
    ]
    
    for role, content in messages:
        success = dialogue_storage.add_message(session_id, role, content)
        print(f"Added {role} message: {success}")
    
    # Test 3: Get the session
    print("\n3. Retrieving session...")
    session_data = dialogue_storage.get_session(session_id)
    if session_data:
        print(f"Session has {session_data['metadata']['total_messages']} messages")
        for msg in session_data['messages']:
            print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    # Test 4: Get all sessions
    print("\n4. Getting all sessions...")
    all_sessions = dialogue_storage.get_all_sessions()
    print(f"Found {len(all_sessions)} sessions")
    for session in all_sessions:
        print(f"  Session {session['session_id'][:8]}... - {session['total_messages']} messages")
    
    # Test 5: Get storage statistics
    print("\n5. Getting storage statistics...")
    stats = dialogue_storage.get_storage_stats()
    print(f"Storage stats: {stats}")
    
    # Test 6: Test chatbot integration
    print("\n6. Testing chatbot integration...")
    chatbot_service.start_new_session()
    response = chatbot_service.generate_response("Привет!")
    print(f"Chatbot response: {response[:100]}...")
    
    current_session = chatbot_service.get_current_session_id()
    print(f"Current session ID: {current_session}")
    
    # Test 7: Get the chatbot session
    print("\n7. Retrieving chatbot session...")
    chatbot_session_data = dialogue_storage.get_session(current_session)
    if chatbot_session_data:
        print(f"Chatbot session has {chatbot_session_data['metadata']['total_messages']} messages")
        for msg in chatbot_session_data['messages']:
            print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    # Test 8: Get updated statistics
    print("\n8. Getting updated storage statistics...")
    updated_stats = dialogue_storage.get_storage_stats()
    print(f"Updated stats: {updated_stats}")
    
    print("\nDialogue storage test completed!")

if __name__ == "__main__":
    test_dialogue_storage() 