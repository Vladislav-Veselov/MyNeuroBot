import requests
import json

def test_chatbot_api():
    """Test the chatbot API endpoint."""
    url = "http://localhost:5001/api/chatbot"
    
    # Test message
    test_message = "Привет! Как дела?"
    
    payload = {
        "message": test_message
    }
    
    try:
        print(f"Sending test message: {test_message}")
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Chatbot response: {data.get('response')}")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on port 5001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_clear_chat():
    """Test the clear chat API endpoint."""
    url = "http://localhost:5001/api/chatbot/clear"
    
    try:
        print("Testing clear chat functionality...")
        response = requests.post(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Chat history cleared successfully")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on port 5001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing Chatbot API...")
    print("=" * 50)
    
    test_chatbot_api()
    print("\n" + "=" * 50)
    test_clear_chat() 