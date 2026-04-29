"""
services/session_service.py — Session management service.

Handles all business logic related to session lifecycle, participant
management, and session status transitions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from repositories.sessions import (
    create_session,
    load_session,
    update_session_participants,
    delete_session,
    get_all_sessions_for_presentation,
    get_all_sessions_for_user
)
from repositories import runs_repo
from repositories.base import NotFoundError, ValidationError
from models.participant import Participant
from config.constants import STATUS_ACTIVE


class SessionService:
    """
    Service class for session business logic.
    
    Centralizes all session-related operations including creation,
    participant management, and status tracking.
    """
    
    @staticmethod
    def create_active_session(
        session_uuid: str,
        username: str,
        presentation_uuid: str,
        participants: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new active session.
        
        Args:
            session_uuid: UUID for the new session
            username: Instructor username
            presentation_uuid: UUID of the presentation
            participants: Initial participant list
            
        Returns:
            Created session data
            
        Raises:
            ValidationError: If session data is invalid
        """
        if not session_uuid:
            raise ValidationError("Session UUID is required")
        
        if not username:
            raise ValidationError("Username is required")
        
        if not presentation_uuid:
            raise ValidationError("Presentation UUID is required")
        
        # Ensure participants is a list
        participants = participants or []
        
        # Create session
        session_data = create_session(
            session_uuid=session_uuid,
            username=username,
            presentation_uuid=presentation_uuid,
            participants=participants
        )
        
        return session_data
    
    @staticmethod
    def get_session(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> Dict[str, Any]:
        """
        Get session data with validation.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Session data dictionary
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        
        if not session_data:
            raise NotFoundError("Session not found")
        
        return session_data
    
    @staticmethod
    def is_session_active(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> bool:
        """
        Check if a session is active.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            True if session is active, False otherwise
        """
        try:
            session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
            return session_data.get('status') == STATUS_ACTIVE
        except NotFoundError:
            return False
    
    @staticmethod
    def add_participant_to_session(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        participant: Participant
    ) -> Dict[str, Any]:
        """
        Add a participant to an existing session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            participant: Participant to add
            
        Returns:
            Updated session data
            
        Raises:
            NotFoundError: If session not found
            ValidationError: If participant data is invalid
        """
        # Validate participant
        if not participant.uuid:
            raise ValidationError("Participant UUID is required")
        
        if not participant.nickname:
            raise ValidationError("Participant nickname is required")
        
        # Get current session
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Add participant to session
        participants = session_data.get('participants', [])
        if not isinstance(participants, list):
            participants = []
        
        # Check if participant already exists
        existing_participant = next(
            (p for p in participants if p.get('uuid') == participant.uuid),
            None
        )
        
        if existing_participant:
            # Update existing participant
            existing_participant.update(participant.to_dict())
        else:
            # Add new participant
            participants.append(participant.to_dict())
        
        # Update session
        success = update_session_participants(username, presentation_uuid, session_uuid, participants)
        
        if not success:
            raise ValidationError("Failed to update session participants")
        
        # Return updated session data
        return SessionService.get_session(username, presentation_uuid, session_uuid)
    
    @staticmethod
    def remove_participant_from_session(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        participant_uuid: str
    ) -> Dict[str, Any]:
        """
        Remove a participant from an existing session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            participant_uuid: UUID of the participant to remove
            
        Returns:
            Updated session data
            
        Raises:
            NotFoundError: If session or participant not found
        """
        # Get current session
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Find and remove participant
        participants = session_data.get('participants', [])
        if not isinstance(participants, list):
            participants = []
        
        # Filter out the participant
        filtered_participants = [
            p for p in participants if p.get('uuid') != participant_uuid
        ]
        
        # Check if participant was found and removed
        if len(filtered_participants) == len(participants):
            raise NotFoundError("Participant not found in session")
        
        # Update session
        success = update_session_participants(
            username, presentation_uuid, session_uuid, filtered_participants
        )
        
        if not success:
            raise ValidationError("Failed to update session participants")
        
        # Return updated session data
        return SessionService.get_session(username, presentation_uuid, session_uuid)
    
    @staticmethod
    def get_session_participants(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> List[Dict[str, Any]]:
        """
        Get all participants in a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            List of participant dictionaries
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        return session_data.get('participants', [])
    
    @staticmethod
    def get_participant_count(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> int:
        """
        Get the number of participants in a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Number of participants
            
        Raises:
            NotFoundError: If session not found
        """
        participants = SessionService.get_session_participants(
            username, presentation_uuid, session_uuid
        )
        return len(participants)
    
    @staticmethod
    def list_presentation_sessions(username: str, presentation_uuid: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a presentation.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            
        Returns:
            List of session data dictionaries
        """
        return get_all_sessions_for_presentation(username, presentation_uuid)
    
    @staticmethod
    def list_user_sessions(username: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user across all presentations.
        
        Args:
            username: Instructor username
            
        Returns:
            List of session data dictionaries
        """
        return get_all_sessions_for_user(username)
    
    @staticmethod
    def delete_session(username: str, presentation_uuid: str, session_uuid: str) -> bool:
        """
        Delete a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            True if deleted, False if not found
        """
        return delete_session(username, presentation_uuid, session_uuid)
    
    @staticmethod
    def validate_participant_access(
        participant_uuid: str,
        session_uuid: str,
        presentation_uuid: str,
        username: str
    ) -> bool:
        """
        Validate that a participant has access to a session.
        
        Args:
            participant_uuid: UUID of the participant
            session_uuid: UUID of the session
            presentation_uuid: UUID of the presentation
            username: Instructor username
            
        Returns:
            True if participant has access, False otherwise
        """
        try:
            session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
            participants = session_data.get('participants', [])
            
            return any(
                p.get('uuid') == participant_uuid
                for p in participants
            )
        except NotFoundError:
            return False
    
    @staticmethod
    def get_session_statistics(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Dictionary containing session statistics
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        participants = session_data.get('participants', [])
        
        return {
            'participant_count': len(participants),
            'session_uuid': session_uuid,
            'presentation_uuid': presentation_uuid,
            'status': session_data.get('status'),
            'created_at': session_data.get('created_at'),
            'participants': participants
        }
    
    @staticmethod
    def move_run_to_session(username: str, presentation_uuid: str) -> Dict[str, Any]:
        """
        Move data from run stage to session stage.
        
        Creates a session from run data and deletes the run file.
        This function encapsulates the complete workflow of transitioning
        from the run phase (PIN-based participant collection) to the
        active session phase.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            
        Returns:
            Session data dictionary with session_uuid, presentation_uuid,
            username, created_at, status, and participants
            
        Raises:
            NotFoundError: If run data not found
            ValidationError: If session creation fails or required data missing
        """
        # Load run data
        run_data = runs_repo.load_run_data(username, presentation_uuid)
        if not run_data:
            raise NotFoundError("No active run found for this presentation")
        
        # Extract required properties from run data
        session_uuid = run_data.get('session_uuid')
        if not session_uuid:
            raise ValidationError("No session UUID found in run data")
        
        run_username = run_data.get('username', username)
        participants = run_data.get('participants', [])
        
        # Create session with run data properties
        session_data = SessionService.create_active_session(
            session_uuid=session_uuid,
            username=run_username,
            presentation_uuid=presentation_uuid,
            participants=participants
        )
        
        # Delete run file after successful session creation
        try:
            runs_repo.delete_run_data(username, presentation_uuid)
        except Exception as e:
            # Log the error but don't fail the session creation
            # The session was successfully created, so we continue
            print(f"Warning: Failed to delete run data file after session creation: {str(e)}")
        
        return session_data
