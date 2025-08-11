#!/usr/bin/env python3
"""
Test script for standalone chatbot service.
"""

try:
    print("Testing standalone chatbot service import...")
    from standalone_chatbot_service import standalone_chatbot_service
    print("✓ Service imported successfully")
    
    print("\nTesting basic functionality...")
    
    # Test getting user data directory
    try:
        user_dir = standalone_chatbot_service.get_user_data_directory("alexey123")
        print(f"✓ User data directory: {user_dir}")
    except Exception as e:
        print(f"✗ Error getting user data directory: {e}")
    
    # Test getting current KB ID
    try:
        kb_id = standalone_chatbot_service.get_current_kb_id("alexey123")
        print(f"✓ Current KB ID: {kb_id}")
    except Exception as e:
        print(f"✗ Error getting current KB ID: {e}")
    
    # Test getting settings
    try:
        settings = standalone_chatbot_service.get_settings("alexey123")
        print(f"✓ Settings: {settings}")
    except Exception as e:
        print(f"✗ Error getting settings: {e}")
    
    # Test session creation
    try:
        session_id = standalone_chatbot_service.get_or_create_session("alexey123")
        print(f"✓ Session ID: {session_id}")
    except Exception as e:
        print(f"✗ Error creating session: {e}")
    
    print("\n✓ All tests completed!")
    
except Exception as e:
    print(f"✗ Error importing service: {e}")
    import traceback
    traceback.print_exc()
