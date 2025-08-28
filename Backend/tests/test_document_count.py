#!/usr/bin/env python3
"""
Test script for document count functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import update_kb_document_count, get_knowledge_bases, parse_knowledge_file
from auth import get_current_user_data_dir

def test_document_count():
    """Test the document count functionality."""
    print("Testing document count functionality...")
    
    # Test updating document count for current KB
    print("\n1. Testing update_kb_document_count...")
    try:
        from app.blueprints.kb_api import get_current_kb_id
        current_kb_id = get_current_kb_id()
        print(f"Current KB ID: {current_kb_id}")
        
        # Get actual document count
        documents = parse_knowledge_file(current_kb_id)
        actual_count = len(documents)
        print(f"Actual document count: {actual_count}")
        
        # Update document count
        updated_count = update_kb_document_count(current_kb_id)
        print(f"Updated document count: {updated_count}")
        
        assert updated_count == actual_count, f"Document count mismatch: {updated_count} != {actual_count}"
        
        # Test getting knowledge bases
        print("\n2. Testing get_knowledge_bases...")
        kb_list = get_knowledge_bases()
        print(f"Found {len(kb_list)} knowledge bases")
        
        for kb in kb_list:
            print(f"KB: {kb['name']} (ID: {kb['id']}) - Documents: {kb['document_count']}")
            # Verify document count is accurate
            kb_documents = parse_knowledge_file(kb['id'])
            actual_kb_count = len(kb_documents)
            assert kb['document_count'] == actual_kb_count, f"KB {kb['id']} count mismatch: {kb['document_count']} != {actual_kb_count}"
        
        print("\n✅ All document count tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_count() 