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
    
    def __init__(self, title: str, description: str, username: str, status: str = 'draft'):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.username = username
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.objectives = []
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'username': self.username,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'objectives': self.objectives
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
        return presentation
