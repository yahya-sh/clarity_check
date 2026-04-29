import os
from pathlib import Path
from models.user import User
from utils.file_utils import read_json_file, write_json_file, FileOperationError

users_dir = Path('data/users')

def username_exist(username: str) -> bool:
    """Check if a username already exists by checking if the user file exists."""
    user_file = users_dir / f"{username}.json"
    return user_file.exists()

def get_user(username: str) -> User|None:
    """Get user using username."""
    user_file = users_dir / f"{username}.json"
    try:
        user_data = read_json_file(str(user_file))
        user_data['username'] = username
        return User.from_dict(user_data)
    except FileOperationError:
        return None

def save_user(user: User) -> bool:
    """Save user data to individual user file. Accepts User model or dict."""
    user_file = users_dir / f"{user.username}.json"
    
    # Ensure users directory exists
    users_dir.mkdir(parents=True, exist_ok=True)

    
    try:
        user_record = user.to_dict()
        del user_record['username']
        write_json_file(str(user_file), user_record)
        return True
    except FileOperationError:
        return False


def create_user(user: User) -> User|None:
    """Create a new user and save to file."""
    if username_exist(user.username):
        return None
    
    if save_user(user):
        return user
    return None