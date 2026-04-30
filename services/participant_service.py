"""
services/participant_service.py — Participant session management service.

Handles all participant-related business logic including joining sessions,
session status checking, and participant data management. Extracted from
main routes to improve separation of concerns and testability.
"""

from typing import Dict, Any, Optional, Tuple

from repositories.runs import get_unexpired_run_by_pin, join_participant
from repositories.sessions import load_session
from repositories.base import NotFoundError
from models.participant import Participant
from config.constants import FLASH_ERROR


class ParticipantService:
    """
    Service class for participant business logic.
    
    Centralizes all participant operations including session joining,
    status validation, and participant management.
    """
    
    @staticmethod
    def join_session_run(pin: str, nickname: str) -> Tuple[bool, Optional[str], Optional[Participant], Optional[Dict[str, Any]]]:
        """
        Join a participant to a session run using PIN and nickname.
        
        Args:
            pin: The PIN code for the session
            nickname: The participant's display name
            
        Returns:
            Tuple of (success, error_message, participant, run_data)
            - success: True if join succeeded
            - error_message: Error message if failed, None if succeeded
            - participant: Participant instance if succeeded, None if failed
            - run_data: Run data dictionary if succeeded, None if failed
        """
        if not pin or not pin.strip():
            return False, "PIN is required", None, None
        
        if not nickname or not nickname.strip():
            return False, "Nickname is required", None, None
        
        pin = pin.strip()
        nickname = nickname.strip()
        
        run = get_unexpired_run_by_pin(pin)
        if not run:
            return False, "Presentation not found with this PIN", None, None
        
        participant = join_participant(run, nickname)
        
        return True, None, participant, run
    
    @staticmethod
    def prepare_participant_session_data(participant: Participant, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare session data for a joined participant.
        
        Args:
            participant: The participant instance
            run_data: The run data dictionary
            
        Returns:
            Dictionary with session data to be stored in Flask session
        """
        return {
            'participant_uuid': participant.uuid,
            'participant_session_uuid': participant.session_uuid,
            'participant_nickname': participant.nickname,
            'presentation_uuid': run_data['presentation_uuid'],
            'presentation_instructor_username': run_data['username'],
            'permanent': True
        }
    
    @staticmethod
    def check_session_status(instructor_username: str, presentation_uuid: str, session_uuid: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check the status of a participant's session.
        
        Args:
            instructor_username: Username of the session instructor
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Tuple of (success, error_message, session_data)
            - success: True if status check succeeded
            - error_message: Error message if failed, None if succeeded
            - session_data: Session data dictionary if succeeded, None if failed
        """
        try:
            session_data = load_session(instructor_username, presentation_uuid, session_uuid)
            
            if not session_data:
                return False, "Session not found", None
            
            return True, None, session_data
            
        except Exception as e:
            return False, f"Failed to check session status: {str(e)}", None
    
    @staticmethod
    def format_session_status_response(session_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format the response for session status API endpoint.
        
        Args:
            session_data: Session data dictionary or None
            
        Returns:
            Response dictionary suitable for JSON API
        """
        if not session_data:
            return {
                'success': False,
                'status': 'error',
                'message': 'Session not found'
            }
        
        if session_data.get('status') == 'active':
            return {
                'success': True,
                'status': 'active'
            }
        else:
            return {
                'success': False,
                'status': 'waiting'
            }
    
    @staticmethod
    def get_session_for_participant(instructor_username: str, presentation_uuid: str, session_uuid: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Get session data for a participant.
        
        First tries to get data from run file (join phase), then from session file (active session phase).
        
        Args:
            instructor_username: Username of the session instructor
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Tuple of (success, error_message, session_data)
            - success: True if session found
            - error_message: Error message if failed, None if succeeded
            - session_data: Session data dictionary if succeeded, None if failed
        """
        # First try to get data from run file (join phase)
        from repositories.runs import load_run_data
        try:
            run_data = load_run_data(instructor_username, presentation_uuid)
            if run_data:
                # Create session-like data structure from run data
                return True, None, {
                    'session_uuid': run_data['session_uuid'],
                    'presentation_uuid': run_data['presentation_uuid'],
                    'status': 'waiting',  # Run phase is waiting for instructor to start session
                    'participants': run_data.get('participants', []),
                    'created_at': run_data.get('created_at'),
                    'is_run_phase': True  # Flag to indicate this is run phase data
                }
        except Exception:
            pass
        
        # If not found in run file, try session file (active session phase)
        return ParticipantService.check_session_status(instructor_username, presentation_uuid, session_uuid)
    
    @staticmethod
    def get_join_success_redirect_url(session_uuid: str) -> str:
        """
        Get the redirect URL after successful session join.
        
        Args:
            session_uuid: UUID of the joined session
            
        Returns:
            URL string for redirect
        """
        return f"/session/{session_uuid}"
    


    @staticmethod
    def get_join_failure_flash_message() -> str:
        """Get the flash message for join failures."""
        return "Presentation not found with this PIN."
    
