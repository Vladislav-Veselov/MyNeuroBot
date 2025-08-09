#!/usr/bin/env python3
"""
Test for KB selector functionality in analytics page
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from dialogue_storage import DialogueStorage, reset_dialogue_storage, get_dialogue_storage
from auth import get_current_user_data_dir

def test_kb_selector_functionality():
    """Test that sessions can be filtered by KB"""
    print("Testing KB selector functionality...")
    
    try:
        # Create temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            test_user = "test_user"
            user_data_dir = Path(temp_dir) / "user_data" / test_user
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test knowledge bases
            kb1_dir = user_data_dir / "knowledge_bases" / "kb1"
            kb1_dir.mkdir(parents=True, exist_ok=True)
            
            kb2_dir = user_data_dir / "knowledge_bases" / "kb2"
            kb2_dir.mkdir(parents=True, exist_ok=True)
            
            # Create KB info files
            kb1_info = {
                "name": "Test KB 1",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "document_count": 5
            }
            
            kb2_info = {
                "name": "Test KB 2", 
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "document_count": 3
            }
            
            with open(kb1_dir / "kb_info.json", 'w', encoding='utf-8') as f:
                json.dump(kb1_info, f, ensure_ascii=False, indent=2)
                
            with open(kb2_dir / "kb_info.json", 'w', encoding='utf-8') as f:
                json.dump(kb2_info, f, ensure_ascii=False, indent=2)
            
            # Create dialogue storage with test sessions
            dialogue_file = user_data_dir / "dialogues.json"
            dialogue_storage = DialogueStorage(str(dialogue_file))
            
            # Create test sessions with different KBs
            session1 = dialogue_storage.create_session(
                ip_address="192.168.1.1",
                kb_id="kb1",
                kb_name="Test KB 1"
            )
            
            session2 = dialogue_storage.create_session(
                ip_address="192.168.1.2", 
                kb_id="kb2",
                kb_name="Test KB 2"
            )
            
            session3 = dialogue_storage.create_session(
                ip_address="192.168.1.3",
                kb_id="kb1", 
                kb_name="Test KB 1"
            )
            
            # Add some messages to sessions
            dialogue_storage.add_message(session1, "user", "Hello from KB1")
            dialogue_storage.add_message(session1, "assistant", "Hi there!")
            
            dialogue_storage.add_message(session2, "user", "Hello from KB2")
            dialogue_storage.add_message(session2, "assistant", "Greetings!")
            
            dialogue_storage.add_message(session3, "user", "Another KB1 message")
            dialogue_storage.add_message(session3, "assistant", "Response!")
            
            # Test that all sessions are returned
            all_sessions = dialogue_storage.get_all_sessions()
            assert len(all_sessions) == 3, f"Expected 3 sessions, got {len(all_sessions)}"
            
            # Test filtering by KB1
            kb1_sessions = [s for s in all_sessions if s['kb_id'] == 'kb1']
            assert len(kb1_sessions) == 2, f"Expected 2 KB1 sessions, got {len(kb1_sessions)}"
            
            # Test filtering by KB2  
            kb2_sessions = [s for s in all_sessions if s['kb_id'] == 'kb2']
            assert len(kb2_sessions) == 1, f"Expected 1 KB2 session, got {len(kb2_sessions)}"
            
            # Test that KB names are correctly stored
            for session in all_sessions:
                if session['kb_id'] == 'kb1':
                    assert session['kb_name'] == 'Test KB 1'
                elif session['kb_id'] == 'kb2':
                    assert session['kb_name'] == 'Test KB 2'
            
            print("✅ KB selector functionality test passed!")
            return True
        
    except Exception as e:
        print(f"❌ KB selector functionality test failed: {str(e)}")
        return False

def test_kb_api_endpoint():
    """Test the knowledge bases API endpoint"""
    print("Testing KB API endpoint...")
    
    try:
        with app.test_client() as client:
            # Mock login
            with client.session_transaction() as sess:
                sess['username'] = 'test_user'
            
            # Test getting knowledge bases
            response = client.get('/api/knowledge-bases')
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = json.loads(response.data)
            assert data['success'] == True, "API should return success"
            assert 'knowledge_bases' in data, "Response should contain knowledge_bases"
            
            print("✅ KB API endpoint test passed!")
            return True
            
    except Exception as e:
        print(f"❌ KB API endpoint test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running KB selector tests...")
    
    test1_passed = test_kb_selector_functionality()
    test2_passed = test_kb_api_endpoint()
    
    if test1_passed and test2_passed:
        print("\n🎉 All KB selector tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some KB selector tests failed!")
        sys.exit(1) 