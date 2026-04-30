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
from repositories import runs_repo, presentations_repo
from repositories.base import NotFoundError, ValidationError
from models.participant import Participant
from config.constants import SESSION_ACTIVE
import random
from datetime import datetime, timedelta

from utils.path_utils import get_session_file_path


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
    def get_session_status(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> Optional[str]:
        """
        Get the status of a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Session status string or None if session not found
        """
        try:
            session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
            return session_data.get('status')
        except NotFoundError:
            return None
    
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
        status = SessionService.get_session_status(username, presentation_uuid, session_uuid)
        return status == SESSION_ACTIVE
    
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
        except Exception:
            # The session was successfully created, so we continue
            pass
        return session_data
    
    @staticmethod
    def init_session(username: str, presentation_uuid: str, session_uuid: str) -> Dict[str, Any]:
        """
        Initialize session with objectives, questions, and question sequencing.
        
        Fetches all objectives and questions from the related presentation,
        stores them as key-value pairs with parent references, creates shuffled
        question sequence, and sets up current question timing.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Updated session data dictionary
            
        Raises:
            NotFoundError: If presentation or session not found
            ValidationError: If required data is missing
        """
        # Load presentation data
        presentation = presentations_repo.load_presentation(username, presentation_uuid)
        if not presentation:
            raise NotFoundError("Presentation not found")
        
        # Load current session data
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Process objectives into key-value pairs (without questions array)
        objectives_dict = {}
        for objective in presentation.objectives:
            objective_id = objective.get('objective_id')
            if objective_id:
                # Create a copy of objective without questions array
                objective_clean = objective.copy()
                objective_clean.pop('questions', None)
                objectives_dict[objective_id] = objective_clean
        
        # Process questions into key-value pairs with parent objective references
        questions_dict = {}
        question_uuids = []
        
        for objective in presentation.objectives:
            objective_id = objective.get('objective_id')
            questions = objective.get('questions', [])
            
            for question in questions:
                question_id = question.get('question_id')
                if question_id:
                    # Add parent objective reference to question
                    question_with_parent = question.copy()
                    question_with_parent['parent_objective_id'] = objective_id
                    
                    questions_dict[question_id] = question_with_parent
                    question_uuids.append(question_id)
        
        # Create shuffled array of question UUIDs
        shuffled_question_uuids = question_uuids.copy()
        random.shuffle(shuffled_question_uuids)
        
        # Set initial current question and timing
        current_question_uuid = None
        start_time = None
        end_time = None
        
        if shuffled_question_uuids:
            current_question_uuid = shuffled_question_uuids[0]
            first_question = questions_dict.get(current_question_uuid)
            if first_question:
                time_limit = first_question.get('time_limit', 30)
                start_time = datetime.now().isoformat()
                end_time = (datetime.now() + timedelta(seconds=time_limit)).isoformat()
        
        # Update session data with new properties
        session_data.update({
            'objectives': objectives_dict,
            'questions': questions_dict,
            'shuffled_question_uuids': shuffled_question_uuids,
            'current_question_uuid': current_question_uuid,
            'start_time': start_time,
            'end_time': end_time
        })
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        from utils.file_utils import write_json_file
        write_json_file(session_file_path, session_data)
        
        return session_data
    
    @staticmethod
    def set_status(username: str, presentation_uuid: str, session_uuid: str, status: str) -> Dict[str, Any]:
        """
        Set the status of a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            status: New status value to set
            
        Returns:
            Updated session data dictionary
            
        Raises:
            NotFoundError: If session not found
            ValidationError: If status update fails
        """
        # Get current session data
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Update session status
        session_data['status'] = status
        
        # Add timestamp for status change
        session_data[f'{status}_at'] = datetime.now().isoformat()
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        from utils.file_utils import write_json_file
        write_json_file(session_file_path, session_data)
        
        return session_data
    
    @staticmethod
    def calculate_participants_points(username: str, presentation_uuid: str, session_uuid: str) -> Dict[str, Any]:
        """
        Calculate points for each participant based on their answers.
        
        Analyzes all questions in answers_statistics and calculates points for each participant
        based on correct and incorrect answers. Handles both single_choice and multiple_choice
        question types with appropriate scoring logic.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Updated session data dictionary with users_points map
        """
        # Get current session data
        session_data = load_session(username, presentation_uuid, session_uuid)
        
        # Initialize users_points map
        users_points = {}
        
        # Get answers_statistics and questions from session data
        answers_statistics = session_data.get('answers_statistics', {})
        questions = session_data.get('questions', {})
        
        # Loop across all questions in answers_statistics
        for question_uuid, question_stats in answers_statistics.items():
            # Get question data
            question = questions.get(question_uuid)
            if not question:
                continue  # Skip if question data not found
            
            # Get question properties
            question_type = question.get('type')
            question_points = question.get('points', 0)
            correct_indices = question.get('correct_indices', [])
            
            # Skip if no correct indices or no points
            if not correct_indices or question_points <= 0:
                continue
            
            # Convert correct_indices to set for easier lookup
            correct_indices_set = set(correct_indices)
            correct_choices_length = len(correct_indices_set)
            
            # Loop for each choice in this question's statistics
            for choice_index_str, participant_uuids in question_stats.items():
                try:
                    choice_index = int(choice_index_str)
                except ValueError:
                    continue  # Skip invalid choice indices
                
                # Determine if this choice is correct
                is_correct = choice_index in correct_indices_set
                
                # Calculate points for this choice
                if question_type == "single_choice":
                    # For single choice, only correct choice gets full points
                    choice_points = question_points if is_correct else 0
                elif question_type == "multiple_choice":
                    # For multiple choice, divide points among correct choices
                    # and subtract for wrong choices
                    choice_points = question_points / correct_choices_length
                    if not is_correct:
                        choice_points = -choice_points  # Negative points for wrong choice
                else:
                    continue  # Skip unsupported question types
                
                # Loop for each participant uuid who selected this choice
                for participant_uuid in participant_uuids:
                    # Initialize participant points if not exists
                    if participant_uuid not in users_points:
                        users_points[participant_uuid] = 0
                    
                    # Add/increment the points for this participant
                    users_points[participant_uuid] += choice_points
        
        # Round all participant points to integers
        for participant_uuid in users_points:
            users_points[participant_uuid] = round(users_points[participant_uuid])
        
        # Store the users_points map in the session data
        session_data['users_points'] = users_points
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        from utils.file_utils import write_json_file
        write_json_file(session_file_path, session_data)
        
        return session_data
    
    @staticmethod
    def calculate_participant_performance(username: str, presentation_uuid: str, session_uuid: str) -> List[Dict[str, Any]]:
        """
        Calculate performance metrics for each participant in a session.
        
        Analyzes participant answers from users_answers data and calculates
        correct answers count, total answered, and score percentage for each participant.
        Handles both single_choice and multiple_choice question types.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            List of participant performance dictionaries sorted by score_percentage (highest first)
            Each dictionary contains: uuid, nickname, correct_count, total_answered, score_percentage
            
        Raises:
            NotFoundError: If session not found
            ValidationError: If required data is missing
        """
        # Get current session data
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Get participants, questions, and user answers from session data
        participants = session_data.get('participants', [])
        questions = session_data.get('questions', {})
        users_answers = session_data.get('users_answers', {})
        
        # Calculate participant performance
        participant_results = []
        for participant in participants:
            participant_uuid = participant.get('uuid')
            nickname = participant.get('nickname', 'Anonymous')
            
            # Get participant's answers from users_answers
            participant_answers = users_answers.get(participant_uuid, {})
            
            # Calculate correct answers count
            correct_count = 0
            total_answered = 0
            
            for question_uuid, answer_data in participant_answers.items():
                if question_uuid in questions:
                    question = questions[question_uuid]
                    correct_indices = question.get('correct_indices', [])
                    user_answer = answer_data
                    
                    total_answered += 1
                    
                    # Handle both single answer (int) and multiple answers (list)
                    if isinstance(user_answer, list):
                        # Multiple choice: check if all selected indices are correct
                        correct_indices_set = set(correct_indices)
                        user_answer_set = set(user_answer)
                        if user_answer_set == correct_indices_set:
                            correct_count += 1
                    else:
                        # Single choice: check if answer matches correct index
                        if user_answer in correct_indices:
                            correct_count += 1
            
            score_percentage = (correct_count / total_answered * 100) if total_answered > 0 else 0
            
            participant_results.append({
                'uuid': participant_uuid,
                'nickname': nickname,
                'correct_count': correct_count,
                'total_answered': total_answered,
                'score_percentage': round(score_percentage, 1)
            })
        
        # Sort participants by score (highest first)
        participant_results.sort(key=lambda x: x['score_percentage'], reverse=True)
        
        return participant_results
    
    @staticmethod
    def calculate_objectives_performance(username: str, presentation_uuid: str, session_uuid: str, question_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate performance metrics for each objective based on question performance.
        
        Aggregates question performance by parent_objective_id and calculates
        average performance for each objective.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            question_stats: List of question performance statistics from calculate_question_statistics
            
        Returns:
            List of objective performance dictionaries sorted by objective order
            Each dictionary contains: uuid, objective_text, total_questions, avg_performance
            
        Raises:
            NotFoundError: If session not found
            ValidationError: If required data is missing
        """
        # Get current session data
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Get objectives and questions from session data
        objectives = session_data.get('objectives', {})
        questions = session_data.get('questions', {})
        
        # Create a mapping of objective_id to list of question performances
        objective_question_map = {}
        
        # Group question statistics by parent_objective_id
        for question_stat in question_stats:
            question_uuid = question_stat.get('uuid')
            if question_uuid in questions:
                question = questions[question_uuid]
                parent_objective_id = question.get('parent_objective_id')
                
                if parent_objective_id:
                    if parent_objective_id not in objective_question_map:
                        objective_question_map[parent_objective_id] = []
                    objective_question_map[parent_objective_id].append(question_stat)
        
        # Calculate objective performance
        objective_results = []
        for objective_id, objective_questions in objective_question_map.items():
            # Get objective data
            objective = objectives.get(objective_id, {})
            objective_text = objective.get('text', 'Unknown Objective')
            objective_order = objective.get('order', 999)
            
            # Calculate average performance
            total_questions = len(objective_questions)
            total_performance = sum(q.get('correct_percentage', 0) for q in objective_questions)
            avg_performance = total_performance / total_questions if total_questions > 0 else 0
            
            objective_results.append({
                'uuid': objective_id,
                'objective_text': objective_text,
                'order': objective_order,
                'total_questions': total_questions,
                'avg_performance': round(avg_performance, 1)
            })
        
        # Sort by objective order
        objective_results.sort(key=lambda x: x['order'])
        
        return objective_results
    
    @staticmethod
    def end_session(username: str, presentation_uuid: str, session_uuid: str) -> Dict[str, Any]:
        """
        End a session by updating its status to completed.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Updated session data dictionary
            
        Raises:
            NotFoundError: If session not found
            ValidationError: If session update fails
        """
        # Get current session data
        session_data = SessionService.get_session(username, presentation_uuid, session_uuid)
        
        # Update session status to completed
        session_data['status'] = 'completed'
        session_data['ended_at'] = datetime.now().isoformat()
        
        # Clear current question timing
        session_data['current_question_uuid'] = None
        session_data['start_time'] = None
        session_data['end_time'] = None
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        from utils.file_utils import write_json_file
        write_json_file(session_file_path, session_data)
        
        return session_data
