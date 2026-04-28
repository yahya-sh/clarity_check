import json
import os
import uuid
from datetime import datetime

from models.participant import Participant

def get_user_runs(username):
    """Get the runs directory for a user"""
    runs_dir = f"data/instructors/{username}/runs"
    os.makedirs(runs_dir, exist_ok=True)
    return runs_dir

def get_run_file_path(username, presentation_uuid, pin_code):
    """Get the run file path for a presentation"""
    runs_dir = get_user_runs(username)
    return f"{runs_dir}/{presentation_uuid}_{pin_code}.json"

def save_run_data(username, presentation_uuid, pin_code, expires_at: datetime, created_at: str = None, participants: list = None):
    """Save run data to file"""
    run_file = get_run_file_path(username, presentation_uuid, pin_code)
    
    run_data = {
        'session_uuid': str(uuid.uuid4()),
        'presentation_uuid': presentation_uuid,
        'pin_code': pin_code,
        'expires_at': expires_at.isoformat(),
        'created_at': created_at if created_at else datetime.now().isoformat(),
        'username': username,
        'participants': participants if participants else []
    }
    
    with open(run_file, 'w') as f:
        json.dump(run_data, f, indent=2)
    
    return run_data

def load_run_data(username, presentation_uuid):
    """Load run data for a presentation by finding first run that starts with the UUID"""
    runs_dir = get_user_runs(username)
    
    if not os.path.exists(runs_dir):
        return None
    
    # Find first file that starts with the presentation_uuid followed by underscore
    for filename in os.listdir(runs_dir):
        if filename.startswith(f"{presentation_uuid}_") and filename.endswith('.json'):
            # Extract UUID part by removing the last underscore and extension
            base_name = filename[:-5]  # Remove .json
            uuid_part = base_name.split("_")[0]
            if uuid_part == presentation_uuid:
                try:
                    filepath = os.path.join(runs_dir, filename)
                    with open(filepath) as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
    
    return None

def delete_run_data(username, presentation_uuid):
    """Delete run data file"""
    run_file = get_run_file_path(username, presentation_uuid)
    if os.path.exists(run_file):
        try:
            os.remove(run_file)
            return True
        except:
            return False
    return False

def rename_run_file(username, presentation_uuid, old_pin_code, new_pin_code):
    """Rename run file from old PIN to new PIN and update the PIN code in the file"""
    runs_dir = get_user_runs(username)
    old_file_path = f"{runs_dir}/{presentation_uuid}_{old_pin_code}.json"
    new_file_path = f"{runs_dir}/{presentation_uuid}_{new_pin_code}.json"
    
    if not os.path.exists(old_file_path):
        return False, "Old run file not found"
    
    try:
        # Load the existing run data
        with open(old_file_path, 'r') as f:
            run_data = json.load(f)
        
        # Update the PIN code in the data but preserve session_uuid
        run_data['pin_code'] = new_pin_code
        
        # Save to new file with updated PIN (session_uuid remains unchanged)
        with open(new_file_path, 'w') as f:
            json.dump(run_data, f, indent=2)
        
        # Remove the old file
        os.remove(old_file_path)
        
        return True, run_data
    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        return False, f"Error renaming run file: {str(e)}"

def get_all_runs_for_user(username: str) -> list:
    """Get all run files for a user"""
    runs_dir = get_user_runs(username)
    runs = []
    
    if not os.path.exists(runs_dir):
        return runs
    
    for filename in os.listdir(runs_dir):
        if filename.endswith('.json'):
            try:
                filepath = os.path.join(runs_dir, filename)
                with open(filepath) as f:
                    run_data = json.load(f)
                    runs.append(run_data)
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    return runs

def pin_exists(pin_code):
    """Check if PIN code already exists across all users' runs"""
    all_run_paths = get_all_run_paths_across_users()
    
    for run_path in all_run_paths:
        try:
            with open(run_path, 'r') as f:
                run_data = json.load(f)
                
            if run_data.get('pin_code') == pin_code:
                try:
                    expires_at = datetime.fromisoformat(run_data.get('expires_at'))
                    if expires_at > datetime.now():
                        return True  # PIN exists and is not expired
                except (ValueError, TypeError):
                    continue
        except (json.JSONDecodeError, FileNotFoundError):
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

def get_unexpired_run_by_pin(pin_code):
    """Get unexpired run data by PIN code across all users"""
    all_run_paths = get_all_run_paths_across_users()
    
    for run_path in all_run_paths:
        try:
            with open(run_path, 'r') as f:
                run_data = json.load(f)
                
            if run_data.get('pin_code') == pin_code:
                # Check if the run is not expired
                try:
                    expires_at = datetime.fromisoformat(run_data.get('expires_at'))
                    if expires_at > datetime.now():
                        return run_data
                except (ValueError, TypeError):
                    # If no expiration or invalid format, return the run
                    return run_data
        except (json.JSONDecodeError, FileNotFoundError):
            continue
    
    return None

def get_all_run_paths_across_users():
    """Get all run file paths across all users"""
    all_run_paths = []
    instructors_dir = "data/instructors"
    
    if not os.path.exists(instructors_dir):
        return all_run_paths
    
    # Iterate through all user directories
    for username in os.listdir(instructors_dir):
        user_dir = os.path.join(instructors_dir, username)
        if os.path.isdir(user_dir):
            runs_dir = os.path.join(user_dir, "runs")
            if os.path.exists(runs_dir):
                # Get all JSON files in the runs directory
                for filename in os.listdir(runs_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(runs_dir, filename)
                        all_run_paths.append(filepath)
    
    return all_run_paths

def join_participant(run: dict, nickname: str) -> Participant:
    """Create a participant, add them to the run, and return the participant object"""
    # Create participant object with session_uuid from run
    participant = Participant(
        session_uuid=run['session_uuid'],
        nickname=nickname
    )
    
    # Add participant to run's participants list
    if 'participants' not in run:
        run['participants'] = []
    
    run['participants'].append(participant.to_dict())
    save_run_data(run['username'], run['presentation_uuid'], run['pin_code'], datetime.fromisoformat(run['expires_at']), run['created_at'], run['participants'])
    
    return participant
    
