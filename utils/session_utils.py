"""
utils/session_utils.py — Session management utilities.

Provides centralized session validation and management functionality
for both instructor and participant sessions.
"""

from typing import Optional, Dict, Any
from flask import session, g, flash, redirect, url_for
from config.constants import (
    PARTICIPANT_SESSION_KEYS,
    FLASH_ERROR,
    FLASH_INFO,
    ERROR_SESSION_NOT_FOUND,
    SESSION_DONE
)
from repositories import users_repo
from repositories.sessions import load_session
from repositories.runs import load_run_data
from models.participant import Participant


class SessionValidationError(Exception):
    """Raised when session validation fails."""
    pass


def validate_instructor_session() -> Optional[str]:
    """
    Validate instructor session and return error message if invalid.
    
    Returns:
        Error message if validation fails, None if valid
        
    Raises:
        SessionValidationError: If session is invalid
    """
    username = session.get('username')
    if not username:
        raise SessionValidationError("Please log in to access this page")
    
    # Verify the user record still exists (handles deleted accounts)
    user = users_repo.get_user(username)
    if not user:
        g.user = None
        session.clear()
        raise SessionValidationError("User not found. Please log in again.")
    
    return None


def check_participant_in_run_file(instructor_username: str, presentation_uuid: str, participant_uuid: str) -> bool:
    """
    Check if participant exists in the run file.
    
    Args:
        instructor_username: Username of the session instructor
        presentation_uuid: UUID of the presentation
        participant_uuid: UUID of the participant to check
        
    Returns:
        True if participant exists in run file, False otherwise
    """
    try:
        run_data = load_run_data(instructor_username, presentation_uuid)
        if not run_data:
            return False
        
        # Check if participant exists in run's participants list
        return any(
            p.get('uuid') == participant_uuid
            for p in run_data.get('participants', [])
        )
    except Exception:
        return False


def validate_participant_session() -> Optional[str]:
    """
    Validate participant session and return error message if invalid.
    
    Returns:
        Error message if validation fails, None if valid
        
    Raises:
        SessionValidationError: If session is invalid
    """
    # Check all required session keys are present
    session_data = {
        'participant_uuid': session.get('participant_uuid'),
        'participant_session_uuid': session.get('participant_session_uuid'),
        'participant_nickname': session.get('participant_nickname'),
        'presentation_uuid': session.get('presentation_uuid'),
        'presentation_instructor_username': session.get('presentation_instructor_username'),
    }
    
    missing_keys = [key for key, value in session_data.items() if not value]
    if missing_keys:
        raise SessionValidationError("Please join a session to access this page")
    
    # First try to validate against run file (join phase)
    participant_in_run = check_participant_in_run_file(
        session_data['presentation_instructor_username'],
        session_data['presentation_uuid'],
        session_data['participant_uuid']
    )
    
    if participant_in_run:
        # Participant is in run file, this is valid for join phase
        return None
    
    # If not found in run file, try session file (active session phase)
    try:
        session_file_data = load_session(
            session_data['presentation_instructor_username'],
            session_data['presentation_uuid'],
            session_data['participant_session_uuid'],
        )
        if not session_file_data:
            raise Exception
    except Exception:
        raise SessionValidationError("Session not found. Please join a session again.")
        
    # Check if participant exists in session
    participant_exists = any(
        p.get('uuid') == session_data['participant_uuid']
        for p in session_file_data.get('participants', [])
    )
    
    if not participant_exists:
        session.clear()
        raise SessionValidationError("Session not found. Please join a session again.")
    

    
    return None


def populate_participant_in_context() -> None:
    """
    Populate g.participant with participant data from session.
    
    This function should be called before each request to ensure
    g.participant is available for route handlers and templates.
    """
    session_data = {
        'participant_uuid': session.get('participant_uuid'),
        'participant_session_uuid': session.get('participant_session_uuid'),
        'participant_nickname': session.get('participant_nickname'),
        'presentation_uuid': session.get('presentation_uuid'),
        'presentation_instructor_username': session.get('presentation_instructor_username'),
    }
    
    if all(session_data.values()):
        g.participant = Participant(
            session_uuid=session_data['participant_session_uuid'],
            nickname=session_data['participant_nickname'],
            presentation_uuid=session_data['presentation_uuid'],
            presentation_instructor_username=session_data['presentation_instructor_username'],
            participant_uuid=session_data['participant_uuid'],
        )
    else:
        g.participant = None


def populate_user_in_context() -> None:
    """
    Populate g.user with user data from session.
    
    This function should be called before each request to ensure
    g.user is available for route handlers and templates.
    """
    username = session.get('username')
    g.user = users_repo.get_user(username) if username else None


def clear_participant_session() -> None:
    """Clear participant session data."""
    for key in PARTICIPANT_SESSION_KEYS:
        session.pop(key, None)


def set_participant_session(participant_data: Dict[str, str]) -> None:
    """
    Set participant session data from dictionary.
    
    Args:
        participant_data: Dictionary containing participant session keys
    """
    for key in PARTICIPANT_SESSION_KEYS:
        if key in participant_data:
            session[key] = participant_data[key]
    
    session.permanent = True


def get_session_error_response(error_message: str, redirect_endpoint: str):
    """
    Generate standardized error response for session validation failures.
    
    Args:
        error_message: Error message to display to user
        redirect_endpoint: Flask endpoint to redirect to
        
    Returns:
        Flask response tuple (redirect response)
    """
    flash(error_message, FLASH_ERROR if "not found" in error_message.lower() else FLASH_INFO)
    return redirect(url_for(redirect_endpoint))


