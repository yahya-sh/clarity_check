
import json
import os
from datetime import datetime
from models.presentation import Presentation
from repositories import runs

def get_presentations_dir(username):
    """Get the presentations directory for a user"""
    return f"data/instructors/{username}/presentations"

def ensure_presentations_dir(username):
    """Ensure the presentations directory exists for a user"""
    presentations_dir = get_presentations_dir(username)
    os.makedirs(presentations_dir, exist_ok=True)
    return presentations_dir

def load_presentation(username, presentation_id):
    """Load a specific presentation by ID"""
    path = f"{get_presentations_dir(username)}/{presentation_id}.json"
    with open(path) as f:
        data = json.load(f)
        return Presentation.from_dict(data)

def get_user_presentations(username):
    """Get all presentations for a user"""
    presentations_dir = get_presentations_dir(username)
    if not os.path.exists(presentations_dir):
        return []
    
    presentations = []
    for filename in os.listdir(presentations_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(presentations_dir, filename)) as f:
                    data = json.load(f)
                    presentations.append(Presentation.from_dict(data))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    
    # Sort by creation date (newest first)
    presentations.sort(key=lambda p: p.created_at, reverse=True)
    return presentations

def save_presentation(presentation):
    """Save a presentation to file"""
    ensure_presentations_dir(presentation.username)
    path = f"{get_presentations_dir(presentation.username)}/{presentation.id}.json"
    
    presentation.updated_at = datetime.now()
    with open(path, 'w') as f:
        json.dump(presentation.to_dict(), f, indent=2)
    
    return presentation

def delete_presentation(username, presentation_id):
    """Delete a presentation by ID"""
    path = f"{get_presentations_dir(username)}/{presentation_id}.json"
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def get_presentation_by_pin(pin_code):
    """Find a presentation by its PIN code across all users
    
    Args:
        pin_code: The PIN code to search for
        
    Returns:
        Presentation object if found and valid, None otherwise
    """
    if not pin_code or not pin_code.strip():
        return None
    
    pin_code = pin_code.strip()
    all_run_paths = runs.get_all_run_paths_across_users()
    
    for run_path in all_run_paths:
        try:
            with open(run_path, 'r') as f:
                run_data = json.load(f)
            
            if run_data.get('pin_code') == pin_code:
                # Check if PIN is not expired
                expires_at = run_data.get('expires_at')
                if expires_at:
                    try:
                        expires_at_datetime = datetime.fromisoformat(expires_at)
                        if expires_at_datetime > datetime.now():
                            # PIN is valid, load the presentation
                            presentation_uuid = run_data.get('presentation_uuid')
                            if presentation_uuid:
                                # Extract username from the file path
                                # Path format: data/instructors/{username}/runs/{presentation_uuid}_{pin}.json
                                path_parts = run_path.split(os.sep)
                                if len(path_parts) >= 4 and path_parts[1] == 'instructors':
                                    username = path_parts[2]
                                    return load_presentation(username, presentation_uuid)
                    except (ValueError, TypeError):
                        continue
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    return None