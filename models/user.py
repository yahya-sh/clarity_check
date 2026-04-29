"""
models/user.py — Instructor user domain model.

Passwords are stored as SHA-256 hex digests.  The model intentionally has no
dependency on Flask or the file store; persistence is handled exclusively by
:mod:`repositories.users`.
"""
import hashlib
from datetime import datetime, UTC
class User:
    """
    Represents an instructor account.

    Attributes:
        username (str): Unique login name.
        password_hash (str): SHA-256 hex digest of the user's password.
        created_at (str): ISO-8601 timestamp of account creation (UTC with
            trailing ``Z``).
    """
    username: str
    password_hash: str
    created_at: str
    
    def __init__(self, username: str, password: str|None = None, password_hash: str|None = None, created_at: str|None =None):
        self.username = username
        self.password_hash = password_hash or self.__hash_password(password)
        self.created_at = created_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def check_password(self, password: str)-> bool:
        return self.password_hash == self.__hash_password(password)
    
    def to_dict(self):
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        }
    
    @classmethod
    def __hash_password(cls, password: str)-> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data['username'],
            password_hash=data['password_hash'],
            created_at=data['created_at']
        )
    