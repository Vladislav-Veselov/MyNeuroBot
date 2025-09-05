import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

def get_moscow_time():
    """Get current Moscow time."""
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)

class DialogueStorage:
    def __init__(self, storage_file: str = "dialogues.json"):
        """
        Initialize dialogue storage.
        
        Args:
            storage_file: JSON file to store all dialogue sessions
        """
        self.storage_file = Path(storage_file)
        self._pending_sessions = {}  # Initialize pending sessions storage
        self._ensure_storage_file()
    
    def _ensure_storage_file(self):
        """Ensure the storage file exists with proper structure."""
        if not self.storage_file.exists():
            self._save_all_sessions({
                "metadata": {
                    "created_at": get_moscow_time().isoformat(),
                    "last_updated": get_moscow_time().isoformat(),
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
                    "created_at": get_moscow_time().isoformat(),
                    "last_updated": get_moscow_time().isoformat(),
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
    
    def create_session(self, ip_address: str = None, kb_id: str = None, kb_name: str = None) -> str:
        """
        Create a new dialogue session (pending - not stored until first message).
        
        Args:
            ip_address: IP address of the client (optional)
            kb_id: Knowledge base ID (optional)
            kb_name: Knowledge base name (optional)
            
        Returns:
            Session ID (UUID string)
        """
        # Clean up old pending sessions periodically
        self.cleanup_pending_sessions()
        
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "created_at": get_moscow_time().isoformat(),
            "messages": [],
            "metadata": {
                "total_messages": 0,
                "last_updated": get_moscow_time().isoformat(),
                "unread": True,
                "potential_client": None,
                "ip_address": ip_address,
                "kb_id": kb_id,
                "kb_name": kb_name,
                "pending": True  # Mark as pending until first message
            }
        }
        
        # Store the pending session temporarily (will be moved to main storage when first message is added)
        self._pending_sessions[session_id] = session_data
        
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
            
            # Check if session exists in main storage
            if session_id in all_data["sessions"]:
                session_data = all_data["sessions"][session_id]
            else:
                # Check if session exists in pending storage
                if session_id in self._pending_sessions:
                    # Move session from pending to main storage
                    session_data = self._pending_sessions[session_id]
                    session_data["metadata"]["pending"] = False
                    all_data["sessions"][session_id] = session_data
                    del self._pending_sessions[session_id]
                else:
                    return False
            
            message = {
                "id": str(uuid.uuid4()),
                "role": role,
                "content": content,
                "timestamp": get_moscow_time().isoformat()
            }
            
            session_data["messages"].append(message)
            session_data["metadata"]["total_messages"] = len(session_data["messages"])
            session_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
            
            # Mark session as unread when a new message is added
            session_data["metadata"]["unread"] = True
            
            # Reset potential client status to unknown when new message is added
            session_data["metadata"]["potential_client"] = None
            
            # Update global metadata
            all_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
            all_data["metadata"]["total_sessions"] = len(all_data["sessions"])
            
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
            
            # Check main storage first
            if session_id in all_data["sessions"]:
                return all_data["sessions"][session_id]
            
            # Check pending sessions
            if session_id in self._pending_sessions:
                return self._pending_sessions[session_id]
            
            return None
            
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
                    "potential_client": session_data["metadata"].get("potential_client", None),
                    "ip_address": session_data["metadata"].get("ip_address", None),
                    "kb_id": session_data["metadata"].get("kb_id", None),
                    "kb_name": session_data["metadata"].get("kb_name", None)
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
                all_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
                
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
                    "created_at": get_moscow_time().isoformat(),
                    "last_updated": get_moscow_time().isoformat(),
                    "total_sessions": 0
                },
                "sessions": {}
            }
            self._save_all_sessions(all_data)
            
            # Reset global instance to ensure fresh loading
            reset_dialogue_storage()
            
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
            
            # Count potential clients (sessions marked as "Лид!")
            potential_clients_count = sum(
                1 for session in all_data["sessions"].values()
                if session["metadata"].get("potential_client") is True
            )
            
            return {
                "total_sessions": all_data["metadata"]["total_sessions"],
                "total_messages": total_messages,
                "storage_created": all_data["metadata"]["created_at"],
                "last_updated": all_data["metadata"]["last_updated"],
                "potential_clients_count": potential_clients_count
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
                session_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
                
                # Update global metadata
                all_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
                
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
                session_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
                
                # Update global metadata
                all_data["metadata"]["last_updated"] = get_moscow_time().isoformat()
                
                self._save_all_sessions(all_data)
                return True
            return False
            
        except Exception as e:
            print(f"Error marking session {session_id} as potential client: {str(e)}")
            return False

    def get_session_by_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent session for a given IP address.
        
        Args:
            ip_address: IP address to search for
            
        Returns:
            Session data or None if not found
        """
        try:
            all_data = self._load_all_sessions()
            
            # Find sessions with matching IP address in main storage
            matching_sessions = []
            for session_id, session_data in all_data["sessions"].items():
                if session_data["metadata"].get("ip_address") == ip_address:
                    matching_sessions.append((session_id, session_data))
            
            # Check pending sessions
            for session_id, session_data in self._pending_sessions.items():
                if session_data["metadata"].get("ip_address") == ip_address:
                    matching_sessions.append((session_id, session_data))
            
            if not matching_sessions:
                return None
            
            # Return the most recent session (by last_updated)
            matching_sessions.sort(
                key=lambda x: x[1]["metadata"]["last_updated"], 
                reverse=True
            )
            return matching_sessions[0][1]
            
        except Exception as e:
            print(f"Error getting session by IP {ip_address}: {str(e)}")
            return None

    def cleanup_pending_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up pending sessions that are older than the specified age.
        
        Args:
            max_age_hours: Maximum age in hours for pending sessions
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            from datetime import datetime, timedelta
            
            if not self._pending_sessions:
                return 0
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            sessions_to_remove = []
            
            for session_id, session_data in self._pending_sessions.items():
                created_at = datetime.fromisoformat(session_data["created_at"])
                if created_at < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            # Remove old pending sessions
            for session_id in sessions_to_remove:
                del self._pending_sessions[session_id]
            
            if sessions_to_remove:
                print(f"Cleaned up {len(sessions_to_remove)} old pending sessions")
            
            return len(sessions_to_remove)
            
        except Exception as e:
            print(f"Error cleaning up pending sessions: {str(e)}")
            return 0

# Global instance - will be initialized per user
dialogue_storage = None
current_user = None

def reset_dialogue_storage():
    """Reset the global dialogue storage instance."""
    global dialogue_storage, current_user
    dialogue_storage = None
    current_user = None

def get_dialogue_storage():
    """Get the dialogue storage instance for the current user."""
    global dialogue_storage, current_user
    
    try:
        from auth import get_current_user_data_dir
        user_data_dir = get_current_user_data_dir()
        current_username = user_data_dir.name  # Get username from directory name
        
        # Reset global instance if user changed
        if current_user != current_username:
            dialogue_storage = None
            current_user = current_username
        
        if dialogue_storage is None:
            dialogues_file = user_data_dir / "dialogues.json"
            dialogue_storage = DialogueStorage(str(dialogues_file))
            
    except Exception as e:
        print(f"Error initializing dialogue storage: {str(e)}")
        # Fallback to admin directory
        admin_file = os.path.join(os.path.dirname(__file__), "..", "user_data", "admin", "dialogues.json")
        dialogue_storage = DialogueStorage(admin_file)
    
    return dialogue_storage 