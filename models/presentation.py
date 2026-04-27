from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Presentation:
    id: str
    title: str
    description: str
    username: str
    status: str
    created_at: datetime
    updated_at: datetime
    objectives: list
    session_pin: str = None
    pin_expires_at: str = None
    participants: list = None
    
    def __init__(self, title: str, description: str, username: str, status: str = 'draft'):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.username = username
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.objectives = []
        self.session_pin = None
        self.pin_expires_at = None
        self.participants = []
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'username': self.username,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'objectives': self.objectives,
            'session_pin': self.session_pin,
            'pin_expires_at': self.pin_expires_at,
            'participants': self.participants
        }
    
    @classmethod
    def from_dict(cls, data):
        presentation = cls(data['title'], data['description'], data['username'])
        presentation.id = data['id']
        presentation.status = data.get('status', 'draft')
        presentation.created_at = datetime.fromisoformat(data['created_at'])
        presentation.updated_at = datetime.fromisoformat(data['updated_at'])
        objectives = data.get('objectives', [])
        if isinstance(objectives, list):
            presentation.objectives = objectives
        else:
            presentation.objectives = []
        
        # Load session fields
        presentation.session_pin = data.get('session_pin')
        presentation.pin_expires_at = data.get('pin_expires_at')
        participants = data.get('participants', [])
        if isinstance(participants, list):
            presentation.participants = participants
        else:
            presentation.participants = []
        
        return presentation
    
    def calculate_estimated_duration(self):
        """
        Calculate estimated duration by summing all question time limits,
        multiplying by 1.4, and adding 3 minutes.
        
        Returns:
            float: Estimated duration in minutes
        """
        total_time_seconds = 0
        
        objectives = self.objectives if isinstance(self.objectives, list) else []
        for obj in objectives:
            questions = obj.get('questions', [])
            if isinstance(questions, list):
                for question in questions:
                    time_limit = question.get('time_limit')
                    if time_limit is not None:
                        try:
                            total_time_seconds += int(time_limit)
                        except (ValueError, TypeError):
                            continue
        
        # Convert to minutes: (sum of time limits in seconds * 1.4 + 3 minutes * 60 seconds) / 60
        estimated_duration = (total_time_seconds * 1.4 + 180) / 60
        return estimated_duration
    
    def can_be_published(self):
        """
        Check if the presentation meets the requirements to be published:
        1. At least two questions total
        2. At least one objective
        3. No objective without questions beneath it
        
        Returns:
            tuple: (bool: can_publish, str: error_message)
        """
        objectives = self.objectives if isinstance(self.objectives, list) else []
        
        # Check if there's at least one objective
        if len(objectives) < 1:
            return False, "Presentation must have at least one objective to be published."
        
        total_questions = 0
        objectives_without_questions = []
        
        for objective in objectives:
            questions = objective.get('questions', [])
            if isinstance(questions, list):
                total_questions += len(questions)
                if len(questions) == 0:
                    objectives_without_questions.append(objective.get('text', 'Untitled objective'))
        
        # Check if there are at least two questions
        if total_questions < 2:
            return False, "Presentation must have at least two questions to be published."
        
        # Check if any objective has no questions
        if objectives_without_questions:
            objective_names = ', '.join(objectives_without_questions)
            return False, f"The following objectives have no questions: {objective_names}"
        
        return True, ""
    
    def validate_and_fix_status(self):
        """
        Validate the presentation and automatically convert to draft if it doesn't meet publishing requirements.
        
        Returns:
            tuple: (bool: status_changed, str: message)
        """
        if self.status == 'published':
            can_publish, error_message = self.can_be_published()
            if not can_publish:
                self.status = 'draft'
                return True, f"Presentation automatically set to draft: {error_message}"
        
        return False, ""
