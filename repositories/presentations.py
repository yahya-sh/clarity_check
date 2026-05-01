
from datetime import datetime, timezone
from typing import Dict, List, Optional

from models.presentation import Presentation
from repositories.base import UserSpecificRepository, NotFoundError, CorruptedDataError
from repositories import runs
from utils.path_utils import (
    get_user_presentations_dir,
    get_presentation_file_path,
    extract_username_from_path
)
from utils.file_utils import (
    read_json_file,
    write_json_file,
    delete_file,
    safe_read_json_files,
    FileOperationError,
    FileCorruptedError
)
from config.constants import JSON_EXTENSION


class PresentationsRepository(UserSpecificRepository):
    """
    Repository for presentation data operations.
    
    Handles CRUD operations for presentations with standardized
    error handling and file operations.
    """
    
    def get_by_id(self, presentation_id: str) -> Optional[Presentation]:
        """
        Get a presentation by its ID.
        
        Args:
            presentation_id: UUID of the presentation
            
        Returns:
            Presentation instance or None if not found
        """
        try:
            file_path = get_presentation_file_path(self.username, presentation_id)
            data = self._read_json_file(file_path)
            return Presentation.from_dict(data)
        except (NotFoundError, CorruptedDataError):
            return None
    
    def save(self, presentation: Presentation) -> Presentation:
        """
        Save a presentation to file.
        
        Args:
            presentation: Presentation instance to save
            
        Returns:
            Saved presentation instance
        """
        presentation.updated_at = datetime.now(timezone.utc)
        file_path = get_presentation_file_path(presentation.username, presentation.id)
        self._write_json_file(file_path, presentation.to_dict())
        return presentation
    
    def delete(self, presentation_id: str) -> bool:
        """
        Delete a presentation by ID.
        
        Args:
            presentation_id: UUID of the presentation
            
        Returns:
            True if deleted, False if not found
        """
        file_path = get_presentation_file_path(self.username, presentation_id)
        return self._delete_file(file_path)
    
    def list_all(self) -> List[Presentation]:
        """
        Get all presentations for the user.
        
        Returns:
            List of presentation instances
        """
        presentations_dir = get_user_presentations_dir(self.username)
        json_data_list = self._safe_read_json_files(presentations_dir)
        
        presentations = []
        for data in json_data_list:
            try:
                presentations.append(Presentation.from_dict(data))
            except (KeyError, ValueError):
                # Skip corrupted presentation data
                continue
        
        # Sort by creation date (newest first)
        presentations.sort(key=lambda p: p.created_at, reverse=True)
        return presentations
    
    @staticmethod
    def get_presentation_by_pin(pin_code: str) -> Optional[Presentation]:
        """
        Find a presentation by its PIN code across all users.
        
        Args:
            pin_code: The PIN code to search for
            
        Returns:
            Presentation instance if found and valid, None otherwise
        """
        if not pin_code or not pin_code.strip():
            return None
        
        pin_code = pin_code.strip()
        all_run_paths = runs.get_all_run_paths_across_users()
        
        for run_path in all_run_paths:
            try:
                run_data = read_json_file(run_path)
                
                if run_data.get('pin_code') == pin_code:
                    # Check if PIN is not expired
                    expires_at = run_data.get('expires_at')
                    if expires_at:
                        try:
                            expires_at_datetime = datetime.fromisoformat(expires_at)
                            if expires_at_datetime > datetime.now(timezone.utc):
                                # PIN is valid, load the presentation
                                presentation_uuid = run_data.get('presentation_uuid')
                                if presentation_uuid:
                                    username = extract_username_from_path(run_path)
                                    if username:
                                        return PresentationsRepository(username)._load_presentation_for_user(username, presentation_uuid)
                        except (ValueError, TypeError):
                            continue
            except (FileNotFoundError, FileOperationError):
                continue
        
        return None
    
    def _load_presentation_for_user(self, username: str, presentation_uuid: str) -> Optional[Presentation]:
        """
        Load a presentation for a specific user.
        
        Args:
            username: Username of the presentation owner
            presentation_uuid: UUID of the presentation
            
        Returns:
            Presentation instance or None if not found
        """
        try:
            file_path = get_presentation_file_path(username, presentation_uuid)
            data = read_json_file(file_path)
            return Presentation.from_dict(data)
        except (FileNotFoundError, FileCorruptedError, FileOperationError):
            return None



def load_presentation(username: str, presentation_id: str) -> Optional[Presentation]:
    """Load a specific presentation by ID"""
    return PresentationsRepository(username).get_by_id(presentation_id)

def get_user_presentations(username: str) -> List[Presentation]:
    """Get all presentations for a user"""
    return PresentationsRepository(username).list_all()

def save_presentation(presentation: Presentation) -> Presentation:
    """Save a presentation to file"""
    return PresentationsRepository(presentation.username).save(presentation)

def delete_presentation(username: str, presentation_id: str) -> bool:
    """Delete a presentation by ID"""
    return PresentationsRepository(username).delete(presentation_id)

def get_presentation_by_pin(pin_code: str) -> Optional[Presentation]:
    """Find a presentation by its PIN code across all users"""
    return PresentationsRepository.get_presentation_by_pin(pin_code)