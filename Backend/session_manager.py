#!/usr/bin/env python3
"""
Session manager for IP-based session tracking.
"""

import hashlib
from typing import Dict, Any, Optional
from flask import request
from datetime import datetime

class IPSessionManager:
    def __init__(self):
        self.ip_sessions: Dict[str, str] = {}  # IP -> Session ID mapping
    
    def get_client_ip(self) -> str:
        """Get the client's IP address."""
        # Check for forwarded headers (for proxy/load balancer setups)
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    def get_ip_hash(self, ip: str) -> str:
        """Create a hash of the IP address for consistent identification."""
        return hashlib.md5(ip.encode()).hexdigest()[:16]
    
    def get_session_id_for_ip(self, ip: str) -> Optional[str]:
        """Get the session ID for a given IP address."""
        ip_hash = self.get_ip_hash(ip)
        return self.ip_sessions.get(ip_hash)
    
    def set_session_id_for_ip(self, ip: str, session_id: str) -> None:
        """Set the session ID for a given IP address."""
        ip_hash = self.get_ip_hash(ip)
        self.ip_sessions[ip_hash] = session_id
    
    def clear_session_for_ip(self, ip: str) -> None:
        """Clear the session for a given IP address."""
        ip_hash = self.get_ip_hash(ip)
        if ip_hash in self.ip_sessions:
            del self.ip_sessions[ip_hash]
    
    def get_current_ip_session_id(self) -> Optional[str]:
        """Get the session ID for the current request's IP address."""
        ip = self.get_client_ip()
        return self.get_session_id_for_ip(ip)
    
    def set_current_ip_session_id(self, session_id: str) -> None:
        """Set the session ID for the current request's IP address."""
        ip = self.get_client_ip()
        self.set_session_id_for_ip(ip, session_id)
    
    def clear_current_ip_session(self) -> None:
        """Clear the session for the current request's IP address."""
        ip = self.get_client_ip()
        self.clear_session_for_ip(ip)

# Global session manager instance
ip_session_manager = IPSessionManager() 