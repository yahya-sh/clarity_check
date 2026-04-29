"""
services/live_session_service.py — Live session management service.

Handles business logic for live session operations including question
navigation, timing management, and session flow control.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from repositories.sessions import load_session
from repositories.base import NotFoundError, ValidationError
from utils.file_utils import write_json_file
from utils.path_utils import get_session_file_path


class LiveSessionService:
    """
    Service class for live session business logic.
    
    Handles question navigation, timing, and session flow management
    for active presentation sessions.
    """
    
    @staticmethod
    def move_to_next_question(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> Dict[str, Any]:
        """
        Move to the next question in the session sequence.
        
        Updates the current_question_uuid to the next question from the
        shuffled array and calculates new start_time and end_time based
        on the question's time_limit.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Updated session data dictionary
            
        Raises:
            NotFoundError: If session not found
            ValidationError: If no more questions available
        """
        # Load current session data
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            raise NotFoundError("Session not found")
        
        # Get current question sequence and current question
        shuffled_question_uuids = session_data.get('shuffled_question_uuids', [])
        current_question_uuid = session_data.get('current_question_uuid')
        
        if not shuffled_question_uuids:
            raise ValidationError("No questions available in session")
        
        # Find current question index
        current_index = -1
        if current_question_uuid:
            try:
                current_index = shuffled_question_uuids.index(current_question_uuid)
            except ValueError:
                # Current question not found in sequence, start from beginning
                current_index = -1
        
        # Move to next question
        next_index = current_index + 1
        if next_index >= len(shuffled_question_uuids):
            raise ValidationError("No more questions available")
        
        next_question_uuid = shuffled_question_uuids[next_index]
        
        # Get next question data for timing
        questions = session_data.get('questions', {})
        next_question = questions.get(next_question_uuid)
        
        if not next_question:
            raise ValidationError(f"Question {next_question_uuid} not found in session data")
        
        # Calculate new timing
        time_limit = next_question.get('time_limit', 30)  # Default 30 seconds
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=time_limit)
        
        # Update session data
        session_data.update({
            'current_question_uuid': next_question_uuid,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        })
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        write_json_file(session_file_path, session_data)
        
        return session_data
    
    @staticmethod
    def get_current_question(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current question data for a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Current question data dictionary or None if no current question
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            raise NotFoundError("Session not found")
        
        current_question_uuid = session_data.get('current_question_uuid')
        if not current_question_uuid:
            return None
        
        questions = session_data.get('questions', {})
        return questions.get(current_question_uuid)
    
    @staticmethod
    def get_session_timing(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> Dict[str, Any]:
        """
        Get current timing information for the session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Dictionary containing timing information
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            raise NotFoundError("Session not found")
        
        start_time_str = session_data.get('start_time')
        end_time_str = session_data.get('end_time')
        
        timing_info = {
            'current_question_uuid': session_data.get('current_question_uuid'),
            'start_time': start_time_str,
            'end_time': end_time_str,
            'time_remaining': None
        }
        
        if start_time_str and end_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
                now = datetime.now()
                
                if now < end_time:
                    timing_info['time_remaining'] = (end_time - now).total_seconds()
                else:
                    timing_info['time_remaining'] = 0
            except (ValueError, TypeError):
                # Invalid datetime format, ignore timing calculation
                pass
        
        return timing_info
    
    @staticmethod
    def is_question_time_expired(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> bool:
        """
        Check if the current question time has expired.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            True if time expired, False otherwise
            
        Raises:
            NotFoundError: If session not found
        """
        timing_info = LiveSessionService.get_session_timing(
            username, presentation_uuid, session_uuid
        )
        
        time_remaining = timing_info.get('time_remaining')
        return time_remaining is not None and time_remaining <= 0
