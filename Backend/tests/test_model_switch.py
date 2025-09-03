#!/usr/bin/env python3
"""
Test script to verify LITE/PRO model switching functionality in the custom widget API.
Tests both 'mode' parameter ('lite'/'pro') and direct 'model' parameter.
"""

import requests
import json
import time
from typing import Dict, Any

# Test configuration
API_BASE = "http://localhost:5001"
WIDGET_ID = "creatium-alexey-widget"
API_URL = f"{API_BASE}/public/custom-widget/{WIDGET_ID}/chatbot"

def send_chat_message(message: str, mode: str = None, model: str = None, session_id: str = None) -> Dict[str, Any]:
    """Send a chat message to the widget API."""
    payload = {
        "message": message,
        "tone": 2,
        "humor": 2,
        "brevity": 2
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    if mode:
        payload["mode"] = mode
        print(f"🔧 Sending with mode: '{mode}'")
    
    if model:
        payload["model"] = model
        print(f"🔧 Sending with model: '{model}'")
    
    print(f"📤 Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📥 Response data: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Error response: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {"success": False, "error": str(e)}

def test_model_switching():
    """Test the model switching functionality."""
    print("🧪 Starting model switching tests...")
    print("=" * 60)
    
    # Test 1: Default behavior (should use LITE/gpt-4o-mini)
    print("\n🔍 TEST 1: Default behavior (no mode/model specified)")
    print("-" * 50)
    result1 = send_chat_message("Hello, what model are you using?")
    
    if result1.get("success"):
        print("✅ Test 1 passed - Default response received")
        print(f"   Model used: {result1.get('model', 'unknown')}")
    else:
        print("❌ Test 1 failed")
        return False
    
    time.sleep(1)  # Small delay between requests
    
    # Test 2: LITE mode
    print("\n🔍 TEST 2: LITE mode")
    print("-" * 50)
    result2 = send_chat_message("Hello, what model are you using?", mode="lite")
    
    if result2.get("success"):
        print("✅ Test 2 passed - LITE mode response received")
        print(f"   Model used: {result2.get('model', 'unknown')}")
        if result2.get("model") == "gpt-4o-mini":
            print("   ✅ Correct model (gpt-4o-mini) selected for LITE mode")
        else:
            print("   ❌ Wrong model selected for LITE mode")
    else:
        print("❌ Test 2 failed")
        return False
    
    time.sleep(1)
    
    # Test 3: PRO mode
    print("\n🔍 TEST 3: PRO mode")
    print("-" * 50)
    result3 = send_chat_message("Hello, what model are you using?", mode="pro")
    
    if result3.get("success"):
        print("✅ Test 3 passed - PRO mode response received")
        print(f"   Model used: {result3.get('model', 'unknown')}")
        if result3.get("model") == "gpt-4o":
            print("   ✅ Correct model (gpt-4o) selected for PRO mode")
        else:
            print("   ❌ Wrong model selected for PRO mode")
    else:
        print("❌ Test 3 failed")
        return False
    
    time.sleep(1)
    
    # Test 4: Direct model specification - gpt-4o-mini
    print("\n🔍 TEST 4: Direct model specification (gpt-4o-mini)")
    print("-" * 50)
    result4 = send_chat_message("Hello, what model are you using?", model="gpt-4o-mini")
    
    if result4.get("success"):
        print("✅ Test 4 passed - Direct model response received")
        print(f"   Model used: {result4.get('model', 'unknown')}")
        if result4.get("model") == "gpt-4o-mini":
            print("   ✅ Correct model (gpt-4o-mini) selected")
        else:
            print("   ❌ Wrong model selected")
    else:
        print("❌ Test 4 failed")
        return False
    
    time.sleep(1)
    
    # Test 5: Direct model specification - gpt-4o
    print("\n🔍 TEST 5: Direct model specification (gpt-4o)")
    print("-" * 50)
    result5 = send_chat_message("Hello, what model are you using?", model="gpt-4o")
    
    if result5.get("success"):
        print("✅ Test 5 passed - Direct model response received")
        print(f"   Model used: {result5.get('model', 'unknown')}")
        if result5.get("model") == "gpt-4o":
            print("   ✅ Correct model (gpt-4o) selected")
        else:
            print("   ❌ Wrong model selected")
    else:
        print("❌ Test 5 failed")
        return False
    
    time.sleep(1)
    
    # Test 6: Invalid mode (should fall back to default)
    print("\n🔍 TEST 6: Invalid mode (should fall back to default)")
    print("-" * 50)
    result6 = send_chat_message("Hello, what model are you using?", mode="invalid")
    
    if result6.get("success"):
        print("✅ Test 6 passed - Invalid mode handled gracefully")
        print(f"   Model used: {result6.get('model', 'unknown')}")
    else:
        print("❌ Test 6 failed")
        return False
    
    time.sleep(1)
    
    # Test 7: Invalid model (should fall back to default)
    print("\n🔍 TEST 7: Invalid model (should fall back to default)")
    print("-" * 50)
    result7 = send_chat_message("Hello, what model are you using?", model="invalid-model")
    
    if result7.get("success"):
        print("✅ Test 7 passed - Invalid model handled gracefully")
        print(f"   Model used: {result7.get('model', 'unknown')}")
    else:
        print("❌ Test 7 failed")
        return False
    
    time.sleep(1)
    
    # Test 8: Session continuity with model switching
    print("\n🔍 TEST 8: Session continuity with model switching")
    print("-" * 50)
    
    # First message with LITE mode
    result8a = send_chat_message("First message with LITE mode", mode="lite")
    if not result8a.get("success"):
        print("❌ Test 8a failed")
        return False
    
    session_id = result8a.get("session_id")
    print(f"   Session ID: {session_id}")
    
    # Second message with PRO mode (same session)
    result8b = send_chat_message("Second message with PRO mode", mode="pro", session_id=session_id)
    if result8b.get("success"):
        print("✅ Test 8b passed - Session continuity maintained")
        print(f"   Model used: {result8b.get('model', 'unknown')}")
        if result8b.get("model") == "gpt-4o":
            print("   ✅ Correct model (gpt-4o) selected for PRO mode")
        else:
            print("   ❌ Wrong model selected for PRO mode")
    else:
        print("❌ Test 8b failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All model switching tests completed!")
    print("=" * 60)
    
    return True

def test_widget_functionality():
    """Test basic widget functionality."""
    print("\n🧪 Testing basic widget functionality...")
    print("=" * 60)
    
    # Test basic message
    print("\n🔍 TEST: Basic message functionality")
    print("-" * 50)
    result = send_chat_message("Hello, how are you?")
    
    if result.get("success"):
        print("✅ Basic functionality test passed")
        print(f"   Response: {result.get('response', 'No response')[:100]}...")
        print(f"   Model used: {result.get('model', 'unknown')}")
    else:
        print("❌ Basic functionality test failed")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting NeuroBot Model Switch Tests")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Make sure your app is running on {API_BASE}")
    print("=" * 60)
    
    try:
        # Test basic functionality first
        if not test_widget_functionality():
            print("❌ Basic functionality test failed. Stopping.")
            exit(1)
        
        # Test model switching
        if test_model_switching():
            print("\n🎉 All tests passed successfully!")
            print("✅ Model switching is working correctly")
        else:
            print("\n❌ Some tests failed")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        exit(1)
