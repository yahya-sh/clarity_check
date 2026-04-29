"""
services/presentation_service.py — Presentation business logic service.

Handles all business logic related to presentations, including validation,
objective management, question management, and status transitions.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid

from models.presentation import Presentation
from repositories.presentations import save_presentation, load_presentation
from repositories.base import ValidationError, NotFoundError
from config.constants import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_ARCHIVED,
    MIN_QUESTIONS_FOR_PUBLISH,
    MIN_OBJECTIVES_FOR_PUBLISH,
    VALID_STATUSES
)


class PresentationService:
    """
    Service class for presentation business logic.
    
    Centralizes all presentation-related business operations,
    validation, and state management.
    """
    
    @staticmethod
    def create_presentation(username: str, title: str = "Untitled", description: str = "") -> Presentation:
        """
        Create a new presentation with default values.
        
        Args:
            username: Instructor username
            title: Presentation title (defaults to "Untitled")
            description: Presentation description
            
        Returns:
            Created presentation instance
        """
        presentation = Presentation(
            title=title,
            description=description,
            username=username,
            status=STATUS_DRAFT
        )
        
        return save_presentation(presentation)
    
    @staticmethod
    def update_presentation_basic_info(
        presentation_id: str,
        username: str,
        title: str,
        description: str,
        status: str
    ) -> Tuple[Presentation, Optional[str]]:
        """
        Update basic presentation information.
        
        Args:
            presentation_id: UUID of the presentation
            username: Instructor username
            title: New title
            description: New description
            status: New status
            
        Returns:
            Tuple of (updated presentation, warning message)
            
        Raises:
            NotFoundError: If presentation not found
            ValidationError: If status is invalid
        """
        presentation = load_presentation(username, presentation_id)
        if not presentation:
            raise NotFoundError("Presentation not found")
        
        # Validate status
        if status not in VALID_STATUSES:
            raise ValidationError(f"Invalid status: {status}")
        
        # Validate publishing requirements
        if status == STATUS_PUBLISHED:
            can_publish, error_message = presentation.can_be_published()
            if not can_publish:
                raise ValidationError(error_message)
        
        # Update presentation
        presentation.title = title
        presentation.description = description
        presentation.status = status
        
        # Validate and fix status if needed
        status_changed, message = presentation.validate_and_fix_status()
        warning = message if status_changed else None
        
        # Save presentation
        updated_presentation = save_presentation(presentation)
        
        return updated_presentation, warning
    
    @staticmethod
    def add_objective(presentation_id: str, username: str, objective_text: str) -> Presentation:
        """
        Add a new objective to a presentation.
        
        Args:
            presentation_id: UUID of the presentation
            username: Instructor username
            objective_text: Text for the new objective
            
        Returns:
            Updated presentation
            
        Raises:
            NotFoundError: If presentation not found
            ValidationError: If objective text is empty
        """
        if not objective_text or not objective_text.strip():
            raise ValidationError("Objective title cannot be empty.")
        
        presentation = load_presentation(username, presentation_id)
        if not presentation:
            raise NotFoundError("Presentation not found")
        
        # Ensure objectives is a list
        if not isinstance(presentation.objectives, list):
            presentation.objectives = []
        
        # Calculate next order
        next_order = (
            max((o.get('order', -1) for o in presentation.objectives), default=-1) + 1
        )
        
        # Add new objective
        new_objective = {
            'objective_id': str(uuid.uuid4()),
            'text': objective_text.strip(),
            'order': next_order,
            'questions': [],
        }
        
        presentation.objectives.append(new_objective)
        
        # Validate and fix status
        presentation.validate_and_fix_status()
        
        return save_presentation(presentation)
    
    @staticmethod
    def update_objective(
        presentation_id: str,
        username: str,
        objective_id: str,
        objective_text: str
    ) -> Presentation:
        """
        Update an existing objective.
        
        Args:
            presentation_id: UUID of the presentation
            username: Instructor username
            objective_id: UUID of the objective
            objective_text: New text for the objective
            
        Returns:
            Updated presentation
            
        Raises:
            NotFoundError: If presentation or objective not found
            ValidationError: If objective text is empty
        """
        if not objective_text or not objective_text.strip():
            raise ValidationError("Objective title cannot be empty.")
        
        presentation = load_presentation(username, presentation_id)
        if not presentation:
            raise NotFoundError("Presentation not found")
        
        objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
        objective = next((o for o in objectives if o.get('objective_id') == objective_id), None)
        
        if objective is None:
            raise NotFoundError("Objective not found")
        
        objective['text'] = objective_text.strip()
        
        return save_presentation(presentation)
    
    @staticmethod
    def delete_objective(presentation_id: str, username: str, objective_id: str) -> Presentation:
        """
        Delete an objective and resequence remaining objectives.
        
        Args:
            presentation_id: UUID of the presentation
            username: Instructor username
            objective_id: UUID of the objective to delete
            
        Returns:
            Updated presentation
            
        Raises:
            NotFoundError: If presentation or objective not found
        """
        presentation = load_presentation(username, presentation_id)
        if not presentation:
            raise NotFoundError("Presentation not found")
        
        objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
        filtered = [o for o in objectives if o.get('objective_id') != objective_id]
        
        if len(filtered) == len(objectives):
            raise NotFoundError("Objective not found")
        
        # Resequence orders after deletion
        for index, obj in enumerate(sorted(filtered, key=lambda o: o.get('order', 0))):
            obj['order'] = index
        
        presentation.objectives = filtered
        
        # Validate and fix status
        presentation.validate_and_fix_status()
        
        return save_presentation(presentation)
    
    @staticmethod
    def get_objective_questions(presentation_id: str, username: str, objective_id: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a specific objective.
        
        Args:
            presentation_id: UUID of the presentation
            username: Instructor username
            objective_id: UUID of the objective
            
        Returns:
            List of question dictionaries
            
        Raises:
            NotFoundError: If presentation or objective not found
        """
        presentation = load_presentation(username, presentation_id)
        if not presentation:
            raise NotFoundError("Presentation not found")
        
        objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
        objective = next((o for o in objectives if o.get('objective_id') == objective_id), None)
        
        if objective is None:
            raise NotFoundError("Objective not found")
        
        questions = objective.get('questions', [])
        if not isinstance(questions, list):
            return []
        
        # Sort by order and format for response
        formatted_questions = [
            {
                'question_id': q.get('question_id'),
                'text': q.get('text', ''),
                'type': q.get('type', 'single_choice'),
                'choices': q.get('choices', []),
                # Handle legacy typo 'correct_indicies' in older saved data
                'correct_indices': q.get('correct_indices', q.get('correct_indicies', [])),
                'points': q.get('points'),
                'time_limit': q.get('time_limit'),
                'order': q.get('order', 0),
            }
            for q in sorted(questions, key=lambda q: q.get('order', 0))
        ]
        
        return formatted_questions
    
