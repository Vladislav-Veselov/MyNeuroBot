#!/usr/bin/env python3
"""
Chatbot status manager for controlling chatbot availability per user.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from auth import get_current_user_data_dir

class ChatbotStatusManager:
    def __init__(self):
        self.status_file_name = "chatbot_status.json"
    
    def get_status_file_path(self) -> Path:
        """Get the path to the chatbot status file for the current user."""
        try:
            user_data_dir = get_current_user_data_dir()
            return user_data_dir / self.status_file_name
        except Exception as e:
            print(f"Error getting status file path: {str(e)}")
            return None
    
    def get_chatbot_status(self) -> Dict[str, Any]:
        """Get the current chatbot status for the user."""
        try:
            status_file = self.get_status_file_path()
            if not status_file or not status_file.exists():
                # Default status: chatbots are running
                return {
                    "stopped": False,
                    "stopped_at": None,
                    "stopped_by": None,
                    "message": None
                }
            
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            
            return status
        except Exception as e:
            print(f"Error getting chatbot status: {str(e)}")
            return {
                "stopped": False,
                "stopped_at": None,
                "stopped_by": None,
                "message": None
            }
    
    def stop_chatbots(self, stopped_by: str = "user", message: str = "Чатбот временно остановлен") -> bool:
        """Stop all chatbots for the current user."""
        try:
            status_file = self.get_status_file_path()
            if not status_file:
                return False
            
            from datetime import datetime
            
            status = {
                "stopped": True,
                "stopped_at": datetime.now().isoformat(),
                "stopped_by": stopped_by,
                "message": message
            }
            
            # Ensure directory exists
            status_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error stopping chatbots: {str(e)}")
            return False
    
    def start_chatbots(self) -> bool:
        """Start all chatbots for the current user."""
        try:
            status_file = self.get_status_file_path()
            if not status_file:
                return False
            
            status = {
                "stopped": False,
                "stopped_at": None,
                "stopped_by": None,
                "message": None
            }
            
            # Ensure directory exists
            status_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error starting chatbots: {str(e)}")
            return False
    
    def is_chatbot_stopped(self) -> bool:
        """Check if chatbots are stopped for the current user."""
        status = self.get_chatbot_status()
        return status.get("stopped", False)
    
    def get_stop_message(self) -> str:
        """Get the stop message for the current user."""
        status = self.get_chatbot_status()
        return status.get("message", "Чатбот временно недоступен")

# Global instance
chatbot_status_manager = ChatbotStatusManager() 