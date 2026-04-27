import json
import os
from datetime import datetime

def get_runs_dir(username):
    """Get the runs directory for a user"""
    runs_dir = f"data/instructors/{username}/runs"
    os.makedirs(runs_dir, exist_ok=True)
    return runs_dir

def get_run_file_path(username, presentation_uuid):
    """Get the run file path for a presentation"""
    runs_dir = get_runs_dir(username)
    return f"{runs_dir}/{presentation_uuid}_pin.json"

def save_run_data(username, presentation_uuid, pin_code, expires_at):
    """Save run data to file"""
    run_file = get_run_file_path(username, presentation_uuid)
    run_data = {
        'presentation_uuid': presentation_uuid,
        'pin_code': pin_code,
        'expires_at': expires_at.isoformat() if expires_at else None,
        'created_at': datetime.now().isoformat(),
        'participants': []
    }
    
    with open(run_file, 'w') as f:
        json.dump(run_data, f, indent=2)
    
    return run_data

def load_run_data(username, presentation_uuid):
    """Load run data for a presentation"""
    run_file = get_run_file_path(username, presentation_uuid)
    
    if not os.path.exists(run_file):
        return None
    
    try:
        with open(run_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def delete_run_data(username, presentation_uuid):
    """Delete run data file"""
    run_file = get_run_file_path(username, presentation_uuid)
    if os.path.exists(run_file):
        os.remove(run_file)
        return True
    return False

def get_all_runs_for_user(username):
    """Get all run files for a user"""
    runs_dir = get_runs_dir(username)
    runs = []
    
    if not os.path.exists(runs_dir):
        return runs
    
    for filename in os.listdir(runs_dir):
        if filename.endswith('_pin.json'):
            try:
                filepath = os.path.join(runs_dir, filename)
                with open(filepath) as f:
                    run_data = json.load(f)
                    runs.append(run_data)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return runs

def pin_exists_for_user(username, pin_code):
    """Check if PIN code already exists for any of user's runs"""
    runs = get_all_runs_for_user(username)
    for run in runs:
        if run.get('pin_code') == pin_code:
            try:
                expires_at = datetime.fromisoformat(run.get('expires_at'))
                if expires_at > datetime.now():
                    return True  # PIN exists and is not expired
            except (ValueError, TypeError):
                continue
    return False

def cleanup_expired_runs(username):
    """Remove expired run files"""
    runs = get_all_runs_for_user(username)
    for run in runs:
        try:
            expires_at = datetime.fromisoformat(run.get('expires_at'))
            if expires_at <= datetime.now():
                # Extract presentation UUID from filename
                presentation_uuid = run.get('presentation_uuid')
                if presentation_uuid:
                    delete_run_data(username, presentation_uuid)
        except (ValueError, TypeError):
            continue
