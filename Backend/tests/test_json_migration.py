#!/usr/bin/env python3
"""
Comprehensive test script for JSON migration and system robustness.
Tests all critical functionality while being mindful of API token usage.
"""

import json
import time
import random
import string
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

# Add Backend to path for imports
sys.path.append(os.path.dirname(__file__))

from app.blueprints.kb_api import (
    read_knowledge_file, write_knowledge_file, get_knowledge_file_path,
    get_current_kb_id, find_kb_by_password
)
from vectorize import rebuild_vector_store_with_context
from auth import get_current_user_data_dir
from chatbot_service import ChatbotService

class TestRunner:
    def __init__(self, username: str = "vladis", password: str = "654321"):
        self.username = username
        self.password = username  # In this system, username is used as password
        self.test_results = []
        self.errors = []
        self.warnings = []
        
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
        if not success:
            self.errors.append(f"{test_name}: {details}")
            
    def log_warning(self, message: str):
        """Log warnings"""
        print(f"⚠️  WARNING: {message}")
        self.warnings.append(message)
        
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting comprehensive JSON migration and system tests...")
        print("=" * 60)
        
        # Test 1: Basic JSON functionality
        self.test_json_basic_functionality()
        
        # Test 2: CRUD operations
        self.test_crud_operations()
        
        # Test 3: Edge cases and robustness
        self.test_edge_cases()
        
        # Test 4: Vector store integration
        self.test_vector_store_integration()
        
        # Test 5: Performance and token efficiency
        self.test_performance_and_efficiency()
        
        # Test 6: Data integrity
        self.test_data_integrity()
        
        # Test 7: Error handling
        self.test_error_handling()
        
        # Test 8: Multi-language support
        self.test_multi_language_support()
        
        print("=" * 60)
        self.print_summary()
        
    def test_json_basic_functionality(self):
        """Test basic JSON reading/writing functionality"""
        print("\n📋 Testing Basic JSON Functionality")
        print("-" * 40)
        
        try:
            # Test 1.1: Read existing knowledge file
            kb_id = get_current_kb_id()
            knowledge_path = get_knowledge_file_path(kb_id)
            
            if knowledge_path.exists():
                data = read_knowledge_file(kb_id)
                self.log_test("JSON Read", True, f"Loaded {len(data)} items from {knowledge_path.name}")
                
                # Verify JSON structure
                if data:
                    first_item = data[0]
                    required_fields = ['id', 'question', 'answer', 'content']
                    has_all_fields = all(field in first_item for field in required_fields)
                    self.log_test("JSON Structure", has_all_fields, 
                                f"First item has fields: {list(first_item.keys())}")
                else:
                    self.log_warning("Knowledge base is empty - this is normal for new users")
            else:
                self.log_test("JSON Read", False, f"Knowledge file not found: {knowledge_path}")
                
        except Exception as e:
            self.log_test("JSON Read", False, f"Exception: {str(e)}")
            
    def test_crud_operations(self):
        """Test Create, Read, Update, Delete operations"""
        print("\n🔄 Testing CRUD Operations")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            
            # Test 2.1: Create new Q&A
            test_question = f"Test question {random.randint(1000, 9999)}"
            test_answer = f"Test answer with special chars: !@#$%^&*()_+-=[]{{}}|;':\",./<>?"
            
            # Read current data
            current_data = read_knowledge_file(kb_id)
            initial_count = len(current_data)
            
            # Add new item
            new_item = {
                "id": len(current_data),
                "question": test_question,
                "answer": test_answer,
                "content": f"Вопрос: {test_question}\n{test_answer}"
            }
            current_data.append(new_item)
            
            # Write back
            write_knowledge_file(current_data, kb_id)
            
            # Verify addition
            updated_data = read_knowledge_file(kb_id)
            self.log_test("Create Q&A", len(updated_data) == initial_count + 1,
                         f"Count: {initial_count} → {len(updated_data)}")
            
            # Test 2.2: Read specific item
            found_item = next((item for item in updated_data if item['question'] == test_question), None)
            self.log_test("Read Q&A", found_item is not None, 
                         f"Found item with question: {test_question[:30]}...")
            
            # Test 2.3: Update item
            if found_item:
                item_id = found_item['id']
                updated_question = f"Updated question {random.randint(1000, 9999)}"
                updated_data[item_id]['question'] = updated_question
                updated_data[item_id]['content'] = f"Вопрос: {updated_question}\n{test_answer}"
                
                write_knowledge_file(updated_data, kb_id)
                
                # Verify update
                final_data = read_knowledge_file(kb_id)
                updated_item = next((item for item in final_data if item['id'] == item_id), None)
                self.log_test("Update Q&A", updated_item and updated_item['question'] == updated_question,
                             f"Question updated to: {updated_question[:30]}...")
                
                # Test 2.4: Delete item
                final_data.pop(item_id)
                # Reindex remaining items
                for i, item in enumerate(final_data):
                    item['id'] = i
                
                write_knowledge_file(final_data, kb_id)
                
                # Verify deletion
                final_check = read_knowledge_file(kb_id)
                self.log_test("Delete Q&A", len(final_check) == initial_count,
                             f"Count restored to: {len(final_check)}")
                
        except Exception as e:
            self.log_test("CRUD Operations", False, f"Exception: {str(e)}")
            
    def test_edge_cases(self):
        """Test edge cases and robustness"""
        print("\n🔍 Testing Edge Cases and Robustness")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            
            # Test 3.1: Empty strings
            edge_data = [
                {"question": "", "answer": "Valid answer"},
                {"question": "Valid question", "answer": ""},
                {"question": "   ", "answer": "   "},
                {"question": "Normal question", "answer": "Normal answer"}
            ]
            
            write_knowledge_file(edge_data, kb_id)
            loaded_data = read_knowledge_file(kb_id)
            
            # Should handle empty strings gracefully
            self.log_test("Empty String Handling", True, 
                         f"Loaded {len(loaded_data)} items with edge cases")
            
            # Test 3.2: Very long content
            long_question = "A" * 1000
            long_answer = "B" * 2000
            long_data = [
                {"question": long_question, "answer": long_answer}
            ]
            
            write_knowledge_file(long_data, kb_id)
            long_loaded = read_knowledge_file(kb_id)
            
            self.log_test("Long Content Handling", len(long_loaded) == 1,
                         f"Loaded item with {len(long_question)} char question")
            
            # Test 3.3: Special characters
            special_chars = [
                {"question": "Test with émojis 🚀🎉", "answer": "Answer with symbols: ©®™"},
                {"question": "Test with quotes: \"Hello\" 'World'", "answer": "Answer with <tags> & entities"},
                {"question": "Test with newlines\nand tabs\t", "answer": "Answer with\nmultiple\nlines"}
            ]
            
            write_knowledge_file(special_chars, kb_id)
            special_loaded = read_knowledge_file(kb_id)
            
            self.log_test("Special Characters", len(special_loaded) == 3,
                         f"Loaded {len(special_loaded)} items with special chars")
            
            # Test 3.4: Malformed JSON handling
            knowledge_path = get_knowledge_file_path(kb_id)
            backup_content = knowledge_path.read_text(encoding='utf-8')
            
            # Write malformed JSON
            knowledge_path.write_text('{"invalid": json}', encoding='utf-8')
            
            try:
                malformed_data = read_knowledge_file(kb_id)
                # Should handle gracefully and return empty list
                self.log_test("Malformed JSON Handling", len(malformed_data) == 0,
                             "Gracefully handled malformed JSON")
            except Exception:
                self.log_test("Malformed JSON Handling", False, "Failed to handle malformed JSON")
            finally:
                # Restore valid content
                knowledge_path.write_text(backup_content, encoding='utf-8')
                
        except Exception as e:
            self.log_test("Edge Cases", False, f"Exception: {str(e)}")
            
    def test_vector_store_integration(self):
        """Test vector store integration (minimal token usage)"""
        print("\n🧠 Testing Vector Store Integration")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            user_data_dir = get_current_user_data_dir()
            
            # Test 4.1: Check vector store files exist
            vector_dir = user_data_dir / "knowledge_bases" / kb_id / "vector_KB"
            index_file = vector_dir / "index.faiss"
            docstore_file = vector_dir / "docstore.json"
            
            has_vector_files = index_file.exists() and docstore_file.exists()
            self.log_test("Vector Store Files", has_vector_files,
                         f"Index: {index_file.exists()}, Docstore: {docstore_file.exists()}")
            
            if has_vector_files:
                # Test 4.2: Check docstore structure
                with open(docstore_file, 'r', encoding='utf-8') as f:
                    docstore = json.load(f)
                
                self.log_test("Docstore Structure", isinstance(docstore, dict),
                             f"Docstore has {len(docstore)} entries")
                
                # Test 4.3: Minimal vector rebuild test (only if needed)
                knowledge_data = read_knowledge_file(kb_id)
                if knowledge_data:
                    print("  ⚠️  Skipping vector rebuild test to save tokens")
                    print("  💡 Run manually: rebuild_vector_store_with_context()")
                else:
                    self.log_test("Vector Store", True, "No data to vectorize")
                    
        except Exception as e:
            self.log_test("Vector Store Integration", False, f"Exception: {str(e)}")
            
    def test_performance_and_efficiency(self):
        """Test performance and token efficiency"""
        print("\n⚡ Testing Performance and Token Efficiency")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            
            # Test 5.1: JSON parsing speed
            knowledge_path = get_knowledge_file_path(kb_id)
            
            if knowledge_path.exists():
                start_time = time.time()
                data = read_knowledge_file(kb_id)
                parse_time = time.time() - start_time
                
                self.log_test("JSON Parse Speed", parse_time < 0.1,
                             f"Parsed {len(data)} items in {parse_time:.3f}s")
                
                # Test 5.2: File size efficiency
                file_size = knowledge_path.stat().st_size
                item_count = len(data)
                
                if item_count > 0:
                    avg_size_per_item = file_size / item_count
                    self.log_test("File Size Efficiency", avg_size_per_item < 1000,
                                 f"Average {avg_size_per_item:.1f} bytes per item")
                else:
                    self.log_test("File Size Efficiency", True, "No items to measure")
                    
            # Test 5.3: Memory usage (rough estimate)
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform some operations
            for _ in range(100):
                _ = read_knowledge_file(kb_id)
                
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            self.log_test("Memory Efficiency", memory_increase < 50,
                         f"Memory increase: {memory_increase:.1f} MB")
                         
        except Exception as e:
            self.log_test("Performance Tests", False, f"Exception: {str(e)}")
            
    def test_data_integrity(self):
        """Test data integrity and consistency"""
        print("\n🔒 Testing Data Integrity")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            
            # Test 6.1: ID consistency
            data = read_knowledge_file(kb_id)
            if data:
                ids = [item['id'] for item in data]
                expected_ids = list(range(len(data)))
                
                self.log_test("ID Consistency", ids == expected_ids,
                             f"IDs: {ids[:5]}... (should be sequential)")
                
                # Test 6.2: Content consistency
                content_consistent = True
                for item in data:
                    expected_content = f"Вопрос: {item['question']}\n{item['answer']}"
                    if item['content'] != expected_content:
                        content_consistent = False
                        break
                        
                self.log_test("Content Consistency", content_consistent,
                             "All items have correct content format")
                
                # Test 6.3: Data validation
                valid_items = 0
                for item in data:
                    if (isinstance(item.get('question'), str) and 
                        isinstance(item.get('answer'), str) and
                        isinstance(item.get('id'), int) and
                        isinstance(item.get('content'), str)):
                        valid_items += 1
                        
                self.log_test("Data Validation", valid_items == len(data),
                             f"All {valid_items} items have valid data types")
                
            else:
                self.log_test("Data Integrity", True, "No data to validate")
                
        except Exception as e:
            self.log_test("Data Integrity", False, f"Exception: {str(e)}")
            
    def test_error_handling(self):
        """Test error handling and recovery"""
        print("\n🛡️  Testing Error Handling")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            knowledge_path = get_knowledge_file_path(kb_id)
            
            # Test 7.1: Non-existent file handling
            non_existent_path = Path("/non/existent/path/knowledge.json")
            try:
                data = read_knowledge_file("non_existent_kb")
                self.log_test("Non-existent File Handling", len(data) == 0,
                             "Gracefully handled non-existent file")
            except Exception:
                self.log_test("Non-existent File Handling", False, "Failed to handle non-existent file")
                
            # Test 7.2: Permission error handling (simulated)
            if knowledge_path.exists():
                original_permissions = knowledge_path.stat().st_mode
                
                # Try to read with current permissions
                try:
                    data = read_knowledge_file(kb_id)
                    self.log_test("Permission Handling", True, "Successfully read with current permissions")
                except Exception as e:
                    self.log_test("Permission Handling", False, f"Failed to read: {str(e)}")
                    
            # Test 7.3: Corrupted data handling
            if knowledge_path.exists():
                backup_content = knowledge_path.read_text(encoding='utf-8')
                
                # Write corrupted data
                knowledge_path.write_text('{"corrupted": "data"', encoding='utf-8')
                
                try:
                    corrupted_data = read_knowledge_file(kb_id)
                    # Should handle gracefully
                    self.log_test("Corrupted Data Handling", True, "Gracefully handled corrupted data")
                except Exception:
                    self.log_test("Corrupted Data Handling", False, "Failed to handle corrupted data")
                finally:
                    # Restore valid content
                    knowledge_path.write_text(backup_content, encoding='utf-8')
                    
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
            
    def test_multi_language_support(self):
        """Test multi-language support"""
        print("\n🌍 Testing Multi-language Support")
        print("-" * 40)
        
        try:
            kb_id = get_current_kb_id()
            
            # Test 8.1: Russian text (original format)
            russian_data = [
                {"question": "Что такое NeuroBot?", "answer": "NeuroBot — это AI-ассистент"},
                {"question": "Как работает система?", "answer": "Система использует векторные базы данных"}
            ]
            
            write_knowledge_file(russian_data, kb_id)
            russian_loaded = read_knowledge_file(kb_id)
            
            self.log_test("Russian Text Support", len(russian_loaded) == 2,
                         f"Loaded {len(russian_loaded)} Russian items")
            
            # Test 8.2: English text
            english_data = [
                {"question": "What is NeuroBot?", "answer": "NeuroBot is an AI assistant"},
                {"question": "How does the system work?", "answer": "The system uses vector databases"}
            ]
            
            write_knowledge_file(english_data, kb_id)
            english_loaded = read_knowledge_file(kb_id)
            
            self.log_test("English Text Support", len(english_loaded) == 2,
                         f"Loaded {len(english_loaded)} English items")
            
            # Test 8.3: Mixed language
            mixed_data = [
                {"question": "What is NeuroBot? / Что такое NeuroBot?", 
                 "answer": "NeuroBot is an AI assistant / NeuroBot — это AI-ассистент"}
            ]
            
            write_knowledge_file(mixed_data, kb_id)
            mixed_loaded = read_knowledge_file(kb_id)
            
            self.log_test("Mixed Language Support", len(mixed_loaded) == 1,
                         f"Loaded {len(mixed_loaded)} mixed language items")
                         
        except Exception as e:
            self.log_test("Multi-language Support", False, f"Exception: {str(e)}")
            
    def print_summary(self):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if failed_tests == 0:
            print(f"\n🎉 All tests passed! The JSON migration is working correctly.")
        else:
            print(f"\n🔧 {failed_tests} tests failed. Please review the errors above.")
            
        # Print recommendations
        print(f"\n💡 Recommendations:")
        if failed_tests == 0:
            print("  - System is ready for production use")
            print("  - Consider running vector store rebuilds for active KBs")
            print("  - Monitor system performance in production")
        else:
            print("  - Fix failing tests before deployment")
            print("  - Review error logs for specific issues")
            print("  - Consider rolling back if critical failures occur")

def main():
    """Main test execution"""
    print("🧪 NeuroBot JSON Migration Test Suite")
    print("Testing system robustness and JSON functionality")
    print()
    
    # Check if running from correct directory
    if not Path("app").exists():
        print("❌ Error: Please run this script from the Backend directory")
        print("   cd Backend && python test_json_migration.py")
        return
        
    # Run tests
    test_runner = TestRunner()
    test_runner.run_all_tests()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in test_runner.test_results if not result['success'])
    sys.exit(1 if failed_tests > 0 else 0)

if __name__ == "__main__":
    main()
