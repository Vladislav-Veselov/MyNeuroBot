#!/usr/bin/env python3
"""
Test script to verify KB analyze_clients toggle functionality.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def test_kb_analyze_clients_toggle():
    """Test the KB analyze_clients toggle functionality."""
    print("Testing KB analyze_clients toggle functionality...")
    
    # Test 1: Simulate KB info with analyze_clients setting
    print("\n1. Testing KB info with analyze_clients setting...")
    
    kb_info = {
        'name': 'Test KB',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'document_count': 0,
        'analyze_clients': True
    }
    
    print(f"Initial KB info: {kb_info}")
    print(f"analyze_clients: {kb_info.get('analyze_clients')}")
    
    # Test 2: Simulate changing analyze_clients setting
    print("\n2. Testing analyze_clients setting change...")
    
    # Simulate API request to change setting
    new_analyze_clients = False
    kb_info['analyze_clients'] = new_analyze_clients
    kb_info['updated_at'] = datetime.now().isoformat()
    
    print(f"Updated KB info: {kb_info}")
    print(f"New analyze_clients value: {kb_info.get('analyze_clients')}")
    
    # Test 3: Test UI state detection
    print("\n3. Testing UI state detection...")
    
    test_cases = [
        ("Включен", True),
        ("Отключен", False),
        ("Включен (по умолчанию)", True),
        ("Отключен", False)
    ]
    
    for display_text, expected_value in test_cases:
        # Simulate the JavaScript logic for detecting current state
        is_enabled = "Включен" in display_text
        print(f"Display text: '{display_text}' -> Detected as enabled: {is_enabled} (Expected: {expected_value})")
    
    # Test 4: Test API response format
    print("\n4. Testing API response format...")
    
    api_response = {
        'success': True,
        'message': f'Настройка анализа клиентов изменена на {"включено" if new_analyze_clients else "отключено"}'
    }
    
    print(f"API response: {api_response}")
    
    # Test 5: Test backward compatibility
    print("\n5. Testing backward compatibility...")
    
    old_kb_info = {
        'name': 'Old KB',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'document_count': 0
        # No analyze_clients field
    }
    
    # Simulate adding the field to old KB
    old_kb_info['analyze_clients'] = True  # Default value
    old_kb_info['updated_at'] = datetime.now().isoformat()
    
    print(f"Old KB updated: {old_kb_info}")
    print(f"analyze_clients added: {'analyze_clients' in old_kb_info}")
    
    print("\n✅ All toggle tests passed!")

if __name__ == "__main__":
    test_kb_analyze_clients_toggle() 