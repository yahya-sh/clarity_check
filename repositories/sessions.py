"""
repositories/sessions.py — Live session data repository.

Handles all CRUD operations for live session data including
participant answers, timing information, and session state management.
Provides file-based storage with standardized error handling.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from utils.path_utils import (
    get_user_sessions_dir,
    get_presentation_sessions_dir,
    get_session_file_path,
)
from utils.file_utils import read_json_file, write_json_file, delete_file, FileOperationError


def create_session(session_uuid, username: str, presentation_uuid: str, participants: List[Dict] = None) -> Dict:
    """
    Create a new live session with initial participants.
    
    Args:
        session_uuid: Unique identifier for the new session
        username: Instructor username who owns the session
        presentation_uuid: UUID of the presentation being sessioned
        participants: Initial list of participant dictionaries (optional)
        
    Returns:
        Created session data dictionary with all required fields
    """
    created_at = datetime.now().isoformat()

    # Reappend session uuid to participants for consistency
    if participants:
        for participant in participants:
            participant['session_uuid'] = session_uuid
    
    session_data = {
        'session_uuid': session_uuid,
        'presentation_uuid': presentation_uuid,
        'username': username,
        'created_at': created_at,
        'status': 'active',
        'participants': participants if participants else []
    }
    
    # Save session to file
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    write_json_file(session_file_path, session_data)
    
    return session_data

def load_session(username: str, presentation_uuid: str, session_uuid: str) -> Optional[Dict]:
    """
    Load session data from file storage.
    
    Args:
        username: Instructor username who owns the session
        presentation_uuid: UUID of the presentation
        session_uuid: UUID of the session to load
        
    Returns:
        Session data dictionary if found and readable, None if file doesn't exist or is corrupted
    """
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    try:
        return read_json_file(session_file_path)
    except FileOperationError:
        return None

def update_session_participants(username: str, presentation_uuid: str, session_uuid: str, participants: List[Dict]) -> bool:
    """
    Update the participants list in an existing session.
    
    Args:
        username: Instructor username who owns the session
        presentation_uuid: UUID of the presentation
        session_uuid: UUID of the session to update
        participants: New list of participant dictionaries
        
    Returns:
        True if update succeeded, False if session not found or file operation failed
    """
    session_data = load_session(username, presentation_uuid, session_uuid)
    if not session_data:
        return False
    
    session_data['participants'] = participants
    
    # Save updated session data
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    try:
        write_json_file(session_file_path, session_data)
        return True
    except FileOperationError:
        return False

def get_all_sessions_for_presentation(username: str, presentation_uuid: str) -> List[Dict]:
    """
    Get all session data for a specific presentation.
    
    Args:
        username: Instructor username who owns the presentation
        presentation_uuid: UUID of the presentation
        
    Returns:
        List of session data dictionaries sorted by creation date (newest first)
    """
    presentation_sessions_dir = get_presentation_sessions_dir(username, presentation_uuid)
    sessions = []
    
    if not os.path.exists(presentation_sessions_dir):
        return sessions
    
    for filename in os.listdir(presentation_sessions_dir):
        if filename.endswith('.json'):
            try:
                session_uuid = filename[:-5]  # Remove .json
                session_data = load_session(username, presentation_uuid, session_uuid)
                if session_data:
                    sessions.append(session_data)
            except (json.JSONDecodeError, FileNotFoundError):
                continue  # Skip corrupted or missing session files
    
    # Sort by created_at (newest first)
    sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return sessions

def get_all_sessions_for_user(username: str) -> List[Dict]:
    """
    Get all session data for a user across all their presentations.
    
    Args:
        username: Instructor username
        
    Returns:
        List of all session data dictionaries sorted by creation date (newest first)
    """
    user_sessions_dir = get_user_sessions_dir(username)
    all_sessions = []
    
    if not os.path.exists(user_sessions_dir):
        return all_sessions
    
    # Iterate through all presentation directories
    for presentation_uuid in os.listdir(user_sessions_dir):
        presentation_path = os.path.join(user_sessions_dir, presentation_uuid)
        if os.path.isdir(presentation_path):
            sessions = get_all_sessions_for_presentation(username, presentation_uuid)
            all_sessions.extend(sessions)
    
    # Sort by created_at (newest first)
    all_sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_sessions

def delete_session(username: str, presentation_uuid: str, session_uuid: str) -> bool:
    """
    Delete a session file from storage.
    
    Args:
        username: Instructor username who owns the session
        presentation_uuid: UUID of the presentation
        session_uuid: UUID of the session to delete
        
    Returns:
        True if session file was found and deleted, False otherwise
    """
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    return delete_file(session_file_path)
