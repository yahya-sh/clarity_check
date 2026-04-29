"""
services/auth_service.py — Authentication business logic service.

Handles all authentication-related business logic including login,
registration, logout, and user validation. Extracted from auth routes
to improve separation of concerns and testability.
"""

from typing import Optional, Tuple

from repositories import users_repo
from repositories.base import ValidationError, NotFoundError
from models.user import User


class AuthService:
    """
    Service class for authentication business logic.
    
    Centralizes all authentication operations including login validation,
    registration processing, and user management.
    """
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The password to validate
            
        Returns:
            Tuple of (success, error_message, user_object)
            - success: True if authentication succeeded
            - error_message: Error message if failed, None if succeeded
            - user_object: User instance if succeeded, None if failed
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        user = users_repo.get_user(username)
        if not user:
            return False, "Invalid username or password", None
        
        if not user.check_password(password):
            return False, "Invalid username or password", None
        
        return True, None, user
    
    @staticmethod
    def register_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[User]]:
        """
        Register a new user account.
        
        Args:
            username: The username for the new account
            password: The password for the new account
            
        Returns:
            Tuple of (success, error_message, user_object)
            - success: True if registration succeeded
            - error_message: Error message if failed, None if succeeded
            - user_object: User instance if succeeded, None if failed
        """
        if not username or not password:
            return False, "Username and password are required", None
        
        # Check if username already exists by attempting to create user
        user = User(username=username, password=password)
        saved_user = users_repo.create_user(user)
        
        if saved_user:
            return True, None, saved_user
        else:
            return False, "Username is already taken. Please choose another one.", None
