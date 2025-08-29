#!/usr/bin/env python3
"""
Test script for API endpoints - tests the actual Flask API.
Run this after starting the Flask server.
"""

import requests
import json
import time
from pathlib import Path

class APITester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_server_connection(self):
        """Test if server is running"""
        print("🔌 Testing Server Connection")
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
            
    def test_knowledge_bases_endpoint(self):
        """Test knowledge bases endpoint"""
        print("\n📚 Testing Knowledge Bases Endpoint")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/api/knowledge-bases")
            
            if response.status_code == 200:
                data = response.json()
                if 'success' in data and data['success']:
                    kb_count = len(data.get('knowledge_bases', []))
                    self.log_test("Knowledge Bases List", True, f"Found {kb_count} KBs")
                    return True
                else:
                    self.log_test("Knowledge Bases List", False, "API returned success: false")
                    return False
            else:
                self.log_test("Knowledge Bases List", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Knowledge Bases List", False, f"Error: {str(e)}")
            return False
            
    def test_documents_endpoint(self):
        """Test documents endpoint"""
        print("\n📄 Testing Documents Endpoint")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/api/documents")
            
            if response.status_code == 200:
                data = response.json()
                if 'documents' in data:
                    doc_count = len(data['documents'])
                    self.log_test("Documents List", True, f"Found {doc_count} documents")
                    return True
                else:
                    self.log_test("Documents List", False, "No documents field in response")
                    return False
            else:
                self.log_test("Documents List", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Documents List", False, f"Error: {str(e)}")
            return False
            
    def test_add_qa_endpoint(self):
        """Test add Q&A endpoint"""
        print("\n➕ Testing Add Q&A Endpoint")
        print("-" * 40)
        
        try:
            test_data = {
                "question": f"API Test Question {int(time.time())}",
                "answer": "This is a test answer from API testing"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/add_qa",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Add Q&A", True, "Successfully added Q&A")
                    return True
                else:
                    self.log_test("Add Q&A", False, f"API error: {data.get('error', 'Unknown')}")
                    return False
            else:
                self.log_test("Add Q&A", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Add Q&A", False, f"Error: {str(e)}")
            return False
            
    def test_update_document_endpoint(self):
        """Test update document endpoint"""
        print("\n✏️  Testing Update Document Endpoint")
        print("-" * 40)
        
        try:
            # First get documents to find one to update
            response = self.session.get(f"{self.base_url}/api/documents")
            if response.status_code != 200:
                self.log_test("Update Document", False, "Could not fetch documents")
                return False
                
            data = response.json()
            documents = data.get('documents', [])
            
            if not documents:
                self.log_test("Update Document", True, "No documents to update")
                return True
                
            # Update first document
            doc_id = documents[0]['id']
            update_data = {
                "question": f"Updated Question {int(time.time())}",
                "answer": "Updated answer from API testing"
            }
            
            response = self.session.put(
                f"{self.base_url}/api/document/{doc_id}",
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Update Document", True, f"Successfully updated document {doc_id}")
                    return True
                else:
                    self.log_test("Update Document", False, f"API error: {data.get('error', 'Unknown')}")
                    return False
            else:
                self.log_test("Update Document", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Update Document", False, f"Error: {str(e)}")
            return False
            
    def test_delete_document_endpoint(self):
        """Test delete document endpoint"""
        print("\n🗑️  Testing Delete Document Endpoint")
        print("-" * 40)
        
        try:
            # First get documents to find one to delete
            response = self.session.get(f"{self.base_url}/api/documents")
            if response.status_code != 200:
                self.log_test("Delete Document", False, "Could not fetch documents")
                return False
                
            data = response.json()
            documents = data.get('documents', [])
            
            if not documents:
                self.log_test("Delete Document", True, "No documents to delete")
                return True
                
            # Delete first document
            doc_id = documents[0]['id']
            
            response = self.session.delete(f"{self.base_url}/api/document/{doc_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Delete Document", True, f"Successfully deleted document {doc_id}")
                    return True
                else:
                    self.log_test("Delete Document", False, f"API error: {data.get('error', 'Unknown')}")
                    return False
            else:
                self.log_test("Delete Document", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Delete Document", False, f"Error: {str(e)}")
            return False
            
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        print("\n📊 Testing Stats Endpoint")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/api/stats")
            
            if response.status_code == 200:
                data = response.json()
                if 'total_documents' in data:
                    doc_count = data['total_documents']
                    self.log_test("Stats", True, f"Total documents: {doc_count}")
                    return True
                else:
                    self.log_test("Stats", False, "No total_documents field in response")
                    return False
            else:
                self.log_test("Stats", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Stats", False, f"Error: {str(e)}")
            return False
            
    def test_download_endpoint(self):
        """Test download endpoint"""
        print("\n⬇️  Testing Download Endpoint")
        print("-" * 40)
        
        try:
            # First get knowledge bases to find one to download
            response = self.session.get(f"{self.base_url}/api/knowledge-bases")
            if response.status_code != 200:
                self.log_test("Download", False, "Could not fetch knowledge bases")
                return False
                
            data = response.json()
            knowledge_bases = data.get('knowledge_bases', [])
            
            if not knowledge_bases:
                self.log_test("Download", True, "No knowledge bases to download")
                return True
                
            # Download first KB
            kb_id = knowledge_bases[0]['id']
            
            response = self.session.get(f"{self.base_url}/api/knowledge-bases/{kb_id}/download")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type or 'application/octet-stream' in content_type:
                    self.log_test("Download", True, f"Successfully downloaded KB {kb_id}")
                    return True
                else:
                    self.log_test("Download", False, f"Unexpected content type: {content_type}")
                    return False
            else:
                self.log_test("Download", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Download", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting API Endpoint Tests...")
        print("=" * 60)
        
        # Test server connection first
        if not self.test_server_connection():
            print("❌ Cannot connect to server. Make sure Flask is running.")
            return
            
        # Run all tests
        self.test_knowledge_bases_endpoint()
        self.test_documents_endpoint()
        self.test_add_qa_endpoint()
        self.test_update_document_endpoint()
        self.test_delete_document_endpoint()
        self.test_stats_endpoint()
        self.test_download_endpoint()
        
        print("=" * 60)
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n📊 API Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
                    
        if failed_tests == 0:
            print(f"\n🎉 All API tests passed! The JSON migration is working correctly.")
        else:
            print(f"\n🔧 {failed_tests} API tests failed. Please review the errors above.")

def main():
    """Main function"""
    print("🧪 API Endpoint Test Suite")
    print("Testing Flask API endpoints for JSON migration")
    print()
    
    # Check if server is running
    tester = APITester()
    tester.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in tester.test_results if not result['success'])
    exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()
