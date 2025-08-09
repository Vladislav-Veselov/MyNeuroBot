#!/usr/bin/env python3
"""
Test script for chatbot status functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_status_manager import chatbot_status_manager
from auth import get_current_user_data_dir

def test_chatbot_status():
    """Test the chatbot status functionality."""
    print("Testing chatbot status functionality...")
    
    # Test initial status (should be running)
    print("\n1. Testing initial status...")
    status = chatbot_status_manager.get_chatbot_status()
    print(f"Initial status: {status}")
    assert not status['stopped'], "Initial status should be running"
    
    # Test stopping chatbots
    print("\n2. Testing stop chatbots...")
    success = chatbot_status_manager.stop_chatbots(message="Test stop message")
    print(f"Stop success: {success}")
    assert success, "Stop should succeed"
    
    # Test status after stop
    status = chatbot_status_manager.get_chatbot_status()
    print(f"Status after stop: {status}")
    assert status['stopped'], "Status should be stopped"
    assert status['message'] == "Test stop message", "Message should match"
    
    # Test is_chatbot_stopped
    is_stopped = chatbot_status_manager.is_chatbot_stopped()
    print(f"Is stopped: {is_stopped}")
    assert is_stopped, "Should be stopped"
    
    # Test get_stop_message
    stop_message = chatbot_status_manager.get_stop_message()
    print(f"Stop message: {stop_message}")
    assert stop_message == "Test stop message", "Stop message should match"
    
    # Test starting chatbots
    print("\n3. Testing start chatbots...")
    success = chatbot_status_manager.start_chatbots()
    print(f"Start success: {success}")
    assert success, "Start should succeed"
    
    # Test status after start
    status = chatbot_status_manager.get_chatbot_status()
    print(f"Status after start: {status}")
    assert not status['stopped'], "Status should be running"
    assert status['message'] is None, "Message should be None"
    
    # Test is_chatbot_stopped after start
    is_stopped = chatbot_status_manager.is_chatbot_stopped()
    print(f"Is stopped after start: {is_stopped}")
    assert not is_stopped, "Should not be stopped"
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_chatbot_status() 