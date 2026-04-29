"""
utils/response_utils.py — Response formatting utilities.

Provides standardized response formatting for JSON API endpoints
and common response patterns across all routes.
"""

from typing import Dict, Any, Optional, Tuple
from flask import jsonify, Response


class ResponseUtils:
    """
    Utility class for formatting HTTP responses.
    
    Centralizes response formatting logic to ensure consistency
    across all API endpoints and error handling.
    """
    
    @staticmethod
    def success_response(data: Optional[Dict[str, Any]] = None, status_code: int = 200) -> Tuple[Dict[str, Any], int]:
        """
        Create a successful JSON response.
        
        Args:
            data: Data to include in the response
            status_code: HTTP status code (default: 200)
            
        Returns:
            Tuple of (response data, status_code)
        """
        response_data = data or {}
        response_data['success'] = True
        
        return response_data, status_code
    
    @staticmethod
    def error_response(message: str, status_code: int = 400, additional_data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        """
        Create an error JSON response.
        
        Args:
            message: Error message
            status_code: HTTP status code (default: 400)
            additional_data: Additional data to include in response
            
        Returns:
            Tuple of (response data, status_code)
        """
        response_data = {
            'success': False,
            'error': message
        }
        
        if additional_data:
            response_data.update(additional_data)
        
        return response_data, status_code
    
    @staticmethod
    def session_status_response(is_active: bool, status: str = "waiting") -> Tuple[Dict[str, Any], int]:
        """
        Create a session status response.
        
        Args:
            is_active: Whether the session is active
            status: Session status (default: "waiting")
            
        Returns:
            Tuple of (response data, status_code)
        """
        response_data = {
            'success': is_active,
            'status': status
        }
        
        return response_data, 200
