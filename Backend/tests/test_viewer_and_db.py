#!/usr/bin/env python3
"""
Comprehensive test script for NeuroBot viewer and database functionality.
Tests both the knowledge base viewer and dialogue storage systems.
"""

import requests
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add the Backend directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent))

from dialogue_storage import DialogueStorage
from chatbot_service import ChatbotService

class NeuroBotTester:
    def __init__(self, base_url: str = "http://localhost:5001"):
        """
        Initialize the tester.
        
        Args:
            base_url: Base URL of the Flask application
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
        # Initialize storage for testing
        self.dialogue_storage = DialogueStorage("test_dialogues.json")
        self.chatbot_service = ChatbotService()
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        print()

    def test_server_connection(self) -> bool:
        """Test if the Flask server is running."""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def test_viewer_endpoints(self):
        """Test all viewer-related API endpoints."""
        print("=" * 60)
        print("TESTING VIEWER FUNCTIONALITY")
        print("=" * 60)
        
        # Test 1: Get documents (basic)
        try:
            response = self.session.get(f"{self.base_url}/api/documents")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Get Documents (Basic)",
                success,
                f"Status: {response.status_code}, Documents: {len(data.get('documents', []))}"
            )
        except Exception as e:
            self.log_test("Get Documents (Basic)", False, f"Exception: {str(e)}")

        # Test 2: Get documents with pagination
        try:
            response = self.session.get(f"{self.base_url}/api/documents?page=1&search=")
            success = response.status_code == 200
            data = response.json() if success else {}
            pagination = data.get('pagination', {})
            self.log_test(
                "Get Documents (Pagination)",
                success,
                f"Page: {pagination.get('current_page', 'N/A')}, "
                f"Total: {pagination.get('total_pages', 'N/A')}, "
                f"Items: {pagination.get('total_documents', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Get Documents (Pagination)", False, f"Exception: {str(e)}")

        # Test 3: Search documents
        try:
            response = self.session.get(f"{self.base_url}/api/documents?search=test")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Search Documents",
                success,
                f"Found {len(data.get('documents', []))} documents"
            )
        except Exception as e:
            self.log_test("Search Documents", False, f"Exception: {str(e)}")

        # Test 4: Get specific document
        try:
            response = self.session.get(f"{self.base_url}/api/document/0")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Get Specific Document",
                success,
                f"Document ID: 0, Question: {data.get('question', 'N/A')[:50]}..."
            )
        except Exception as e:
            self.log_test("Get Specific Document", False, f"Exception: {str(e)}")

        # Test 5: Get statistics
        try:
            response = self.session.get(f"{self.base_url}/api/stats")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Get Statistics",
                success,
                f"Total docs: {data.get('total_documents', 'N/A')}, "
                f"Avg Q length: {data.get('average_question_length', 'N/A'):.1f}, "
                f"Avg A length: {data.get('average_answer_length', 'N/A'):.1f}"
            )
        except Exception as e:
            self.log_test("Get Statistics", False, f"Exception: {str(e)}")

        # Test 6: Add new Q&A
        test_qa = {
            "question": "Test question for automated testing?",
            "answer": "This is a test answer created by the automated test script."
        }
        try:
            response = self.session.post(
                f"{self.base_url}/api/add_qa",
                json=test_qa,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Add New Q&A",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Add New Q&A", False, f"Exception: {str(e)}")

        # Test 7: Update document
        try:
            update_data = {
                "question": "Updated test question?",
                "answer": "This is an updated test answer."
            }
            response = self.session.put(
                f"{self.base_url}/api/document/0",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Update Document",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Update Document", False, f"Exception: {str(e)}")

        # Test 8: Semantic search
        try:
            response = self.session.get(f"{self.base_url}/api/semantic_search?query=test")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Semantic Search",
                success,
                f"Found {len(data.get('documents', []))} relevant documents"
            )
        except Exception as e:
            self.log_test("Semantic Search", False, f"Exception: {str(e)}")

    def test_database_functionality(self):
        """Test dialogue storage and database functionality."""
        print("=" * 60)
        print("TESTING DATABASE FUNCTIONALITY")
        print("=" * 60)
        
        # Test 1: Create new session
        try:
            session_id = self.dialogue_storage.create_session()
            success = bool(session_id)
            self.log_test(
                "Create New Session",
                success,
                f"Session ID: {session_id[:8]}..."
            )
        except Exception as e:
            self.log_test("Create New Session", False, f"Exception: {str(e)}")

        # Test 2: Add messages to session
        try:
            messages = [
                ("user", "Hello, this is a test message"),
                ("assistant", "Hello! I'm here to help you with your questions."),
                ("user", "What is NeuroBot?"),
                ("assistant", "NeuroBot is an intelligent chatbot with RAG capabilities.")
            ]
            
            success_count = 0
            for role, content in messages:
                success = self.dialogue_storage.add_message(session_id, role, content)
                if success:
                    success_count += 1
            
            self.log_test(
                "Add Messages to Session",
                success_count == len(messages),
                f"Added {success_count}/{len(messages)} messages successfully"
            )
        except Exception as e:
            self.log_test("Add Messages to Session", False, f"Exception: {str(e)}")

        # Test 3: Get session data
        try:
            session_data = self.dialogue_storage.get_session(session_id)
            success = session_data is not None
            message_count = len(session_data.get('messages', [])) if session_data else 0
            self.log_test(
                "Get Session Data",
                success,
                f"Session has {message_count} messages"
            )
        except Exception as e:
            self.log_test("Get Session Data", False, f"Exception: {str(e)}")

        # Test 4: Get all sessions
        try:
            all_sessions = self.dialogue_storage.get_all_sessions()
            success = isinstance(all_sessions, list)
            self.log_test(
                "Get All Sessions",
                success,
                f"Found {len(all_sessions)} sessions"
            )
        except Exception as e:
            self.log_test("Get All Sessions", False, f"Exception: {str(e)}")

        # Test 5: Get storage statistics
        try:
            stats = self.dialogue_storage.get_storage_stats()
            success = isinstance(stats, dict)
            self.log_test(
                "Get Storage Statistics",
                success,
                f"Total sessions: {stats.get('total_sessions', 'N/A')}, "
                f"Total messages: {stats.get('total_messages', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Get Storage Statistics", False, f"Exception: {str(e)}")

        # Test 6: Mark session as read
        try:
            success = self.dialogue_storage.mark_session_as_read(session_id)
            self.log_test(
                "Mark Session as Read",
                success,
                "Session marked as read successfully"
            )
        except Exception as e:
            self.log_test("Mark Session as Read", False, f"Exception: {str(e)}")

        # Test 7: Delete session
        try:
            success = self.dialogue_storage.delete_session(session_id)
            self.log_test(
                "Delete Session",
                success,
                "Session deleted successfully"
            )
        except Exception as e:
            self.log_test("Delete Session", False, f"Exception: {str(e)}")

    def test_chatbot_api(self):
        """Test chatbot API endpoints."""
        print("=" * 60)
        print("TESTING CHATBOT API")
        print("=" * 60)
        
        # Test 1: Send message to chatbot
        try:
            payload = {"message": "Hello, this is a test message"}
            response = self.session.post(
                f"{self.base_url}/api/chatbot",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Send Chatbot Message",
                success,
                f"Status: {response.status_code}, Response: {data.get('response', 'N/A')[:50]}..."
            )
        except Exception as e:
            self.log_test("Send Chatbot Message", False, f"Exception: {str(e)}")

        # Test 2: Clear chatbot history
        try:
            response = self.session.post(f"{self.base_url}/api/chatbot/clear")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Clear Chatbot History",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Clear Chatbot History", False, f"Exception: {str(e)}")

        # Test 3: Start new session
        try:
            response = self.session.post(f"{self.base_url}/api/chatbot/new-session")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Start New Session",
                success,
                f"Status: {response.status_code}, Session ID: {data.get('session_id', 'N/A')[:8]}..."
            )
        except Exception as e:
            self.log_test("Start New Session", False, f"Exception: {str(e)}")

        # Test 4: Get dialogues
        try:
            response = self.session.get(f"{self.base_url}/api/dialogues")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Get Dialogues",
                success,
                f"Status: {response.status_code}, Found {len(data.get('dialogues', []))} dialogues"
            )
        except Exception as e:
            self.log_test("Get Dialogues", False, f"Exception: {str(e)}")

        # Test 5: Get dialogue statistics
        try:
            response = self.session.get(f"{self.base_url}/api/dialogues/stats")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Get Dialogue Statistics",
                success,
                f"Status: {response.status_code}, Total sessions: {data.get('total_sessions', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Get Dialogue Statistics", False, f"Exception: {str(e)}")

    def test_settings_api(self):
        """Test settings API endpoints."""
        print("=" * 60)
        print("TESTING SETTINGS API")
        print("=" * 60)
        
        # Test 1: Get settings
        try:
            response = self.session.get(f"{self.base_url}/api/get_settings")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Get Settings",
                success,
                f"Status: {response.status_code}, Tone: {data.get('tone', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Get Settings", False, f"Exception: {str(e)}")

        # Test 2: Save settings
        try:
            test_settings = {
                "tone": "friendly",
                "humor": 2,
                "brevity": 3,
                "additional_prompt": "Test additional prompt"
            }
            response = self.session.post(
                f"{self.base_url}/api/save_settings",
                json=test_settings,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Save Settings",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}"
            )
        except Exception as e:
            self.log_test("Save Settings", False, f"Exception: {str(e)}")

    def test_frontend_pages(self):
        """Test frontend page accessibility."""
        print("=" * 60)
        print("TESTING FRONTEND PAGES")
        print("=" * 60)
        
        pages = [
            ("/", "Home/Viewer"),
            ("/viewer", "Viewer"),
            ("/chatbot", "Chatbot"),
            ("/settings", "Settings"),
            ("/analytics", "Analytics"),
            ("/about", "About")
        ]
        
        for path, name in pages:
            try:
                response = self.session.get(f"{self.base_url}{path}")
                success = response.status_code == 200
                self.log_test(
                    f"Access {name} Page",
                    success,
                    f"Status: {response.status_code}, Content length: {len(response.text)}"
                )
            except Exception as e:
                self.log_test(f"Access {name} Page", False, f"Exception: {str(e)}")

    def test_vector_add_and_semantic_search(self):
        """Test adding a Q&A and verifying it appears in semantic search."""
        print("=" * 60)
        print("TESTING VECTOR DB ADD + SEMANTIC SEARCH")
        print("=" * 60)
        test_qa = {
            "question": "What is the capital of France?",
            "answer": "The capital of France is Paris."
        }
        # Add Q&A
        try:
            response = self.session.post(
                f"{self.base_url}/api/add_qa",
                json=test_qa,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            self.log_test(
                "Add Q&A for Vector DB Test",
                success,
                f"Status: {response.status_code}, Response: {response.text}"
            )
        except Exception as e:
            self.log_test("Add Q&A for Vector DB Test", False, f"Exception: {str(e)}")
            return
        # Wait for vector store to rebuild
        import time; time.sleep(3)
        # Semantic search
        try:
            response = self.session.get(f"{self.base_url}/api/semantic_search?query=capital of France")
            success = response.status_code == 200
            data = response.json() if success else {}
            found = any("Paris" in doc.get("answer", "") for doc in data.get("documents", []))
            self.log_test(
                "Semantic Search After Add",
                success and found,
                f"Found Paris in semantic search: {found}"
            )
        except Exception as e:
            self.log_test("Semantic Search After Add", False, f"Exception: {str(e)}")

    def test_vector_update_and_semantic_search(self):
        """Test updating a Q&A and verifying the update in semantic search."""
        print("=" * 60)
        print("TESTING VECTOR DB UPDATE + SEMANTIC SEARCH")
        print("=" * 60)
        # Find the doc ID for our test Q&A
        try:
            docs_resp = self.session.get(f"{self.base_url}/api/documents?search=capital of France")
            docs = docs_resp.json().get("documents", [])
            doc = next((d for d in docs if "Paris" in d.get("answer", "")), None)
            doc_id = doc["id"] if doc else None
        except Exception as e:
            self.log_test("Find Q&A for Update", False, f"Exception: {str(e)}")
            return
        if doc_id is None:
            self.log_test("Find Q&A for Update", False, "Test Q&A not found for update.")
            return
        # Update Q&A
        update_qa = {
            "question": "What is the capital of France?",
            "answer": "Paris is the capital and largest city of France."
        }
        try:
            response = self.session.put(
                f"{self.base_url}/api/document/{doc_id}",
                json=update_qa,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            self.log_test(
                "Update Q&A for Vector DB Test",
                success,
                f"Status: {response.status_code}, Response: {response.text}"
            )
        except Exception as e:
            self.log_test("Update Q&A for Vector DB Test", False, f"Exception: {str(e)}")
            return
        # Wait for vector store to rebuild
        import time; time.sleep(3)
        # Semantic search
        try:
            response = self.session.get(f"{self.base_url}/api/semantic_search?query=capital of France")
            success = response.status_code == 200
            data = response.json() if success else {}
            found = any("largest city" in doc.get("answer", "") for doc in data.get("documents", []))
            self.log_test(
                "Semantic Search After Update",
                success and found,
                f"Found updated answer in semantic search: {found}"
            )
        except Exception as e:
            self.log_test("Semantic Search After Update", False, f"Exception: {str(e)}")

    def test_vector_delete_and_semantic_search(self):
        """Test deleting a Q&A and verifying it is removed from semantic search."""
        print("=" * 60)
        print("TESTING VECTOR DB DELETE + SEMANTIC SEARCH")
        print("=" * 60)
        # Find the doc ID for our test Q&A
        try:
            docs_resp = self.session.get(f"{self.base_url}/api/documents?search=capital of France")
            docs = docs_resp.json().get("documents", [])
            doc = next((d for d in docs if "Paris" in d.get("answer", "")), None)
            doc_id = doc["id"] if doc else None
        except Exception as e:
            self.log_test("Find Q&A for Delete", False, f"Exception: {str(e)}")
            return
        if doc_id is None:
            self.log_test("Find Q&A for Delete", False, "Test Q&A not found for delete.")
            return
        # Delete Q&A
        try:
            response = self.session.delete(f"{self.base_url}/api/document/{doc_id}")
            success = response.status_code == 200
            self.log_test(
                "Delete Q&A for Vector DB Test",
                success,
                f"Status: {response.status_code}, Response: {response.text}"
            )
        except Exception as e:
            self.log_test("Delete Q&A for Vector DB Test", False, f"Exception: {str(e)}")
            return
        # Wait for vector store to rebuild
        import time; time.sleep(3)
        # Semantic search
        try:
            response = self.session.get(f"{self.base_url}/api/semantic_search?query=capital of France")
            success = response.status_code == 200
            data = response.json() if success else {}
            found = any("Paris" in doc.get("answer", "") for doc in data.get("documents", []))
            self.log_test(
                "Semantic Search After Delete",
                success and not found,
                f"Paris found after delete (should be False): {found}"
            )
        except Exception as e:
            self.log_test("Semantic Search After Delete", False, f"Exception: {str(e)}")

    def test_potential_client_functionality(self):
        """Test potential client marking functionality."""
        print("=" * 60)
        print("TESTING POTENTIAL CLIENT FUNCTIONALITY")
        print("=" * 60)
        
        # Test 1: Create a session via the API
        try:
            response = self.session.post(f"{self.base_url}/api/chatbot/new-session")
            success = response.status_code == 200
            data = response.json() if success else {}
            session_id = data.get("session_id")
            self.log_test(
                "Create Session for Potential Client Test (API)",
                success and session_id is not None,
                f"Session ID: {session_id[:8]}..." if session_id else f"Status: {response.status_code}, Response: {response.text}"
            )
        except Exception as e:
            self.log_test("Create Session for Potential Client Test (API)", False, f"Exception: {str(e)}")
            return
        if not session_id:
            return
        
        # Test 2: Mark session as potential client via API
        try:
            response = self.session.put(
                f"{self.base_url}/api/dialogues/{session_id}/potential-client",
                json={"potential_client": True},
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Mark Session as Potential Client (API)",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}, Session ID: {session_id[:8]}..."
            )
        except Exception as e:
            self.log_test("Mark Session as Potential Client (API)", False, f"Exception: {str(e)}")
            return
        
        # Add a small delay to ensure the session is saved
        import time
        time.sleep(1)
        
        # Test 3: Verify session appears as potential client in API
        try:
            response = self.session.get(f"{self.base_url}/api/dialogues")
            success = response.status_code == 200
            data = response.json() if success else {}
            sessions = data.get("sessions", [])
            potential_client_session = next((s for s in sessions if s["session_id"] == session_id), None)
            is_potential_client = potential_client_session and potential_client_session.get("potential_client") == True
            
            # Debug info
            debug_info = f"Total sessions: {len(sessions)}, Found session: {potential_client_session is not None}"
            if potential_client_session:
                debug_info += f", potential_client field: {potential_client_session.get('potential_client')}"
            
            self.log_test(
                "Verify Potential Client in API",
                success and is_potential_client,
                f"Found potential client session: {is_potential_client}, Session ID: {session_id[:8]}... | {debug_info}"
            )
        except Exception as e:
            self.log_test("Verify Potential Client in API", False, f"Exception: {str(e)}")
        
        # Test 4: Test API endpoint for marking potential client (False)
        try:
            response = self.session.put(
                f"{self.base_url}/api/dialogues/{session_id}/potential-client",
                json={"potential_client": False},
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "API Mark Potential Client (False)",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}, Session ID: {session_id[:8]}..."
            )
        except Exception as e:
            self.log_test("API Mark Potential Client (False)", False, f"Exception: {str(e)}")
        
        # Test 5: Test API endpoint for marking as potential client again (True)
        try:
            response = self.session.put(
                f"{self.base_url}/api/dialogues/{session_id}/potential-client",
                json={"potential_client": True},
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "API Mark Potential Client (True)",
                success,
                f"Status: {response.status_code}, Response: {data.get('message', 'N/A')}, Session ID: {session_id[:8]}..."
            )
        except Exception as e:
            self.log_test("API Mark Potential Client (True)", False, f"Exception: {str(e)}")
        
        # Test 6: Clean up - delete the test session via API
        try:
            response = self.session.delete(f"{self.base_url}/api/dialogues/{session_id}")
            success = response.status_code == 200
            self.log_test(
                "Clean Up Test Session (API)",
                success,
                "Test session deleted"
            )
        except Exception as e:
            self.log_test("Clean Up Test Session (API)", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests and generate a summary report."""
        print("🚀 Starting NeuroBot Viewer and Database Tests")
        print("=" * 60)
        
        # Check if server is running
        if not self.test_server_connection():
            print("❌ ERROR: Flask server is not running!")
            print("Please start the server with: python app.py")
            return False
        
        print("✅ Server is running and accessible")
        print()
        
        # Run all test suites
        self.test_viewer_endpoints()
        self.test_database_functionality()
        self.test_chatbot_api()
        self.test_settings_api()
        self.test_frontend_pages()
        # Add vector DB and semantic search tests
        self.test_vector_add_and_semantic_search()
        self.test_vector_update_and_semantic_search()
        self.test_vector_delete_and_semantic_search()
        self.test_potential_client_functionality()
        
        # Generate summary
        self.generate_summary()
        
        return True

    def generate_summary(self):
        """Generate a summary of all test results."""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # Clean up test files
        self.cleanup_test_files()

    def cleanup_test_files(self):
        """Clean up test files created during testing."""
        try:
            test_files = [
                "test_dialogues.json",
                "test_dialogues_backup.json"
            ]
            
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🧹 Cleaned up: {file_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up test files: {str(e)}")

def main():
    """Main function to run the tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test NeuroBot viewer and database functionality")
    parser.add_argument(
        "--url", 
        default="http://localhost:5000",
        help="Base URL of the Flask application (default: http://localhost:5000)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = NeuroBotTester(args.url)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 