#!/usr/bin/env python3
"""
Test script for potential client analysis functionality.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from app import analyze_unread_sessions_for_potential_clients
from dialogue_storage import dialogue_storage

def test_analysis():
    """Test the potential client analysis functionality."""
    print("Testing potential client analysis...")
    
    # Get current sessions
    sessions = dialogue_storage.get_all_sessions()
    print(f"Total sessions: {len(sessions)}")
    
    # Show unread sessions
    unread_sessions = [s for s in sessions if s.get('unread', False)]
    print(f"Unread sessions: {len(unread_sessions)}")
    
    for session in unread_sessions:
        print(f"  - Session {session['session_id'][:8]}... (potential_client: {session.get('potential_client')})")
    
    # Run analysis
    print("\nRunning analysis...")
    stats = analyze_unread_sessions_for_potential_clients()
    
    print(f"Analysis results:")
    print(f"  - Analyzed: {stats['analyzed']}")
    print(f"  - Potential clients: {stats['potential_clients']}")
    print(f"  - Not potential: {stats['not_potential']}")
    
    # Check results
    updated_sessions = dialogue_storage.get_all_sessions()
    for session in updated_sessions:
        if session.get('unread', False):
            print(f"  - Session {session['session_id'][:8]}... -> potential_client: {session.get('potential_client')}")

if __name__ == "__main__":
    test_analysis() 