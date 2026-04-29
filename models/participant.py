"""
models/participant.py — Participant domain model.

A participant is a session attendee (non-instructor) who joins via a PIN code.
This model is used both during the run (lobby) phase and during the live
session.  It is stored in abbreviated form inside the run JSON file and
reconstituted from the Flask session on each request by
:func:`~app.add_auth_participant_to_context`.
"""
import uuid
from datetime import datetime, UTC

class Participant:
    """
    Represents a participant in a presentation session.

    Attributes:
        uuid (str): Unique identifier for this participant.
        session_uuid (str): UUID of the session the participant belongs to.
        nickname (str): Display name chosen by the participant.
        presentation_uuid (str): UUID of the presentation being attended.
        presentation_instructor_username (str): Username of the instructor
            who owns the presentation.
    """
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
