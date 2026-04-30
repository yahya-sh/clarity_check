"""
services/pin_service_extended.py — Extended PIN validation service.

Extends the existing pin_service with additional functionality for
PIN validation and presentation lookup, extracting logic from main routes.
"""

from typing import Optional, Tuple, Dict, Any

from repositories.presentations import get_presentation_by_pin
from repositories.base import NotFoundError
from models.presentation import Presentation


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
    
        
    
