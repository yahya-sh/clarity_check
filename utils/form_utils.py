"""
utils/form_utils.py — Form handling utilities.

Provides standardized form validation and error processing
patterns to reduce duplication across all routes.
"""

from typing import Dict, Any, Optional, Tuple, List
from flask import flash
from wtforms import Form


class FormUtils:
    """
    Utility class for form handling patterns.
    
    Centralizes common form validation and error processing
    logic to ensure consistency across all routes.
    """
    
    @staticmethod
    def extract_string_field(form, field_name: str, strip: bool = True, default: str = "") -> str:
        """
        Extract a string field from a form.
        
        Args:
            form: WTForms form instance or ImmutableMultiDict
            field_name: Name of the field to extract
            strip: Whether to strip whitespace (default: True)
            default: Default value if field doesn't exist (default: "")
            
        Returns:
            String field value
        """
        # Handle both WTForms (has .data) and ImmutableMultiDict (direct access)
        if hasattr(form, 'data'):
            value = form.data.get(field_name, default)
        else:
            value = form.get(field_name, default)
        
        if isinstance(value, str) and strip:
            return value.strip()
        return str(value) if value is not None else default
    
    @staticmethod
    def validate_required_fields(form_data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that required fields are present and not empty.
        
        Args:
            form_data: Dictionary of form data
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, missing_fields)
            - is_valid: True if all required fields are present and not empty
            - missing_fields: List of missing field names
        """
        missing_fields = []
        
        for field_name in required_fields:
            value = form_data.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field_name)
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def prepare_login_credentials(form: Form) -> Tuple[str, str]:
        """
        Extract and prepare login credentials from form.
        
        Args:
            form: Login form instance
            
        Returns:
            Tuple of (username, password)
        """
        username = FormUtils.extract_string_field(form, 'username')
        password = FormUtils.extract_string_field(form, 'password', strip=False)
        return username, password
    
    @staticmethod
    def prepare_registration_data(form: Form) -> Tuple[str, str]:
        """
        Extract and prepare registration data from form.
        
        Args:
            form: Registration form instance
            
        Returns:
            Tuple of (username, password)
        """
        username = FormUtils.extract_string_field(form, 'username')
        password = FormUtils.extract_string_field(form, 'password', strip=False)
        return username, password
    
    @staticmethod
    def prepare_join_session_data(form: Form) -> Tuple[str, str]:
        """
        Extract and prepare join session data from form.
        
        Args:
            form: Join form instance
            
        Returns:
            Tuple of (pin, nickname)
        """
        pin = FormUtils.extract_string_field(form, 'pin')
        nickname = FormUtils.extract_string_field(form, 'nickname')
        return pin, nickname
    
    @staticmethod
    def prepare_presentation_data(form: Form) -> Tuple[str, str, str]:
        """
        Extract and prepare presentation data from form.
        
        Args:
            form: Presentation form instance
            
        Returns:
            Tuple of (title, description, status)
        """
        title = FormUtils.extract_string_field(form, 'title', default="Untitled")
        description = FormUtils.extract_string_field(form, 'description')
        status = FormUtils.extract_string_field(form, 'status').lower()
        return title, description, status
    
    @staticmethod
    def flash_form_validation_errors(form: Form) -> None:
        """
        Flash form validation errors to the user.
        
        Args:
            form: WTForms form instance with validation errors
        """
        from flask import flash
        from config.constants import FLASH_ERROR
        
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", FLASH_ERROR)
