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
    def calculate_participant_response_time(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> float:
        """
        Calculate the response time for a participant based on current question timing.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Response time in seconds (0.0 if timing calculation fails)
        """
        try:
            timing_info = LiveSessionService.get_session_timing(
                username, presentation_uuid, session_uuid
            )
            start_time_str = timing_info.get('start_time')
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                return (datetime.now() - start_time).total_seconds()
            return 0.0
        except Exception:
            return 0.0
    
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
    
    @staticmethod
    def get_current_question_index(
        username: str,
        presentation_uuid: str,
        session_uuid: str
    ) -> tuple[int, int]:
        """
        Get the current question index and total questions from session data.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            
        Returns:
            Tuple of (current_question_index, total_questions)
            current_question_index is 0-based, total_questions is the count
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            return 0, 0
        
        shuffled_question_uuids = session_data.get('shuffled_question_uuids', [])
        total_questions = len(shuffled_question_uuids)
        
        if total_questions == 0:
            return 0, 0
        
        current_question_uuid = session_data.get('current_question_uuid')
        if not current_question_uuid or current_question_uuid not in shuffled_question_uuids:
            return 0, total_questions
        
        current_question_index = shuffled_question_uuids.index(current_question_uuid)
        return current_question_index, total_questions
    
    @staticmethod
    def has_user_answered_question(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        user_uuid: str,
        question_uuid: str
    ) -> bool:
        """
        Check if a user has answered a specific question.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            user_uuid: UUID of the user
            question_uuid: UUID of the question
            
        Returns:
            True if user has answered the question, False otherwise
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            return False
        
        users_answers = session_data.get('users_answers', {})
        user_answers = users_answers.get(user_uuid, {})
        return question_uuid in user_answers
    
    @staticmethod
    def set_user_answer(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        user_uuid: str,
        question_uuid: str,
        answer_indices: List[int],
        response_time: float = 0.0
    ) -> bool:
        """
        Set or update a user's answer for a specific question in the session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            user_uuid: UUID of the user
            question_uuid: UUID of the question
            answer_indices: List of selected answer indices
            response_time: Time taken to answer in seconds
            
        Returns:
            True if successful, False otherwise
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            return False
        
        # Initialize users_answers if it doesn't exist
        if 'users_answers' not in session_data:
            session_data['users_answers'] = {}
        
        # Initialize user entry if it doesn't exist
        if user_uuid not in session_data['users_answers']:
            session_data['users_answers'][user_uuid] = {}
        
        # Update the user's answer for this question
        session_data['users_answers'][user_uuid][question_uuid] = answer_indices
        
        # Initialize answers_count if it doesn't exist
        if 'answers_count' not in session_data:
            session_data['answers_count'] = {}
        
        # Initialize question_uuid entry in answers_count if it doesn't exist
        if question_uuid not in session_data['answers_count']:
            session_data['answers_count'][question_uuid] = 0
        
        # Increment answer count for the question by 1
        session_data['answers_count'][question_uuid] += 1
        
        # Initialize response_times if it doesn't exist
        if 'response_times' not in session_data:
            session_data['response_times'] = {}
        
        # Initialize question_uuid entry in response_times if it doesn't exist
        if question_uuid not in session_data['response_times']:
            session_data['response_times'][question_uuid] = []
        
        # Add response time for this participant
        session_data['response_times'][question_uuid].append(response_time)
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        write_json_file(session_file_path, session_data)
        return True
    
    @staticmethod
    def get_answered_participants_count(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        question_uuid: str
    ) -> tuple[int, int]:
        """
        Get the count of participants who have answered a specific question.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            question_uuid: UUID of the question
            
        Returns:
            Tuple of (answered_count, total_participants_count)
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            raise NotFoundError("Session not found")
        
        # Get total participants count
        participants = session_data.get('participants', [])
        total_participants_count = len(participants)
        
        # Get answered count from answers_count
        answers_count = session_data.get('answers_count', {})
        answered_count = answers_count.get(question_uuid, 0)
        
        return answered_count, total_participants_count
    
    @staticmethod
    def calculate_answer_statistics(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        question_uuid: str
    ) -> Dict[str, List[str]]:
        """
        Calculate answer statistics for a specific question.
        
        Groups users by their answer choices and returns a dictionary
        with choice indices as keys and lists of user UUIDs as values.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            question_uuid: UUID of the question
            
        Returns:
            Dictionary with choice indices as keys and lists of user UUIDs as values
            Example: {"0": ["user1", "user3"], "1": ["user2"]}
            
        Raises:
            NotFoundError: If session not found
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            raise NotFoundError("Session not found")
        
        # Initialize statistics dictionary
        statistics = {}
        
        # Get all user answers for this question
        users_answers = session_data.get('users_answers', {})
        
        # Group users by their answer choices
        for user_uuid, user_answers in users_answers.items():
            if question_uuid in user_answers:
                answer_indices = user_answers[question_uuid]
                # Handle both single answer (int) and multiple answers (list)
                if isinstance(answer_indices, list):
                    for answer_index in answer_indices:
                        choice_key = str(answer_index)
                        if choice_key not in statistics:
                            statistics[choice_key] = []
                        statistics[choice_key].append(user_uuid)
                else:
                    choice_key = str(answer_indices)
                    if choice_key not in statistics:
                        statistics[choice_key] = []
                    statistics[choice_key].append(user_uuid)
        
        return statistics
    
    @staticmethod
    def store_answer_statistics(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        question_uuid: str,
        statistics: Dict[str, List[str]]
    ) -> bool:
        """
        Store answer statistics for a specific question in the session data.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            question_uuid: UUID of the question
            statistics: Answer statistics dictionary
            
        Returns:
            True if successful, False otherwise
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            return False
        
        # Initialize answers_statistics if it doesn't exist
        if 'answers_statistics' not in session_data:
            session_data['answers_statistics'] = {}
        
        # Store statistics for this question
        session_data['answers_statistics'][question_uuid] = statistics
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        write_json_file(session_file_path, session_data)
        return True
    
    @staticmethod
    def calculate_statistics(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        question_uuid: str
    ) -> Dict[str, Any]:
        """
        Calculate and store answer statistics for a specific question.
        
        Combines statistics calculation, storage, and participants map creation
        into a single method for better code organization.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            question_uuid: UUID of the question
            
        Returns:
            Dictionary containing statistics, participants map, and current question data
            {
                'statistics': Dict[str, List[str]],
                'participants_map': Dict[str, Dict],
                'current_question': Dict[str, Any],
                'success': bool
            }
        """
        try:
            # Load session data
            session_data = load_session(username, presentation_uuid, session_uuid)
            if not session_data:
                return {'success': False, 'error': 'Session not found'}
            
            # Calculate answer statistics
            statistics = LiveSessionService.calculate_answer_statistics(
                username, presentation_uuid, session_uuid, question_uuid
            )
            
            # Store statistics in session data
            store_success = LiveSessionService.store_answer_statistics(
                username, presentation_uuid, session_uuid, question_uuid, statistics
            )
            
            if not store_success:
                return {'success': False, 'error': 'Failed to store statistics'}
            
            # Create participants map for easy lookup
            participants_map = {}
            for participant in session_data.get('participants', []):
                participants_map[participant['uuid']] = participant
            
            # Get current question data
            current_question = None
            questions = session_data.get('questions', {})
            if question_uuid in questions:
                current_question = questions[question_uuid]
            
            return {
                'statistics': statistics,
                'participants_map': participants_map,
                'current_question': current_question,
                'success': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def calculate_enhanced_statistics(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        question_uuid: str
    ) -> Dict[str, Any]:
        """
        Calculate enhanced statistics for question results display.
        
        Includes correct answer count, response time, clarity analysis,
        and other metrics needed for the comprehensive results view.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            question_uuid: UUID of the question
            
        Returns:
            Dictionary with enhanced statistics data
        """
        try:
            # Load session data
            session_data = load_session(username, presentation_uuid, session_uuid)
            if not session_data:
                return {'success': False, 'error': 'Session not found'}
            
            # Get current question data
            questions = session_data.get('questions', {})
            current_question = questions.get(question_uuid)
            if not current_question:
                return {'success': False, 'error': 'Question not found'}
            
            # Get basic answer statistics
            answer_statistics = LiveSessionService.calculate_answer_statistics(
                username, presentation_uuid, session_uuid, question_uuid
            )
            
            # Calculate total responded participants
            total_responded = 0
            for choice_responses in answer_statistics.values():
                total_responded += len(choice_responses)
            
            # Calculate correct answers count
            correct_answers = 0
            correct_indices = set()
            
            # Handle both single choice and multiple choice questions
            if isinstance(current_question.get('correct_indices'), list):
                correct_indices = set(str(idx) for idx in current_question['correct_indices'])
            elif current_question.get('correct_indices') is not None:
                correct_indices = {str(current_question['correct_indices'])}
            
            for choice_index, participants in answer_statistics.items():
                if choice_index in correct_indices:
                    correct_answers += len(participants)
            
            # Calculate average response time
            avg_response_time = LiveSessionService.calculate_average_response_time(
                session_data, question_uuid
            )
            
            # Get question points
            question_points = current_question.get('points', 0)
            
            # Get total participants count
            total_participants = len(session_data.get('participants', []))
            
            # Create clarity analysis
            from services.understanding_service import UnderstandingService
            clarity_analysis = UnderstandingService.get_clarity_analysis(
                correct_answers, total_responded
            )
            
            # Prepare choice data for bar chart
            choice_data = []
            for i, choice_text in enumerate(current_question.get('choices', [])):
                choice_index = str(i)
                responses = answer_statistics.get(choice_index, [])
                is_correct = choice_index in correct_indices
                
                choice_data.append({
                    'index': i,
                    'text': choice_text,
                    'count': len(responses),
                    'percentage': (len(responses) / total_responded * 100) if total_responded > 0 else 0,
                    'is_correct': is_correct,
                    'participants': responses
                })
            
            return {
                'success': True,
                'question_stats': {
                    'responded': f"{total_responded}/{total_participants}",
                    'responded_count': total_responded,
                    'total_participants': total_participants,
                    'correct_answers': correct_answers,
                    'correct_percentage': (correct_answers / total_responded * 100) if total_responded > 0 else 0,
                    'avg_response_time': avg_response_time,
                    'question_points': question_points
                },
                'clarity_analysis': clarity_analysis,
                'choice_data': choice_data,
                'answer_statistics': answer_statistics
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def calculate_average_response_time(
        session_data: Dict[str, Any], 
        question_uuid: str
    ) -> int:
        """
        Calculate average response time for a question.
        
        Args:
            session_data: Session data dictionary
            question_uuid: UUID of the question
            
        Returns:
            Average response time in seconds as rounded integer (0 if no data available)
        """
        try:
            response_times = session_data.get('response_times', {})
            question_times = response_times.get(question_uuid, [])
            
            if not question_times:
                return 0
            
            average = sum(question_times) / len(question_times)
            return round(average)
            
        except Exception:
            return 0
    
    @staticmethod
    def update_session_status(
        username: str,
        presentation_uuid: str,
        session_uuid: str,
        status: str
    ) -> bool:
        """
        Update the status of a session.
        
        Args:
            username: Instructor username
            presentation_uuid: UUID of the presentation
            session_uuid: UUID of the session
            status: New status value
            
        Returns:
            True if successful, False otherwise
        """
        session_data = load_session(username, presentation_uuid, session_uuid)
        if not session_data:
            return False
        
        # Update session status
        session_data['status'] = status
        
        # Save updated session data
        session_file_path = get_session_file_path(username, presentation_uuid, session_uuid)
        write_json_file(session_file_path, session_data)
        return True
