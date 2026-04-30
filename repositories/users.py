"""
repositories/users.py — User account data repository.

Handles all CRUD operations for user accounts including authentication
data persistence and username validation. Provides file-based storage
for user accounts with standardized error handling.
"""

import os
from pathlib import Path
from models.user import User
from utils.file_utils import read_json_file, write_json_file, FileOperationError

users_dir = Path('data/users')

def username_exist(username: str) -> bool:
    """
    Check if a username already exists by checking if user file exists.
    
    Args:
        username: The username to check for existence
        
    Returns:
        True if username exists, False otherwise
    """
    user_file = users_dir / f"{username}.json"
    return user_file.exists()

def get_user(username: str) -> User|None:
    """
    Get user data by username from file storage.
    
    Args:
        username: The username to retrieve
        
    Returns:
        User instance if found, None if file doesn't exist or is corrupted
    """
    user_file = users_dir / f"{username}.json"
    try:
        user_data = read_json_file(str(user_file))
        user_data['username'] = username
        return User.from_dict(user_data)
    except FileOperationError:
        return None

def save_user(user: User) -> bool:
    """
    Save user data to individual user file.
    
    Args:
        user: User instance to save to file
        
    Returns:
        True if saved successfully, False if file operation failed
    """
    user_file = users_dir / f"{user.username}.json"
    
    # Ensure users directory exists
    users_dir.mkdir(parents=True, exist_ok=True)

    try:
        user_record = user.to_dict()
        del user_record['username']  # Username is already in filename
        write_json_file(str(user_file), user_record)
        return True
    except FileOperationError:
        return False


def create_user(user: User) -> User|None:
    """
    Create a new user account and save to file storage.
    
    Args:
        user: User instance to create and save
        
    Returns:
        User instance if created successfully, None if username already exists
    """
    if username_exist(user.username):
        return None
    
    if save_user(user):
        return user
    return None