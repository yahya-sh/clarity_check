import uuid
from datetime import datetime, UTC

class Participant:
    uuid: str
    session_uuid: str
    nickname: str
    
    def __init__(self, session_uuid: str, nickname: str, participant_uuid: str|None = None):
        self.uuid = participant_uuid or str(uuid.uuid4())
        self.session_uuid = session_uuid
        self.nickname = nickname
    
    def to_dict(self):
        return {
            'uuid': self.uuid,
            'session_uuid': self.session_uuid,
            'nickname': self.nickname,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            session_uuid=data['session_uuid'],
            nickname=data['nickname'],
            participant_uuid=data['uuid']
        )
