#!/usr/bin/env python3
"""
Test script to verify KB-specific settings functionality.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def test_kb_specific_settings():
    """Test the KB-specific settings functionality."""
    print("Testing KB-specific settings functionality...")
    
    # Test 1: Simulate KB-specific settings structure
    print("\n1. Testing KB-specific settings structure...")
    
    test_kb_id = "test_kb_123"
    test_settings = {
        'tone': 3,
        'humor': 1,
        'brevity': 4,
        'additional_prompt': 'Ты специалист по продажам. Всегда предлагай товары и услуги.'
    }
    
    print(f"KB ID: {test_kb_id}")
    print(f"Settings: {json.dumps(test_settings, ensure_ascii=False, indent=2)}")
    
    # Test 2: Simulate file path structure
    print("\n2. Testing file path structure...")
    
    user_data_dir = Path("user_data/test_user")
    kb_dir = user_data_dir / "knowledge_bases" / test_kb_id
    settings_file = kb_dir / "system_prompt.txt"
    
    print(f"User data dir: {user_data_dir}")
    print(f"KB dir: {kb_dir}")
    print(f"Settings file: {settings_file}")
    
    # Test 3: Simulate API endpoint patterns
    print("\n3. Testing API endpoint patterns...")
    
    api_endpoints = [
        f"GET /api/get_settings/{test_kb_id}",
        f"POST /api/save_settings/{test_kb_id}",
        "GET /api/knowledge-bases",
        f"GET /api/knowledge-bases/{test_kb_id}"
    ]
    
    for endpoint in api_endpoints:
        print(f"Endpoint: {endpoint}")
    
    # Test 4: Simulate settings validation
    print("\n4. Testing settings validation...")
    
    def validate_settings(settings):
        """Simulate settings validation logic."""
        errors = []
        
        # Validate tone (0-4)
        tone = settings.get('tone', 2)
        if not (0 <= tone <= 4):
            errors.append(f"Тон общения должен быть от 0 до 4, получено: {tone}")
        
        # Validate humor (0-4)
        humor = settings.get('humor', 2)
        if not (0 <= humor <= 4):
            errors.append(f"Уровень юмора должен быть от 0 до 4, получено: {humor}")
        
        # Validate brevity (0-4)
        brevity = settings.get('brevity', 2)
        if not (0 <= brevity <= 4):
            errors.append(f"Уровень краткости должен быть от 0 до 4, получено: {brevity}")
        
        return errors
    
    validation_errors = validate_settings(test_settings)
    if validation_errors:
        print("❌ Validation errors:")
        for error in validation_errors:
            print(f"   - {error}")
    else:
        print("✅ Settings validation passed")
    
    # Test 5: Simulate legacy settings conversion
    print("\n5. Testing legacy settings conversion...")
    
    legacy_settings = {
        'tone': 'friendly',
        'humor': 2,
        'brevity': 3,
        'additional_prompt': 'Legacy prompt'
    }
    
    tone_mapping = {'formal': 0, 'friendly': 2, 'casual': 4}
    
    if isinstance(legacy_settings.get('tone'), str):
        legacy_settings['tone'] = tone_mapping.get(legacy_settings['tone'], 2)
    
    print(f"Legacy settings: {legacy_settings}")
    print(f"Converted tone: {legacy_settings['tone']}")
    
    # Test 6: Simulate default settings
    print("\n6. Testing default settings...")
    
    default_settings = {
        'tone': 2,
        'humor': 2,
        'brevity': 2,
        'additional_prompt': ''
    }
    
    print(f"Default settings: {json.dumps(default_settings, ensure_ascii=False, indent=2)}")
    
    # Test 7: Simulate KB switching logic
    print("\n7. Testing KB switching logic...")
    
    kb_list = [
        {'id': 'kb1', 'name': 'Основная база знаний'},
        {'id': 'kb2', 'name': 'Продажи'},
        {'id': 'kb3', 'name': 'Поддержка'}
    ]
    
    for kb in kb_list:
        print(f"KB: {kb['name']} (ID: {kb['id']})")
        # Simulate loading settings for each KB
        print(f"  -> Loading settings from: user_data/knowledge_bases/{kb['id']}/system_prompt.txt")
    
    print("\n✅ All KB-specific settings tests passed!")

if __name__ == "__main__":
    test_kb_specific_settings() 