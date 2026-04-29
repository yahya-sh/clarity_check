"""
services/question_service.py — Question management service.

Handles all question-related business logic including creation,
updating, deletion, and validation. Extracted from instructor routes
to improve separation of concerns and testability.
"""

from typing import Dict, List, Any, Optional, Tuple
import uuid

from models.presentation import Presentation
from repositories.base import NotFoundError, ValidationError
from forms.question import SaveQuestionForm


class QuestionService:
    """
    Service class for question business logic.
    
    Centralizes all question operations including creation, updating,
    deletion, and validation within presentation objectives.
    """
    
    @staticmethod
    def find_objective_in_presentation(presentation: Presentation, objective_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an objective within a presentation by ID.
        
        Args:
            presentation: Presentation instance
            objective_id: UUID of the objective to find
            
        Returns:
            Objective dictionary or None if not found
        """
        objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
        return next((o for o in objectives if o.get('objective_id') == objective_id), None)
    
    @staticmethod
    def find_question_in_objective(objective: Dict[str, Any], question_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a question within an objective by ID.
        
        Args:
            objective: Objective dictionary
            question_id: UUID of the question to find
            
        Returns:
            Question dictionary or None if not found
        """
        questions = objective.get('questions', [])
        if not isinstance(questions, list):
            return None
        return next((q for q in questions if q.get('question_id') == question_id), None)
    
    @staticmethod
    def validate_question_form(form: SaveQuestionForm, objective_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a question form and objective ID match.
        
        Args:
            form: SaveQuestionForm instance
            objective_id: Expected objective ID
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not form.validate():
            first_error = next(
                (errors[0] for errors in form.errors.values() if errors),
                'Invalid question payload.',
            )
            return False, first_error
        
        # Check objective ID match
        form_objective_id = (form.objective_id.data or '').strip()
        if form_objective_id != objective_id:
            return False, 'Objective ID mismatch.'
        
        return True, None
    
    @staticmethod
    def extract_question_data_from_form(form: SaveQuestionForm) -> Dict[str, Any]:
        """
        Extract and clean question data from a form.
        
        Args:
            form: SaveQuestionForm instance
            
        Returns:
            Dictionary with cleaned question data
        """
        return {
            'question_id': (form.question_id.data or '').strip(),
            'text': (form.text.data or '').strip(),
            'type': (form.type.data or '').strip().lower(),
            'choices': form.cleaned_choices,
            'correct_indices': form.cleaned_correct_indices,
            'points': form.points.data,
            'time_limit': form.time_limit.data
        }
    
    @staticmethod
    def create_new_question(question_data: Dict[str, Any], existing_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a new question dictionary with generated ID and order.
        
        Args:
            question_data: Question data from form
            existing_questions: List of existing questions in the objective
            
        Returns:
            New question dictionary
        """
        question_id = question_data.get('question_id') or str(uuid.uuid4())
        order = max((q.get('order', -1) for q in existing_questions), default=-1) + 1
        
        return {
            'question_id': question_id,
            'text': question_data['text'],
            'type': question_data['type'],
            'choices': question_data['choices'],
            'correct_indices': question_data['correct_indices'],
            'order': order,
            'points': question_data['points'],
            'time_limit': question_data['time_limit'],
        }
    
    @staticmethod
    def update_existing_question(existing_question: Dict[str, Any], question_data: Dict[str, Any]) -> None:
        """
        Update an existing question with new data.
        
        Args:
            existing_question: Existing question dictionary to update
            question_data: New question data
        """
        existing_question.update({
            'text': question_data['text'],
            'type': question_data['type'],
            'choices': question_data['choices'],
            'correct_indices': question_data['correct_indices'],
            'points': question_data['points'],
            'time_limit': question_data['time_limit'],
        })
    
    @staticmethod
    def save_question_to_objective(
        presentation: Presentation,
        objective_id: str,
        question_data: Dict[str, Any],
        save_presentation_func
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save a question to an objective (create or update).
        
        Args:
            presentation: Presentation instance
            objective_id: UUID of the objective
            question_data: Question data from form
            save_presentation_func: Function to save the presentation
            
        Returns:
            Tuple of (success, error_message, question_id)
        """
        # Find objective
        objective = QuestionService.find_objective_in_presentation(presentation, objective_id)
        if not objective:
            return False, 'Objective not found.', None
        
        # Ensure questions list exists
        questions = objective.get('questions', [])
        if not isinstance(questions, list):
            questions = []
            objective['questions'] = questions
        
        # Check if this is an existing question
        question_id = question_data.get('question_id')
        existing_question = QuestionService.find_question_in_objective(objective, question_id) if question_id else None
        
        if existing_question is None:
            # Create new question
            new_question = QuestionService.create_new_question(question_data, questions)
            questions.append(new_question)
            final_question_id = new_question['question_id']
        else:
            # Update existing question
            QuestionService.update_existing_question(existing_question, question_data)
            final_question_id = existing_question['question_id']
        
        # Save presentation
        save_presentation_func(presentation)
        
        return True, None, final_question_id
    
    @staticmethod
    def delete_question_from_objective(
        presentation: Presentation,
        objective_id: str,
        question_id: str,
        save_presentation_func
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a question from an objective and re-sequence remaining questions.
        
        Args:
            presentation: Presentation instance
            objective_id: UUID of the objective
            question_id: UUID of the question to delete
            save_presentation_func: Function to save the presentation
            
        Returns:
            Tuple of (success, error_message)
        """
        # Find objective
        objective = QuestionService.find_objective_in_presentation(presentation, objective_id)
        if not objective:
            return False, 'Objective not found.'
        
        # Find and remove question
        questions = objective.get('questions', [])
        if not isinstance(questions, list):
            return False, 'Objective has no questions.'
        
        original_length = len(questions)
        filtered_questions = [q for q in questions if q.get('question_id') != question_id]
        
        if len(filtered_questions) == original_length:
            return False, 'Question not found.'
        
        # Re-sequence remaining questions
        for index, question in enumerate(sorted(filtered_questions, key=lambda q: q.get('order', 0))):
            question['order'] = index
        
        objective['questions'] = filtered_questions
        
        # Save presentation
        save_presentation_func(presentation)
        
        return True, None
