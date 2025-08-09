#!/usr/bin/env python3
"""
Test script for model manager functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_manager import model_manager

def test_model_manager():
    """Test the model manager functionality."""
    print("Testing model manager functionality...")
    
    # Test initial model (should be default)
    print("\n1. Testing initial model...")
    current_model = model_manager.get_current_model()
    print(f"Initial model: {current_model}")
    assert current_model == "gpt-4o-mini", "Initial model should be gpt-4o-mini"
    
    # Test model config
    print("\n2. Testing model config...")
    config = model_manager.get_model_config()
    print(f"Model config: {config}")
    assert config['model'] == "gpt-4o-mini", "Config model should be gpt-4o-mini"
    assert "gpt-4o-mini" in config['available_models'], "gpt-4o-mini should be available"
    assert "gpt-4o" in config['available_models'], "gpt-4o should be available"
    
    # Test setting model to gpt-4o
    print("\n3. Testing set model to gpt-4o...")
    success = model_manager.set_model("gpt-4o")
    print(f"Set model success: {success}")
    assert success, "Set model should succeed"
    
    # Test current model after change
    current_model = model_manager.get_current_model()
    print(f"Current model after change: {current_model}")
    assert current_model == "gpt-4o", "Model should be gpt-4o"
    
    # Test config after change
    config = model_manager.get_model_config()
    print(f"Config after change: {config}")
    assert config['model'] == "gpt-4o", "Config model should be gpt-4o"
    assert config['current_model_name'] == "GPT-4o (более мощный и точный)", "Model name should match"
    
    # Test setting back to gpt-4o-mini
    print("\n4. Testing set model back to gpt-4o-mini...")
    success = model_manager.set_model("gpt-4o-mini")
    print(f"Set model back success: {success}")
    assert success, "Set model back should succeed"
    
    # Test current model after change back
    current_model = model_manager.get_current_model()
    print(f"Current model after change back: {current_model}")
    assert current_model == "gpt-4o-mini", "Model should be gpt-4o-mini"
    
    # Test invalid model
    print("\n5. Testing invalid model...")
    success = model_manager.set_model("invalid-model")
    print(f"Set invalid model success: {success}")
    assert not success, "Set invalid model should fail"
    
    print("\n✅ All model manager tests passed!")

if __name__ == "__main__":
    test_model_manager() 