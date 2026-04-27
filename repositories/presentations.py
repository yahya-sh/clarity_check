
import json
import os
from datetime import datetime
from models.presentation import Presentation

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