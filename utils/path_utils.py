"""
utils/path_utils.py — Path construction utilities.

Centralizes all file path construction logic to ensure consistency
and reduce hardcoded path strings throughout the application.
"""

import os
from typing import Optional

from config.constants import (
    DATA_DIR,
    INSTRUCTORS_DIR,
    PRESENTATIONS_DIR,
    RUNS_DIR,
    SESSIONS_DIR,
    JSON_EXTENSION
)


def get_data_dir() -> str:
    """Get the root data directory path."""
    return DATA_DIR


def get_instructors_dir() -> str:
    """Get the instructors directory path."""
    return INSTRUCTORS_DIR


def get_user_dir(username: str) -> str:
    """
    Get the directory path for a specific user.
    
    Args:
        username: Instructor username
        
    Returns:
        Path to user's directory
    """
    return os.path.join(INSTRUCTORS_DIR, username)


def get_user_presentations_dir(username: str) -> str:
    """
    Get the presentations directory for a specific user.
    
    Args:
        username: Instructor username
        
    Returns:
        Path to user's presentations directory
    """
    return os.path.join(get_user_dir(username), PRESENTATIONS_DIR)


def get_user_runs_dir(username: str) -> str:
    """
    Get the runs directory for a specific user.
    
    Args:
        username: Instructor username
        
    Returns:
        Path to user's runs directory
    """
    return os.path.join(get_user_dir(username), RUNS_DIR)


def get_user_sessions_dir(username: str) -> str:
    """
    Get the sessions directory for a specific user.
    
    Args:
        username: Instructor username
        
    Returns:
        Path to user's sessions directory
    """
    return os.path.join(get_user_dir(username), SESSIONS_DIR)


def get_presentation_sessions_dir(username: str, presentation_uuid: str) -> str:
    """
    Get the sessions directory for a specific presentation.
    
    Args:
        username: Instructor username
        presentation_uuid: UUID of the presentation
        
    Returns:
        Path to presentation's sessions directory
    """
    return os.path.join(get_user_sessions_dir(username), presentation_uuid)


def get_presentation_file_path(username: str, presentation_uuid: str) -> str:
    """
    Get the file path for a specific presentation.
    
    Args:
        username: Instructor username
        presentation_uuid: UUID of the presentation
        
    Returns:
        Path to presentation JSON file
    """
    filename = f"{presentation_uuid}{JSON_EXTENSION}"
    return os.path.join(get_user_presentations_dir(username), filename)


def get_run_file_path(username: str, presentation_uuid: str, pin_code: str) -> str:
    """
    Get the file path for a specific run.
    
    Args:
        username: Instructor username
        presentation_uuid: UUID of the presentation
        pin_code: PIN code for the run
        
    Returns:
        Path to run JSON file
    """
    filename = f"{presentation_uuid}_{pin_code}{JSON_EXTENSION}"
    return os.path.join(get_user_runs_dir(username), filename)


def get_session_file_path(username: str, presentation_uuid: str, session_uuid: str) -> str:
    """
    Get the file path for a specific session.
    
    Args:
        username: Instructor username
        presentation_uuid: UUID of the presentation
        session_uuid: UUID of the session
        
    Returns:
        Path to session JSON file
    """
    filename = f"{session_uuid}{JSON_EXTENSION}"
    return os.path.join(get_presentation_sessions_dir(username, presentation_uuid), filename)


def get_user_file_path(username: str) -> str:
    """
    Get the file path for a user's data.
    
    Args:
        username: Instructor username
        
    Returns:
        Path to user JSON file
    """
    filename = f"{username}{JSON_EXTENSION}"
    return os.path.join(get_user_dir(username), filename)


def extract_username_from_path(file_path: str) -> Optional[str]:
    """
    Extract username from a file path.
    
    Args:
        file_path: Full file path
        
    Returns:
        Username if found, None otherwise
    """
    path_parts = file_path.split(os.sep)
    
    # Look for 'instructors' in the path and get the next part
    try:
        instructors_index = path_parts.index('instructors')
        if instructors_index + 1 < len(path_parts):
            return path_parts[instructors_index + 1]
    except (ValueError, IndexError):
        pass
    
    return None


def extract_presentation_uuid_from_run_path(file_path: str) -> Optional[str]:
    """
    Extract presentation UUID from a run file path.
    
    Args:
        file_path: Full run file path
        
    Returns:
        Presentation UUID if found, None otherwise
    """
    filename = os.path.basename(file_path)
    if filename.endswith(JSON_EXTENSION):
        # Format: {presentation_uuid}_{pin}.json
        base_name = filename[:-len(JSON_EXTENSION)]
        parts = base_name.split('_')
        if len(parts) >= 2:
            return parts[0]
    
    return None


def extract_session_uuid_from_path(file_path: str) -> Optional[str]:
    """
    Extract session UUID from a session file path.
    
    Args:
        file_path: Full session file path
        
    Returns:
        Session UUID if found, None otherwise
    """
    filename = os.path.basename(file_path)
    if filename.endswith(JSON_EXTENSION):
        return filename[:-len(JSON_EXTENSION)]
    
    return None


def is_presentation_file_path(file_path: str) -> bool:
    """
    Check if a path is a presentation file path.
    
    Args:
        file_path: File path to check
        
    Returns:
        True if it's a presentation file path
    """
    return (PRESENTATIONS_DIR in file_path and 
            file_path.endswith(JSON_EXTENSION))


def is_run_file_path(file_path: str) -> bool:
    """
    Check if a path is a run file path.
    
    Args:
        file_path: File path to check
        
    Returns:
        True if it's a run file path
    """
    return (RUNS_DIR in file_path and 
            file_path.endswith(JSON_EXTENSION) and
            '_' in os.path.basename(file_path))


def is_session_file_path(file_path: str) -> bool:
    """
    Check if a path is a session file path.
    
    Args:
        file_path: File path to check
        
    Returns:
        True if it's a session file path
    """
    return (SESSIONS_DIR in file_path and 
            file_path.endswith(JSON_EXTENSION))
