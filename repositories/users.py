import json
import os
from pathlib import Path
from models.user import User

users_dir = Path('data/users')

def username_exist(username: str) -> bool:
    """Check if a username already exists by checking if the user file exists."""
    user_file = users_dir / f"{username}.json"
    return user_file.exists()

def get_user(username: str) -> User|None:
    """Get user using username."""
    user_file = users_dir / f"{username}.json"
    if user_file.exists():
        try:
            with open(user_file, 'r') as f:
                user_data = json.load(f)
                user_data['username'] = username
                return User.from_dict(user_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    return None

def save_user(user: User) -> bool:
    """Save user data to individual user file. Accepts User model or dict."""
    user_file = users_dir / f"{user.username}.json"
    
    # Ensure users directory exists
    users_dir.mkdir(parents=True, exist_ok=True)

    
    try:
        user_record = user.to_dict()
        del user_record['username']
            
        with open(user_file, 'w') as f:
            json.dump(user_record, f, indent=2)
        return True
    except Exception:
        return False


def create_user(user: User) -> User|None:
    """Create a new user and save to file."""
    if username_exist(user.username):
        return None
    
    if save_user(user):
        return user
    return None