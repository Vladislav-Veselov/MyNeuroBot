#!/usr/bin/env python3
"""
Model manager for controlling AI model selection per user.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from auth import get_current_user_data_dir
from tenant_context import get_model_override  # NEW

class ModelManager:
    def __init__(self):
        self.model_file_name = "model_config.json"
        self.available_models = {
            "gpt-4o-mini": "LITE (быстрый и экономичный)",
            "gpt-4o": "PRO (более мощный и точный)"
        }
        self.default_model = "gpt-4o-mini"
    
    def get_model_file_path(self) -> Path:
        """Get the path to the model config file for the current user."""
        try:
            user_data_dir = get_current_user_data_dir()
            return user_data_dir / self.model_file_name
        except Exception as e:
            print(f"Error getting model file path: {str(e)}")
            return None
    
    def get_current_model(self) -> str:
        """Get the current model for the user (respects per-request override)."""
        try:
            # NEW: take override if present and valid
            override = get_model_override()
            if override and override in self.available_models:
                return override

            model_file = self.get_model_file_path()
            if not model_file or not model_file.exists():
                return self.default_model

            with open(model_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            model = config.get('model', self.default_model)
            if model not in self.available_models:
                model = self.default_model

            return model
        except Exception as e:
            print(f"Error getting current model: {str(e)}")
            return self.default_model
    
    def set_model(self, model: str) -> bool:
        """Set the model for the current user."""
        try:
            if model not in self.available_models:
                print(f"Invalid model: {model}")
                return False
            
            model_file = self.get_model_file_path()
            if not model_file:
                return False
            
            config = {
                'model': model,
                'available_models': list(self.available_models.keys())
            }
            
            # Ensure directory exists
            model_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(model_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error setting model: {str(e)}")
            return False
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get the complete model configuration for the user."""
        try:
            model_file = self.get_model_file_path()
            if not model_file or not model_file.exists():
                # Return default config
                return {
                    'model': self.default_model,
                    'available_models': self.available_models,
                    'current_model_name': self.available_models[self.default_model]
                }
            
            with open(model_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            model = config.get('model', self.default_model)
            if model not in self.available_models:
                model = self.default_model
            
            return {
                'model': model,
                'available_models': self.available_models,
                'current_model_name': self.available_models[model]
            }
        except Exception as e:
            print(f"Error getting model config: {str(e)}")
            return {
                'model': self.default_model,
                'available_models': self.available_models,
                'current_model_name': self.available_models[self.default_model]
            }
    
    def get_available_models(self) -> Dict[str, str]:
        """Get the list of available models."""
        return self.available_models.copy()

# Global instance
model_manager = ModelManager() 