#!/usr/bin/env python3
"""
Test script for old widget functionality - ensures existing widget API still works.
Tests the /public/widget/<widget_id>/chatbot endpoint.
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

class OldWidgetTester:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.temp_dir = None
        self.test_widget_id = "test-old-widget"
        
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
            print(f"Created temp directory: {self.temp_dir}")
            
            # Create user data structure
            user_data_dir = self.temp_dir / "user_data" / "test-tenant"
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
            print("Created knowledge.json")
            
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
            print("Created system_prompt.txt")
            
            # Create kb_info.json
            kb_info_data = {
                "name": "Test Knowledge Base",
                "description": "A test knowledge base for widget testing"
            }
            
            kb_info_file = kb_dir / "kb_info.json"
            with open(kb_info_file, 'w', encoding='utf-8') as f:
                json.dump(kb_info_data, f, ensure_ascii=False, indent=2)
            print("Created kb_info.json")
            
            # Create current_kb.json
            current_kb_data = {
                "current_kb": "default"
            }
            
            current_kb_file = user_data_dir / "current_kb.json"
            with open(current_kb_file, 'w', encoding='utf-8') as f:
                json.dump(current_kb_data, f, ensure_ascii=False, indent=2)
            print("Created current_kb.json")
            
            # Create widget entry in widgets.json
            widgets_file = Path(__file__).parent.parent / "widgets.json"
            if widgets_file.exists():
                with open(widgets_file, 'r', encoding='utf-8') as f:
                    widgets_data = json.load(f)
            else:
                widgets_data = {}
                
            widgets_data[self.test_widget_id] = {
                "tenant_id": "test-tenant",
                "user_data_dir": str(user_data_dir),
                "allowed_origins": ["http://localhost:3000", "http://localhost:5000"]
            }
            
            with open(widgets_file, 'w', encoding='utf-8') as f:
                json.dump(widgets_data, f, ensure_ascii=False, indent=2)
            print("Updated widgets.json")
            
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
                print("Removed temp directory")
                
            # Remove test widget from widgets.json
            widgets_file = Path(__file__).parent.parent / "widgets.json"
            if widgets_file.exists():
                with open(widgets_file, 'r', encoding='utf-8') as f:
                    widgets_data = json.load(f)
                    
                if self.test_widget_id in widgets_data:
                    del widgets_data[self.test_widget_id]
                    
                with open(widgets_file, 'w', encoding='utf-8') as f:
                    json.dump(widgets_data, f, ensure_ascii=False, indent=2)
                print("Removed test widget from widgets.json")
                
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
            
    def test_widget_not_found(self):
        """Test widget not found scenario"""
        print("\n[FIND] Testing Widget Not Found")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/widget/nonexistent-widget/chatbot",
                json={"message": "Hello"}
            )
            
            if response.status_code == 404:
                data = response.json()
                if data.get("success") == False and "Widget not found" in data.get("error", ""):
                    self.log_test("Widget Not Found", True, "Correct error response")
                    return True
                else:
                    self.log_test("Widget Not Found", False, "Incorrect error response format")
                    return False
            else:
                self.log_test("Widget Not Found", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Widget Not Found", False, f"Error: {str(e)}")
            return False
            
    def test_empty_message(self):
        """Test empty message validation"""
        print("\n[BREV] Testing Empty Message Validation")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/widget/{self.test_widget_id}/chatbot",
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
            
    def test_basic_chat(self):
        """Test basic chat functionality"""
        print("\n[CHAT] Testing Basic Chat")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/widget/{self.test_widget_id}/chatbot",
                json={"message": "What is the capital of France?"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") == True and "response" in data and "session_id" in data:
                    self.log_test("Basic Chat", True, f"Response received: {data['response'][:50]}...")
                    return True
                else:
                    self.log_test("Basic Chat", False, "Incorrect response format")
                    return False
            else:
                self.log_test("Basic Chat", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Basic Chat", False, f"Error: {str(e)}")
            return False
            
    def test_session_management(self):
        """Test session management"""
        print("\n[SESS] Testing Session Management")
        print("-" * 40)
        
        try:
            # First message to create session
            response1 = self.session.post(
                f"{self.base_url}/public/widget/{self.test_widget_id}/chatbot",
                json={"message": "Hello"}
            )
            
            if response1.status_code != 200:
                self.log_test("Session Management", False, f"First request failed: {response1.status_code}")
                return False
                
            data1 = response1.json()
            session_id1 = data1.get("session_id")
            
            # Second message with same session
            response2 = self.session.post(
                f"{self.base_url}/public/widget/{self.test_widget_id}/chatbot",
                json={"message": "How are you?", "session_id": session_id1}
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                session_id2 = data2.get("session_id")
                
                if session_id1 == session_id2:
                    self.log_test("Session Management", True, "Session maintained across requests")
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
        """Test __RESET__ command"""
        print("\n[SESS] Testing Reset Command")
        print("-" * 40)
        
        try:
            response = self.session.post(
                f"{self.base_url}/public/widget/{self.test_widget_id}/chatbot",
                json={"message": "__RESET__"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("success") == True and 
                    "Switched to default knowledge base" in data.get("response", "") and
                    "session_id" in data):
                    self.log_test("Reset Command", True, "Reset successful")
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
        print("Testing Old Widget Functionality")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_environment():
            print("[FAIL] Failed to setup test environment")
            return False
            
        try:
            # Run tests
            tests = [
                self.test_server_connection,
                self.test_widget_not_found,
                self.test_empty_message,
                self.test_basic_chat,
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
                print("[SUCCESS] All tests passed! Old widget functionality is working correctly.")
                return True
            else:
                print("[WARN]  Some tests failed. Please check the implementation.")
                return False
                
        finally:
            self.cleanup_test_environment()

def main():
    """Main function"""
    tester = OldWidgetTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
