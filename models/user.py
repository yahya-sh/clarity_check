import hashlib
from datetime import datetime, UTC
class User:
    username: str
    password_hash: str
    created_at: str
    
    def __init__(self, username: str, password: str, password_hash = None):
        self.username = username
        self.password_hash = password_hash or hashlib.sha256(password.encode()).hexdigest()
        self.created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    
    def to_dict(self):
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data['username'],
            password_hash=data['password_hash'],
            created_at=data['created_at']
        )
    