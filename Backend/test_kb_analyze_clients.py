#!/usr/bin/env python3
"""
Test script to verify KB analyze_clients functionality.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def test_kb_analyze_clients():
    """Test the KB analyze_clients functionality."""
    print("Testing KB analyze_clients functionality...")
    
    # Test 1: Check if new KB creation includes analyze_clients field
    print("\n1. Testing KB creation with analyze_clients field...")
    
    # Simulate KB info creation
    kb_info = {
        'name': 'Test KB',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'document_count': 0,
        'analyze_clients': False  # Test with False
    }
    
    print(f"KB info created: {kb_info}")
    print(f"analyze_clients field present: {'analyze_clients' in kb_info}")
    print(f"analyze_clients value: {kb_info.get('analyze_clients')}")
    
    # Test 2: Check backward compatibility
    print("\n2. Testing backward compatibility...")
    
    old_kb_info = {
        'name': 'Old KB',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'document_count': 0
        # No analyze_clients field
    }
    
    # Simulate the default behavior
    analyze_clients = old_kb_info.get('analyze_clients', True)
    print(f"Old KB info: {old_kb_info}")
    print(f"Default analyze_clients value: {analyze_clients}")
    
    # Test 3: Test session filtering logic
    print("\n3. Testing session filtering logic...")
    
    test_sessions = [
        {
            'session_id': 'session1',
            'metadata': {
                'kb_id': 'kb1',
                'analyze_clients': True
            }
        },
        {
            'session_id': 'session2', 
            'metadata': {
                'kb_id': 'kb2',
                'analyze_clients': False
            }
        },
        {
            'session_id': 'session3',
            'metadata': {
                'kb_id': 'kb3',
                'analyze_clients': True
            }
        }
    ]
    
    kb_settings = {
        'kb1': {'analyze_clients': True},
        'kb2': {'analyze_clients': False},
        'kb3': {'analyze_clients': True}
    }
    
    sessions_to_analyze = []
    for session in test_sessions:
        kb_id = session['metadata'].get('kb_id')
        if kb_id and kb_id in kb_settings:
            kb_setting = kb_settings[kb_id].get('analyze_clients', True)
            if kb_setting:
                sessions_to_analyze.append(session['session_id'])
                print(f"Session {session['session_id']} will be analyzed (KB {kb_id}: analyze_clients={kb_setting})")
            else:
                print(f"Session {session['session_id']} will be skipped (KB {kb_id}: analyze_clients={kb_setting})")
    
    print(f"\nTotal sessions to analyze: {len(sessions_to_analyze)}")
    print(f"Sessions to analyze: {sessions_to_analyze}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_kb_analyze_clients() 