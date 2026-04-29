"""
utils/file_utils.py — File operation utilities.

Provides centralized, safe file operations with consistent error handling
for the application's file-based storage system.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from config.constants import JSON_EXTENSION


class FileOperationError(Exception):
    """Base exception for file operation errors."""
    pass


class FileNotFoundError(FileOperationError):
    """Raised when a required file is not found."""
    pass


class FileCorruptedError(FileOperationError):
    """Raised when a file exists but contains invalid data."""
    pass


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory to create
        
    Raises:
        FileOperationError: If directory creation fails
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
    except OSError as e:
        raise FileOperationError(f"Failed to create directory {directory_path}: {e}")


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Safely read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file to read
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        FileCorruptedError: If the file contains invalid JSON
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FileCorruptedError(f"Invalid JSON in file {file_path}: {e}")
    except OSError as e:
        raise FileOperationError(f"Failed to read file {file_path}: {e}")


def write_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """
    Safely write data to a JSON file.
    
    Args:
        file_path: Path to write the JSON file
        data: Data to write (must be JSON serializable)
        indent: JSON indentation level
        
    Raises:
        FileOperationError: If the write operation fails
    """
    ensure_directory_exists(os.path.dirname(file_path))
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise FileCorruptedError(f"Data not JSON serializable for file {file_path}: {e}")
    except OSError as e:
        raise FileOperationError(f"Failed to write file {file_path}: {e}")


def delete_file(file_path: str) -> bool:
    """
    Safely delete a file if it exists.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if file was deleted, False if file didn't exist
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        os.remove(file_path)
        return True
    except OSError:
        return False


def list_json_files(directory_path: str) -> List[str]:
    """
    List all JSON files in a directory.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        List of JSON file paths (full paths)
    """
    if not os.path.exists(directory_path):
        return []
    
    json_files = []
    try:
        for filename in os.listdir(directory_path):
            if filename.endswith(JSON_EXTENSION):
                full_path = os.path.join(directory_path, filename)
                json_files.append(full_path)
    except OSError:
        # Return empty list if directory can't be read
        pass
    
    return json_files


def safe_read_json_files(directory_path: str) -> List[Dict[str, Any]]:
    """
    Safely read all JSON files in a directory, skipping corrupted files.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        List of parsed JSON data dictionaries
    """
    json_files = list_json_files(directory_path)
    valid_data = []
    
    for file_path in json_files:
        try:
            data = read_json_file(file_path)
            valid_data.append(data)
        except (FileNotFoundError, FileCorruptedError, FileOperationError):
            # Skip corrupted or unreadable files
            continue
    
    return valid_data


def get_timestamp_filename(base_name: str, extension: str = JSON_EXTENSION) -> str:
    """
    Generate a filename with timestamp.
    
    Args:
        base_name: Base name for the file
        extension: File extension (with or without dot)
        
    Returns:
        Filename with timestamp: base_name_YYYYMMDD_HHMMSS.ext
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}{extension}"
