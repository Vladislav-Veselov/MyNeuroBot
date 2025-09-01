#!/usr/bin/env python3
"""
Test script for custom widget functionality - tests the new persona-sliders feature.
Tests the /public/custom-widget/<widget_id>/chatbot endpoint with tone/humor/brevity parameters.
"""

import requests
import json
import time
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add Backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class CustomWidgetTester:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.temp_dir = None
        self.test_widget_id = "test-custom-widget"
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "PASS" if success else "FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def setup_test_environment(self):
        """Create temporary test environment with widget and knowledge base"""
        print("Setting up test environment")
        print("-" * 40)
        
        try:
            # Create temporary directory
            self.temp_dir = Path(tempfile.mkdtemp())
            print(f"[OK] Created temp directory: {self.temp_dir}")
            
            # Create user data structure
            user_data_dir = self.temp_dir / "user_data" / "test-custom-tenant"
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create knowledge base
            kb_dir = user_data_dir / "knowledge_bases" / "default"
            kb_dir.mkdir(parents=True, exist_ok=True)
            
            # Create knowledge.json
            knowledge_data = [
                {
                    "question": "What is the capital of France?",
                    "answer": "The capital of France is Paris."
                },
                {
                    "question": "How do you say hello in French?",
                    "answer": "Hello in French is 'Bonjour'."
                }
            ]
            
            knowledge_file = kb_dir / "knowledge.json"
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, ensure_ascii=False, indent=2)
            print("[OK] Created knowledge.json")
            
            # Create system_prompt.txt with persona settings
            system_prompt_data = {
                "tone": 2,
                "humor": 1,
                "brevity": 3,
                "additional_prompt": "You are a helpful assistant."
            }
            
            system_prompt_file = kb_dir / "system_prompt.txt"
            with open(system_prompt_file, 'w', encoding='utf-8') as f:
                json.dump(system_prompt_data, f, ensure_ascii=False, indent=2)
            print("[OK] Created system_prompt.txt")
            
            # Create kb_info.json
            kb_info_data = {
                "name": "Test Knowledge Base",
                "description": "A test knowledge base for custom widget testing"
            }
            
            kb_info_file = kb_dir / "kb_info.json"
            with open(kb_info_file, 'w', encoding='utf-8') as f:
                json.dump(kb_info_data, f, ensure_ascii=False, indent=2)
            print("[OK] Created kb_info.json")
            
            # Create current_kb.json
            current_kb_data = {
                "current_kb": "default"
            }
            
            current_kb_file = user_data_dir / "current_kb.json"
            with open(current_kb_file, 'w', encoding='utf-8') as f:
                json.dump(current_kb_data, f, ensure_ascii=False, indent=2)
            print("[OK] Created current_kb.json")
            
            # Create widget entry in widgets.json
            widgets_file = Path(__file__).parent.parent / "widgets.json"
            if widgets_file.exists():
                with open(widgets_file, 'r', encoding='utf-8') as f:
                    widgets_data = json.load(f)
            else:
                widgets_data = {}
                
            widgets_data[self.test_widget_id] = {
                "tenant_id": "test-custom-tenant",
                "user_data_dir": str(user_data_dir),
                "allowed_origins": ["http://localhost:3000", "http://localhost:5000"]
            }
            
            with open(widgets_file, 'w', encoding='utf-8') as f:
                json.dump(widgets_data, f, ensure_ascii=False, indent=2)
            print("[OK] Updated widgets.json")
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Failed to setup test environment: {e}")
            return False
            
    def cleanup_test_environment(self):
        """Clean up temporary test environment"""
        print("\n[CLEAN] Cleaning up test environment")
        print("-" * 40)
        
        try:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("[OK] Removed temp directory")
                
            # Remove test widget from widgets.json
            widgets_file = Path(__file__).parent.parent / "widgets.json"
            if widgets_file.exists():
                with open(widgets_file, 'r', encoding='utf-8') as f:
                    widgets_data = json.load(f)
                    
                if self.test_widget_id in widgets_data:
                    del widgets_data[self.test_widget_id]
                    
                with open(widgets_file, 'w', encoding='utf-8') as f:
                    json.dump(widgets_data, f, ensure_ascii=False, indent=2)
                print("[OK] Removed test widget from widgets.json")
                
        except Exception as e:
            print(f"[WARN]  Warning: cleanup failed: {e}")
            
    def test_server_connection(self):
        """Test if server is running"""
        print("\n[CONN] Testing Server Connection")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test("Server Connection", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("Server Connection", False, f"Status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Server Connection", False, "Cannot connect to server")
            return False
        except Exception as e:
            self.log_test("Server Connection", False, f"Error: {str(e)}")
            return False
            
    def test_custom_widget_not_found(self):
        """Test custom widget not found scenario"""
        print("\n[FIND] Testing Custom Widget Not Found")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/nonexistent-widget/chatbot",
                json={"message": "Hello"}
            )
            
            if response.status_code == 404:
                data = response.json()
                if data.get("success") == False and "Widget not found" in data.get("error", ""):
                    self.log_test("Custom Widget Not Found", True, "Correct error response")
                    return True
                else:
                    self.log_test("Custom Widget Not Found", False, "Incorrect error response format")
                    return False
            else:
                self.log_test("Custom Widget Not Found", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Custom Widget Not Found", False, f"Error: {str(e)}")
            return False
            
    def test_empty_message(self):
        """Test empty message validation"""
        print("\n[BREV] Testing Empty Message Validation")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={"message": ""}
            )
            
            if response.status_code == 400:
                data = response.json()
                if data.get("success") == False and "Message cannot be empty" in data.get("error", ""):
                    self.log_test("Empty Message Validation", True, "Correct validation response")
                    return True
                else:
                    self.log_test("Empty Message Validation", False, "Incorrect validation response format")
                    return False
            else:
                self.log_test("Empty Message Validation", False, f"Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Empty Message Validation", False, f"Error: {str(e)}")
            return False
            
    def test_basic_chat_no_sliders(self):
        """Test basic chat functionality without persona sliders"""
        print("\n[CHAT] Testing Basic Chat (No Sliders)")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={"message": "What is the capital of France?"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data and "session_id" in data:
                    self.log_test("Basic Chat (No Sliders)", True, f"Response received: {data['response'][:50]}...")
                    return True
                else:
                    self.log_test("Basic Chat (No Sliders)", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Basic Chat (No Sliders)", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Basic Chat (No Sliders)", False, f"Error: {str(e)}")
            return False
            
    def test_tone_override(self):
        """Test tone slider override"""
        print("\n[TONE] Testing Tone Override")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={
                    "message": "Tell me a joke",
                    "tone": 4  # Very casual
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data:
                    self.log_test("Tone Override", True, f"Response with tone=4 received: {data['response'][:50]}...")
                    return True
                else:
                    self.log_test("Tone Override", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Tone Override", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Tone Override", False, f"Error: {str(e)}")
            return False
            
    def test_humor_override(self):
        """Test humor slider override"""
        print("\n[HUMOR] Testing Humor Override")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={
                    "message": "Tell me a joke",
                    "humor": 4  # Very humorous
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data:
                    self.log_test("Humor Override", True, f"Response with humor=4 received: {data['response'][:50]}...")
                    return True
                else:
                    self.log_test("Humor Override", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Humor Override", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Humor Override", False, f"Error: {str(e)}")
            return False
            
    def test_brevity_override(self):
        """Test brevity slider override"""
        print("\n[BREV] Testing Brevity Override")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={
                    "message": "What is the capital of France?",
                    "brevity": 4  # Very brief
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data:
                    self.log_test("Brevity Override", True, f"Response with brevity=4 received: {data['response'][:50]}...")
                    return True
                else:
                    self.log_test("Brevity Override", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Brevity Override", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Brevity Override", False, f"Error: {str(e)}")
            return False
            
    def test_multiple_sliders(self):
        """Test multiple slider overrides"""
        print("\n[MULTI] Testing Multiple Sliders")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={
                    "message": "Tell me about France",
                    "tone": 0,    # Very formal
                    "humor": 4,   # Very humorous
                    "brevity": 1  # Very detailed
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data:
                    self.log_test("Multiple Sliders", True, f"Response with multiple overrides received: {data['response'][:50]}...")
                    return True
                else:
                    self.log_test("Multiple Sliders", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Multiple Sliders", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Multiple Sliders", False, f"Error: {str(e)}")
            return False
            
    def test_invalid_slider_values(self):
        """Test invalid slider value handling"""
        print("\n[WARN] Testing Invalid Slider Values")
        print("-" * 40)
        
        try:
            # Test values outside 0-4 range
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={
                    "message": "Hello",
                    "tone": 10,   # Invalid: too high
                    "humor": -5,  # Invalid: too low
                    "brevity": "invalid"  # Invalid: not a number
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data:
                    self.log_test("Invalid Slider Values", True, "Invalid values were handled gracefully")
                    return True
                else:
                    self.log_test("Invalid Slider Values", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Invalid Slider Values", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invalid Slider Values", False, f"Error: {str(e)}")
            return False
            
    def test_session_management(self):
        """Test session management with custom widget"""
        print("\n[SESS] Testing Session Management")
        print("-" * 40)
        
        try:
            # First message to create session
            response1 = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={"message": "Hello", "tone": 2}
            )
            
            if response1.status_code != 200:
                self.log_test("Session Management", False, f"First request failed: {response1.status_code}")
                return False
                
            data1 = response1.json()
            session_id1 = data1.get("session_id")
            
            # Second message with same session but different sliders
            response2 = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={
                    "message": "How are you?", 
                    "session_id": session_id1,
                    "tone": 4,
                    "humor": 1
                }
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                session_id2 = data2.get("session_id")
                
                if session_id1 == session_id2:
                    self.log_test("Session Management", True, "Session maintained across requests with different sliders")
                    return True
                else:
                    self.log_test("Session Management", False, "Session ID changed unexpectedly")
                    return False
            else:
                self.log_test("Session Management", False, f"Second request failed: {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Session Management", False, f"Error: {str(e)}")
            return False
            
    def test_reset_command(self):
        """Test __RESET__ command with custom widget"""
        print("\n[SESS] Testing Reset Command")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/custom-widget/{self.test_widget_id}/chatbot",
                json={"message": "__RESET__", "tone": 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("success") == True and 
                    "Switched to default knowledge base" in data.get("response", "") and
                    "session_id" in data):
                    self.log_test("Reset Command", True, "Reset successful with custom widget")
                    return True
                else:
                    self.log_test("Reset Command", False, "Incorrect reset response format")
                    return False
            else:
                self.log_test("Reset Command", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Reset Command", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all tests"""
        print("Testing Custom Widget Functionality")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_environment():
            print("[FAIL] Failed to setup test environment")
            return False
            
        try:
            # Run tests
            tests = [
                self.test_server_connection,
                self.test_custom_widget_not_found,
                self.test_empty_message,
                self.test_basic_chat_no_sliders,
                self.test_tone_override,
                self.test_humor_override,
                self.test_brevity_override,
                self.test_multiple_sliders,
                self.test_invalid_slider_values,
                self.test_session_management,
                self.test_reset_command
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if test():
                    passed += 1
                    
            # Summary
            print(f"\n[STATS] Test Summary")
            print("-" * 40)
            print(f"Passed: {passed}/{total}")
            print(f"Failed: {total - passed}/{total}")
            
            success_rate = (passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
            
            if passed == total:
                print("[SUCCESS] All tests passed! Custom widget functionality is working correctly.")
                return True
            else:
                print("[WARN]  Some tests failed. Please check the implementation.")
                return False
                
        finally:
            self.cleanup_test_environment()

def main():
    """Main function"""
    tester = CustomWidgetTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
