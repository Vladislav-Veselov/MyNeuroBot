import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

class DialogueStorage:
    def __init__(self, storage_file: str = "dialogues.json"):
        """
        Initialize dialogue storage.
        
        Args:
            storage_file: JSON file to store all dialogue sessions
        """
        self.storage_file = Path(storage_file)
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Ensure the storage file exists with proper structure."""
        if not self.storage_file.exists():
            self._save_all_sessions({
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_sessions": 0
                },
                "sessions": {}
            })
    
    def _load_all_sessions(self) -> Dict[str, Any]:
        """Load all sessions from the storage file."""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {str(e)}")
            return {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_sessions": 0
                },
                "sessions": {}
            }
    
    def _save_all_sessions(self, data: Dict[str, Any]) -> None:
        """Save all sessions to the storage file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {str(e)}")
    
    def create_session(self) -> str:
        """
        Create a new dialogue session.
        
        Returns:
            Session ID (UUID string)
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "metadata": {
                "total_messages": 0,
                "last_updated": datetime.now().isoformat(),
                "unread": True,
                "potential_client": None
            }
        }
        
        # Load current data
        all_data = self._load_all_sessions()
        
        # Add new session
        all_data["sessions"][session_id] = session_data
        all_data["metadata"]["total_sessions"] = len(all_data["sessions"])
        all_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save updated data
        self._save_all_sessions(all_data)
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to an existing session.
        
        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_data = self._load_all_sessions()
            
            if session_id not in all_data["sessions"]:
                return False
            
            session_data = all_data["sessions"][session_id]
            
            message = {
                "id": str(uuid.uuid4()),
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            session_data["messages"].append(message)
            session_data["metadata"]["total_messages"] = len(session_data["messages"])
            session_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Mark session as unread when a new message is added
            session_data["metadata"]["unread"] = True
            
            # Reset potential client status to unknown when new message is added
            session_data["metadata"]["potential_client"] = None
            
            # Update global metadata
            all_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            self._save_all_sessions(all_data)
            return True
            
        except Exception as e:
            print(f"Error adding message to session {session_id}: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            all_data = self._load_all_sessions()
            return all_data["sessions"].get(session_id)
        except Exception as e:
            print(f"Error getting session {session_id}: {str(e)}")
            return None
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all dialogue sessions.
        
        Returns:
            List of session summaries
        """
        try:
            all_data = self._load_all_sessions()
            sessions = []
            
            for session_id, session_data in all_data["sessions"].items():
                # Return summary for each session
                summary = {
                    "session_id": session_data["session_id"],
                    "created_at": session_data["created_at"],
                    "total_messages": session_data["metadata"]["total_messages"],
                    "last_updated": session_data["metadata"]["last_updated"],
                    "first_message": session_data["messages"][0]["content"][:100] + "..." if session_data["messages"] else "No messages",
                    "unread": session_data["metadata"].get("unread", False),
                    "potential_client": session_data["metadata"].get("potential_client", None)
                }
                sessions.append(summary)
            
            # Sort by last updated (newest first)
            sessions.sort(key=lambda x: x["last_updated"], reverse=True)
            return sessions
            
        except Exception as e:
            print(f"Error loading sessions: {str(e)}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_data = self._load_all_sessions()
            
            if session_id in all_data["sessions"]:
                del all_data["sessions"][session_id]
                all_data["metadata"]["total_sessions"] = len(all_data["sessions"])
                all_data["metadata"]["last_updated"] = datetime.now().isoformat()
                
                self._save_all_sessions(all_data)
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def clear_all_sessions(self) -> bool:
        """
        Clear all dialogue sessions.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            all_data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_sessions": 0
                },
                "sessions": {}
            }
            self._save_all_sessions(all_data)
            return True
        except Exception as e:
            print(f"Error clearing all sessions: {str(e)}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            all_data = self._load_all_sessions()
            total_messages = sum(
                session["metadata"]["total_messages"] 
                for session in all_data["sessions"].values()
            )
            
            return {
                "total_sessions": all_data["metadata"]["total_sessions"],
                "total_messages": total_messages,
                "storage_created": all_data["metadata"]["created_at"],
                "last_updated": all_data["metadata"]["last_updated"],
                "file_size_mb": round(self.storage_file.stat().st_size / (1024 * 1024), 2) if self.storage_file.exists() else 0
            }
        except Exception as e:
            print(f"Error getting storage stats: {str(e)}")
            return {}

    def mark_session_as_read(self, session_id: str) -> bool:
        """
        Mark a session as read.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_data = self._load_all_sessions()
            
            if session_id in all_data["sessions"]:
                session_data = all_data["sessions"][session_id]
                session_data["metadata"]["unread"] = False
                session_data["metadata"]["last_updated"] = datetime.now().isoformat()
                
                # Update global metadata
                all_data["metadata"]["last_updated"] = datetime.now().isoformat()
                
                self._save_all_sessions(all_data)
                return True
            return False
            
        except Exception as e:
            print(f"Error marking session {session_id} as read: {str(e)}")
            return False

    def mark_session_as_potential_client(self, session_id: str, is_potential_client: bool = True) -> bool:
        """
        Mark a session as a potential client.
        
        Args:
            session_id: Session ID
            is_potential_client: Whether the session is a potential client (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_data = self._load_all_sessions()
            
            if session_id in all_data["sessions"]:
                session_data = all_data["sessions"][session_id]
                session_data["metadata"]["potential_client"] = is_potential_client
                session_data["metadata"]["last_updated"] = datetime.now().isoformat()
                
                # Update global metadata
                all_data["metadata"]["last_updated"] = datetime.now().isoformat()
                
                self._save_all_sessions(all_data)
                return True
            return False
            
        except Exception as e:
            print(f"Error marking session {session_id} as potential client: {str(e)}")
            return False

# Global instance
dialogue_storage = DialogueStorage(os.path.join(os.path.dirname(__file__), "dialogues.json")) 