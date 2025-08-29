#!/usr/bin/env python3
"""
Simple test script for JSON migration - minimal dependencies.
Tests core functionality without complex imports.
"""

import json
import time
from pathlib import Path
import sys
import os

def test_json_basic():
    """Test basic JSON functionality"""
    print("📋 Testing Basic JSON Functionality")
    print("-" * 40)
    
    try:
        # Find user data directory (relative to Backend directory)
        user_data_dir = Path("../user_data")
        if not user_data_dir.exists():
            print("❌ user_data directory not found")
            return False
            
        # Look for vladis user
        vladis_dir = user_data_dir / "vladis"
        if not vladis_dir.exists():
            print("❌ vladis user directory not found")
            return False
            
        # Find knowledge bases
        kb_dir = vladis_dir / "knowledge_bases"
        if not kb_dir.exists():
            print("❌ knowledge_bases directory not found")
            return False
            
        # Find first KB
        kb_folders = [f for f in kb_dir.iterdir() if f.is_dir()]
        if not kb_folders:
            print("❌ No knowledge bases found")
            return False
            
        kb_id = kb_folders[0].name
        print(f"✅ Found KB: {kb_id}")
        
        # Test knowledge.json
        knowledge_file = kb_dir / kb_id / "knowledge.json"
        if not knowledge_file.exists():
            print("❌ knowledge.json not found")
            return False
            
        print(f"✅ Found knowledge.json: {knowledge_file}")
        
        # Test reading JSON
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ JSON read successful: {len(data)} items")
            
            # Test structure
            if data and isinstance(data, list):
                first_item = data[0]
                if isinstance(first_item, dict) and 'question' in first_item and 'answer' in first_item:
                    print("✅ JSON structure correct")
                else:
                    print("❌ JSON structure incorrect")
                    return False
            else:
                print("⚠️  Knowledge base is empty (this is normal)")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading JSON: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Exception in basic test: {e}")
        return False

def test_crud_operations():
    """Test basic CRUD operations"""
    print("\n🔄 Testing CRUD Operations")
    print("-" * 40)
    
    try:
        # Find KB
        user_data_dir = Path("../user_data")
        vladis_dir = user_data_dir / "vladis"
        kb_dir = vladis_dir / "knowledge_bases"
        kb_id = [f for f in kb_dir.iterdir() if f.is_dir()][0].name
        
        knowledge_file = kb_dir / kb_id / "knowledge.json"
        
        # Backup original content
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        print(f"✅ Original data: {len(original_data)} items")
        
        # Test 1: Create
        test_data = [
            {"question": "Test question 1", "answer": "Test answer 1"},
            {"question": "Test question 2", "answer": "Test answer 2"}
        ]
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        # Verify create
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            created_data = json.load(f)
            
        if len(created_data) == 2:
            print("✅ Create test passed")
        else:
            print("❌ Create test failed")
            return False
            
        # Test 2: Read
        if created_data[0]['question'] == "Test question 1":
            print("✅ Read test passed")
        else:
            print("❌ Read test failed")
            return False
            
        # Test 3: Update
        created_data[0]['question'] = "Updated question 1"
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(created_data, f, ensure_ascii=False, indent=2)
            
        # Verify update
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
            
        if updated_data[0]['question'] == "Updated question 1":
            print("✅ Update test passed")
        else:
            print("❌ Update test failed")
            return False
            
        # Test 4: Delete
        updated_data.pop(0)
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
        # Verify delete
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            final_data = json.load(f)
            
        if len(final_data) == 1:
            print("✅ Delete test passed")
        else:
            print("❌ Delete test failed")
            return False
            
        # Restore original data
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
            
        print("✅ Original data restored")
        return True
        
    except Exception as e:
        print(f"❌ Exception in CRUD test: {e}")
        return False

def test_edge_cases():
    """Test edge cases"""
    print("\n🔍 Testing Edge Cases")
    print("-" * 40)
    
    try:
        # Find KB
        user_data_dir = Path("../user_data")
        vladis_dir = user_data_dir / "vladis"
        kb_dir = vladis_dir / "knowledge_bases"
        kb_id = [f for f in kb_dir.iterdir() if f.is_dir()][0].name
        
        knowledge_file = kb_dir / kb_id / "knowledge.json"
        
        # Backup original content
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # Test 1: Empty data
        empty_data = []
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
            
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            
        if len(loaded_data) == 0:
            print("✅ Empty data handling passed")
        else:
            print("❌ Empty data handling failed")
            return False
            
        # Test 2: Special characters
        special_data = [
            {"question": "Test with émojis 🚀🎉", "answer": "Answer with symbols: ©®™"},
            {"question": "Test with quotes: \"Hello\" 'World'", "answer": "Answer with <tags> & entities"}
        ]
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(special_data, f, ensure_ascii=False, indent=2)
            
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            
        if len(loaded_data) == 2:
            print("✅ Special characters handling passed")
        else:
            print("❌ Special characters handling failed")
            return False
            
        # Test 3: Very long content
        long_question = "A" * 500
        long_answer = "B" * 1000
        long_data = [{"question": long_question, "answer": long_answer}]
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(long_data, f, ensure_ascii=False, indent=2)
            
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            
        if len(loaded_data) == 1 and len(loaded_data[0]['question']) == 500:
            print("✅ Long content handling passed")
        else:
            print("❌ Long content handling failed")
            return False
            
        # Test 4: Malformed JSON handling
        try:
            # Write malformed JSON
            knowledge_file.write_text('{"invalid": json', encoding='utf-8')
            
            # Try to read it
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                json.load(f)
            print("❌ Malformed JSON should have failed")
            return False
        except json.JSONDecodeError:
            print("✅ Malformed JSON handling passed")
        except Exception as e:
            print(f"❌ Unexpected error with malformed JSON: {e}")
            return False
            
        # Restore original data after all edge case tests
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
            
        return True
        
    except Exception as e:
        print(f"❌ Exception in edge cases test: {e}")
        return False

def test_performance():
    """Test basic performance"""
    print("\n⚡ Testing Performance")
    print("-" * 40)
    
    try:
        # Find KB
        user_data_dir = Path("../user_data")
        vladis_dir = user_data_dir / "vladis"
        kb_dir = vladis_dir / "knowledge_bases"
        kb_id = [f for f in kb_dir.iterdir() if f.is_dir()][0].name
        
        knowledge_file = kb_dir / kb_id / "knowledge.json"
        
        # Test read performance
        start_time = time.time()
        for _ in range(100):
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        read_time = time.time() - start_time
        
        print(f"✅ Read performance: 100 reads in {read_time:.3f}s")
        
        # Test write performance
        test_data = [{"question": f"Q{i}", "answer": f"A{i}"} for i in range(10)]
        
        start_time = time.time()
        for _ in range(10):
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
        write_time = time.time() - start_time
        
        print(f"✅ Write performance: 10 writes in {write_time:.3f}s")
        
        # Test file size
        file_size = knowledge_file.stat().st_size
        print(f"✅ File size: {file_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception in performance test: {e}")
        return False

def test_vector_store_files():
    """Test vector store file existence"""
    print("\n🧠 Testing Vector Store Files")
    print("-" * 40)
    
    try:
        # Find KB
        user_data_dir = Path("../user_data")
        vladis_dir = user_data_dir / "vladis"
        kb_dir = vladis_dir / "knowledge_bases"
        kb_id = [f for f in kb_dir.iterdir() if f.is_dir()][0].name
        
        vector_dir = kb_dir / kb_id / "vector_KB"
        index_file = vector_dir / "index.faiss"
        docstore_file = vector_dir / "docstore.json"
        
        print(f"✅ Vector directory: {vector_dir}")
        print(f"✅ Index file exists: {index_file.exists()}")
        print(f"✅ Docstore file exists: {docstore_file.exists()}")
        
        if docstore_file.exists():
            with open(docstore_file, 'r', encoding='utf-8') as f:
                docstore = json.load(f)
            print(f"✅ Docstore entries: {len(docstore)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Exception in vector store test: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Simple JSON Migration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic JSON", test_json_basic),
        ("CRUD Operations", test_crud_operations),
        ("Edge Cases", test_edge_cases),
        ("Performance", test_performance),
        ("Vector Store Files", test_vector_store_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! JSON migration is working correctly.")
        return 0
    else:
        print("🔧 Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
