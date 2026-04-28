import uuid
from datetime import datetime, UTC

class Participant:
    uuid: str
    session_uuid: str
    nickname: str
    presentation_uuid: str
    presentation_instructor_username: str
    
    def __init__(self, session_uuid: str, nickname: str, presentation_uuid: str, presentation_instructor_username: str, participant_uuid: str|None = None):
        self.uuid = participant_uuid or str(uuid.uuid4())
        self.session_uuid = session_uuid
        self.nickname = nickname
        self.presentation_uuid = presentation_uuid
        self.presentation_instructor_username = presentation_instructor_username
    
    def to_dict(self):
        return {
            'uuid': self.uuid,
            'session_uuid': self.session_uuid,
            'nickname': self.nickname,
            'presentation_uuid': self.presentation_uuid,
            'presentation_instructor_username': self.presentation_instructor_username,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            session_uuid=data['session_uuid'],
            nickname=data['nickname'],
            presentation_uuid=data['presentation_uuid'],
            presentation_instructor_username=data['presentation_instructor_username'],
            participant_uuid=data['uuid']
        )
