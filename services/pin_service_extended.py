"""
services/pin_service_extended.py — Extended PIN validation service.

Extends the existing pin_service with additional functionality for
PIN validation and presentation lookup, extracting logic from main routes.
"""

from typing import Optional, Tuple, Dict, Any

from repositories.presentations import get_presentation_by_pin
from repositories.runs import get_unexpired_run_by_pin
from repositories.base import NotFoundError
from models.presentation import Presentation
from config.constants import FLASH_ERROR


class PinServiceExtended:
    """
    Extended service class for PIN validation and presentation lookup.
    
    Provides additional functionality beyond the basic PIN generation
    and lifecycle management in the original pin_service.
    """
    
    @staticmethod
    def validate_pin(pin: str) -> Tuple[bool, Optional[str], Optional[Presentation]]:
        """
        Validate a PIN code and return associated presentation.
        
        Args:
            pin: The PIN code to validate
            
        Returns:
            Tuple of (is_valid, error_message, presentation)
            - is_valid: True if PIN is valid and presentation exists
            - error_message: Error message if invalid, None if valid
            - presentation: Presentation instance if valid, None if invalid
        """
        if not pin:
            return False, "PIN is required", None
        
        pin = pin.strip()
        if not pin:
            return False, "PIN is required", None
        
        presentation = get_presentation_by_pin(pin)
        if not presentation:
            return False, "Invalid PIN", None
        
        return True, None, presentation
    
    @staticmethod
    def get_presentation_info_for_pin(pin: str) -> Optional[Dict[str, Any]]:
        """
        Get presentation information for a valid PIN.
        
        Args:
            pin: The PIN code to look up
            
        Returns:
            Dictionary with presentation info or None if invalid
        """
        is_valid, error_message, presentation = PinServiceExtended.validate_pin(pin)
        
        if not is_valid or not presentation:
            return None
        
        return {
            'title': presentation.title or '',
            'description': presentation.description or '',
            'valid': True
        }
    
    @staticmethod
    def get_run_for_pin(pin: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Get the active run for a PIN code.
        
        Args:
            pin: The PIN code to look up
            
        Returns:
            Tuple of (found, error_message, run_data)
            - found: True if active run exists
            - error_message: Error message if not found, None if found
            - run_data: Run data dictionary if found, None if not found
        """
        if not pin:
            return False, "PIN is required", None
        
        pin = pin.strip()
        if not pin:
            return False, "PIN is required", None
        
        run = get_unexpired_run_by_pin(pin)
        if not run:
            return False, "Presentation not found with this PIN", None
        
        return True, None, run
    
    @staticmethod
    def validate_pin_for_join(pin: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate a PIN for participant joining.
        
        This method validates both the PIN and ensures there's an active
        run that participants can join.
        
        Args:
            pin: The PIN code to validate
            
        Returns:
            Tuple of (can_join, error_message, run_data)
            - can_join: True if PIN is valid and has active run
            - error_message: Error message if cannot join, None if can join
            - run_data: Run data dictionary if can join, None if cannot
        """
        return PinServiceExtended.get_run_for_pin(pin)
    
    @staticmethod
    def format_pin_validation_response(pin: str) -> Dict[str, Any]:
        """
        Format the response for PIN validation API endpoint.
        
        Args:
            pin: The PIN code to validate
            
        Returns:
            Response dictionary suitable for JSON API
        """
        is_valid, error_message, presentation = PinServiceExtended.validate_pin(pin)
        
        if not is_valid:
            return {
                'error': error_message
            }
        
        return {
            'title': presentation.title or '',
            'description': presentation.description or '',
            'valid': True
        }
    
    @staticmethod
    def get_pin_validation_error_message(pin: str) -> str:
        """
        Get the appropriate error message for PIN validation failure.
        
        Args:
            pin: The PIN code that failed validation
            
        Returns:
            Error message string
        """
        if not pin or not pin.strip():
            return "PIN is required"
        
        return "Invalid PIN"
    
    @staticmethod
    def get_join_error_message(pin: str) -> str:
        """
        Get the appropriate error message for join failure.
        
        Args:
            pin: The PIN code that failed join validation
            
        Returns:
            Error message string
        """
        if not pin or not pin.strip():
            return "PIN is required"
        
        return "Presentation not found with this PIN"
