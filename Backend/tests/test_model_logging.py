#!/usr/bin/env python3
"""
Quick test to see the model selection logging in the chatbot service.
"""

import requests
import json

# Test configuration
API_BASE = "http://localhost:5001"
WIDGET_ID = "creatium-alexey-widget"
API_URL = f"{API_BASE}/public/custom-widget/{WIDGET_ID}/chatbot"

def test_model_logging():
    """Test to see model selection logging."""
    print("🔍 Testing model selection logging...")
    print("=" * 50)
    
    # Test LITE mode
    print("\n📤 Testing LITE mode...")
    payload = {
        "message": "Tell me about yourself",
        "mode": "lite",
        "tone": 2,
        "humor": 2,
        "brevity": 2
    }
    
    response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ LITE mode response received")
        print(f"   Model used: {data.get('model', 'unknown')}")
        print(f"   Response: {data.get('response', 'No response')[:100]}...")
    else:
        print(f"❌ LITE mode failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("📋 Check your server logs for:")
    print("   🤖 MODEL SELECTED: gpt-4o-mini")
    print("   📝 USER MESSAGE: Tell me about yourself")
    print("=" * 50)
    
    # Test PRO mode
    print("\n📤 Testing PRO mode...")
    payload = {
        "message": "Tell me about yourself",
        "mode": "pro",
        "tone": 2,
        "humor": 2,
        "brevity": 2
    }
    
    response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PRO mode response received")
        print(f"   Model used: {data.get('model', 'unknown')}")
        print(f"   Response: {data.get('response', 'No response')[:100]}...")
    else:
        print(f"❌ PRO mode failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("📋 Check your server logs for:")
    print("   🤖 MODEL SELECTED: gpt-4o")
    print("   📝 USER MESSAGE: Tell me about yourself")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Testing Model Selection Logging")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print("Make sure your app is running on http://localhost:5001")
    print("=" * 50)
    
    test_model_logging()
