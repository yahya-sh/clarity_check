import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

def get_user_sessions_dir(username: str) -> str:
    """Get the sessions directory for a user"""
    sessions_dir = f"data/instructors/{username}/sessions"
    os.makedirs(sessions_dir, exist_ok=True)
    return sessions_dir

def get_presentation_sessions_dir(username: str, presentation_uuid: str) -> str:
    """Get the sessions directory for a specific presentation"""
    user_sessions_dir = get_user_sessions_dir(username)
    presentation_sessions_dir = f"{user_sessions_dir}/{presentation_uuid}"
    os.makedirs(presentation_sessions_dir, exist_ok=True)
    return presentation_sessions_dir

def get_session_file_path(username: str, presentation_uuid: str, session_uuid: str) -> str:
    """Get the session file path"""
    presentation_sessions_dir = get_presentation_sessions_dir(username, presentation_uuid)
    return f"{presentation_sessions_dir}/{session_uuid}.json"

def create_session(session_uuid, username: str, presentation_uuid: str, participants: List[Dict] = None) -> Dict:
    """Create a new session and return session data"""
    created_at = datetime.now().isoformat()
    
    session_data = {
        'session_uuid': session_uuid,
        'presentation_uuid': presentation_uuid,
        'created_at': created_at,
        'status': 'active',
        'participants': participants if participants else []
    }
    
    # Save session to file
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    with open(session_file_path, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    return session_data

def load_session(username: str, presentation_uuid: str, session_uuid: str) -> Optional[Dict]:
    """Load session data from file"""
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    
    if not os.path.exists(session_file_path):
        return None
    
    try:
        with open(session_file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def update_session_participants(username: str, presentation_uuid: str, session_uuid: str, participants: List[Dict]) -> bool:
    """Update participants in a session"""
    session_data = load_session(username, presentation_uuid, session_uuid)
    if not session_data:
        return False
    
    session_data['participants'] = participants
    
    # Save updated session data
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    try:
        with open(session_file_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        return True
    except (OSError, IOError):
        return False

def get_all_sessions_for_presentation(username: str, presentation_uuid: str) -> List[Dict]:
    """Get all sessions for a presentation"""
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
                continue
    
    # Sort by created_at (newest first)
    sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return sessions

def get_all_sessions_for_user(username: str) -> List[Dict]:
    """Get all sessions for a user across all presentations"""
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
    """Delete a session file"""
    session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
    
    if os.path.exists(session_file_path):
        try:
            os.remove(session_file_path)
            return True
        except OSError:
            return False
    
    return False
