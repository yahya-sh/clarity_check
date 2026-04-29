"""
repositories/base.py — Base repository class and common patterns.

Provides a foundation for all repository classes with standardized
error handling, file operations, and common patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.file_utils import (
    read_json_file,
    write_json_file,
    delete_file,
    safe_read_json_files,
    ensure_directory_exists,
    FileOperationError,
    FileNotFoundError,
    FileCorruptedError
)
from utils.path_utils import get_user_dir


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class NotFoundError(RepositoryError):
    """Raised when a requested resource is not found."""
    pass


class CorruptedDataError(RepositoryError):
    """Raised when stored data is corrupted or invalid."""
    pass


class ValidationError(RepositoryError):
    """Raised when data validation fails."""
    pass


class BaseRepository(ABC):
    """
    Base class for all repositories providing common functionality.
    
    This class standardizes file operations, error handling, and
    common patterns used across all repository implementations.
    """
    
    def __init__(self, username: Optional[str] = None):
        """
        Initialize repository.
        
        Args:
            username: Username for user-specific repositories
        """
        self.username = username
        if username:
            self._ensure_user_directory()
    
    def _ensure_user_directory(self) -> None:
        """Ensure the user's directory exists."""
        if self.username:
            ensure_directory_exists(get_user_dir(self.username))
    
    def _read_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Safely read a JSON file with standardized error handling.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            NotFoundError: If file is not found
            CorruptedDataError: If file contains invalid data
        """
        try:
            return read_json_file(file_path)
        except FileNotFoundError as e:
            raise NotFoundError(str(e))
        except FileCorruptedError as e:
            raise CorruptedDataError(str(e))
        except FileOperationError as e:
            raise RepositoryError(f"Failed to read file {file_path}: {e}")
    
    def _write_json_file(self, file_path: str, data: Dict[str, Any]) -> None:
        """
        Safely write data to a JSON file with standardized error handling.
        
        Args:
            file_path: Path to write the JSON file
            data: Data to write
            
        Raises:
            RepositoryError: If write operation fails
        """
        try:
            write_json_file(file_path, data)
        except FileOperationError as e:
            raise RepositoryError(f"Failed to write file {file_path}: {e}")
    
    def _delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted, False if it didn't exist
        """
        return delete_file(file_path)
    
    def _safe_read_json_files(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Safely read all JSON files in a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            List of valid JSON data dictionaries
        """
        return safe_read_json_files(directory_path)
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that required fields are present in data.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def _add_timestamps(self, data: Dict[str, Any], created_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Add timestamps to data dictionary.
        
        Args:
            data: Data dictionary to modify
            created_at: Optional creation timestamp (defaults to now)
            
        Returns:
            Modified data dictionary with timestamps
        """
        now = datetime.now().isoformat()
        
        if created_at:
            data['created_at'] = created_at
            data['updated_at'] = now
        else:
            data['created_at'] = now
            data['updated_at'] = now
        
        return data
    
    def _update_timestamp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the updated_at timestamp in data dictionary.
        
        Args:
            data: Data dictionary to modify
            
        Returns:
            Modified data dictionary with updated timestamp
        """
        data['updated_at'] = datetime.now().isoformat()
        return data
    
    @abstractmethod
    def get_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a resource by its ID.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            Resource data dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a resource.
        
        Args:
            data: Resource data to save
            
        Returns:
            Saved resource data
        """
        pass
    
    @abstractmethod
    def delete(self, resource_id: str) -> bool:
        """
        Delete a resource by its ID.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all resources for this repository.
        
        Returns:
            List of resource data dictionaries
        """
        pass


class UserSpecificRepository(BaseRepository):
    """
    Base class for user-specific repositories.
    
    Extends BaseRepository with user-specific functionality and
    ensures username is always provided.
    """
    
    def __init__(self, username: str):
        """
        Initialize user-specific repository.
        
        Args:
            username: Username for the repository
            
        Raises:
            ValidationError: If username is not provided
        """
        if not username:
            raise ValidationError("Username is required for user-specific repositories")
        
        super().__init__(username)
    
    def _get_user_file_path(self, filename: str) -> str:
        """
        Get the full path for a user-specific file.
        
        Args:
            filename: Name of the file
            
        Returns:
            Full file path
        """
        return f"{get_user_dir(self.username)}/{filename}"
