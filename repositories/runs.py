"""
repositories/runs.py — File-based repository for presentation runs.

A **run** represents an active PIN session for a presentation: it records
the PIN code, expiry time, session UUID, and the list of participants who
have joined.  Each run is stored as a JSON file at
``data/instructors/{username}/runs/{presentation_uuid}_{pin_code}.json``.

Public API:
    :func:`save_run_data` — create or overwrite a run file.
    :func:`load_run_data` — find and load a run by presentation UUID.
    :func:`update_run_data` — patch specific fields in an existing run.
    :func:`delete_run_data` — remove a run file.
    :func:`rename_run_file` — atomically rename the file when PIN changes.
    :func:`join_participant` — register a new participant in a run.
    :func:`pin_exists` — global uniqueness check for a PIN.
    :func:`get_unexpired_run_by_pin` — look up a valid run by PIN.
    :func:`cleanup_expired_runs` — purge expired runs for a user.
"""
import os
import uuid
from datetime import datetime

from models.participant import Participant
from utils.path_utils import get_user_runs_dir, get_run_file_path
from utils.file_utils import (
    read_json_file,
    write_json_file,
    delete_file,
    ensure_directory_exists,
    FileOperationError,
)


def save_run_data(
    username: str,
    presentation_uuid: str,
    session_uuid: str,
    pin_code: str,
    expires_at: datetime,
    created_at: str = None,
    participants: list = None,
) -> dict:
    """
    Persist run data to a JSON file, overwriting any existing file.

    The filename encodes both the presentation UUID and PIN so that the
    file can be located by either value without a directory scan.

    Args:
        username: Instructor username.
        presentation_uuid: UUID of the presentation.
        session_uuid: UUID of the associated session (preserved across PIN
            renewals).
        pin_code: Current PIN code.
        expires_at: Expiry time as a ``datetime`` object.
        created_at: ISO-format creation timestamp; defaults to now.
        participants: Initial participant list; defaults to empty list.

    Returns:
        The run data dict that was written to disk.
    """
    runs_dir = get_user_runs_dir(username)
    ensure_directory_exists(runs_dir)
    run_file = get_run_file_path(username, presentation_uuid, pin_code)

    run_data = {
        'session_uuid': session_uuid,
        'presentation_uuid': presentation_uuid,
        'pin_code': pin_code,
        'expires_at': expires_at.isoformat(),
        'created_at': created_at if created_at else datetime.now().isoformat(),
        'username': username,
        'participants': participants if participants else [],
    }

    write_json_file(run_file, run_data)

    return run_data

def load_run_data(username: str, presentation_uuid: str) -> dict | None:
    """
    Find and load the run file for a presentation.

    Scans the user's runs directory for a file whose name starts with
    ``{presentation_uuid}_``.  The first valid match is returned.

    Args:
        username: Instructor username.
        presentation_uuid: UUID of the presentation to look up.

    Returns:
        The run data dict, or ``None`` if no matching file exists.
    """
    runs_dir = get_user_runs_dir(username)
    ensure_directory_exists(runs_dir)

    if not os.path.exists(runs_dir):
        return None

    for filename in os.listdir(runs_dir):
        if filename.startswith(f"{presentation_uuid}_") and filename.endswith('.json'):
            base_name = filename[:-5]  # Remove .json
            uuid_part = base_name.split("_")[0]
            if uuid_part == presentation_uuid:
                try:
                    filepath = os.path.join(runs_dir, filename)
                    return read_json_file(filepath)
                except FileOperationError:
                    continue

    return None

def delete_run_data(username: str, presentation_uuid: str) -> bool:
    """
    Delete the run file for a presentation.

    Args:
        username: Instructor username.
        presentation_uuid: UUID of the presentation whose run should be
            deleted.

    Returns:
        ``True`` if the file was found and deleted, ``False`` otherwise.
    """
    runs_dir = get_user_runs_dir(username)
    ensure_directory_exists(runs_dir)
    
    if not os.path.exists(runs_dir):
        return False
    
    # Find and delete the run file that starts with the presentation_uuid
    for filename in os.listdir(runs_dir):
        if filename.startswith(f"{presentation_uuid}_") and filename.endswith('.json'):
            filepath = os.path.join(runs_dir, filename)
            return delete_file(filepath)
    
    return False

def rename_run_file(username: str, presentation_uuid: str, old_pin_code: str, new_pin_code: str):
    """
    Atomically rename the run file when a PIN is refreshed.

    Loads the existing run data, updates ``pin_code`` to *new_pin_code*,
    writes a new file, then removes the old file.

    Args:
        username: Instructor username.
        presentation_uuid: UUID of the presentation.
        old_pin_code: Current PIN code (used to locate the file).
        new_pin_code: Replacement PIN code.

    Returns:
        ``(True, updated_run_data)`` on success, or
        ``(False, error_message_str)`` on failure.
    """
    runs_dir = get_user_runs_dir(username)
    ensure_directory_exists(runs_dir)
    old_file_path = get_run_file_path(username, presentation_uuid, old_pin_code)
    new_file_path = get_run_file_path(username, presentation_uuid, new_pin_code)

    if not os.path.exists(old_file_path):
        return False, "Old run file not found"

    try:
        run_data = read_json_file(old_file_path)
        run_data['pin_code'] = new_pin_code
        write_json_file(new_file_path, run_data)
        delete_file(old_file_path)
        return True, run_data
    except FileOperationError as e:
        return False, f"Error renaming run file: {str(e)}"


def update_run_data(username: str, presentation_uuid: str, pin_code: str, updates: dict) -> bool:
    """
    Patch specific fields in an existing run file.

    Loads the run file identified by *username*, *presentation_uuid*, and
    *pin_code*, merges *updates* into it, then writes the result back.
    This keeps all file I/O inside the repository layer.

    Args:
        username: Instructor username.
        presentation_uuid: UUID of the presentation.
        pin_code: Current PIN code (used to locate the file).
        updates: Dictionary of field-value pairs to merge into the run data.

    Returns:
        ``True`` if the file was updated successfully, ``False`` otherwise.
    """
    file_path = get_run_file_path(username, presentation_uuid, pin_code)
    if not os.path.exists(file_path):
        return False
    try:
        run_data = read_json_file(file_path)
        run_data.update(updates)
        write_json_file(file_path, run_data)
        return True
    except FileOperationError:
        return False

def get_all_runs_for_user(username: str) -> list:
    """
    Load all run dicts for *username* from disk.

    Args:
        username: Instructor username.

    Returns:
        List of run data dicts (may be empty).  Corrupt files are silently
        skipped.
    """
    runs_dir = get_user_runs_dir(username)
    ensure_directory_exists(runs_dir)
    runs = []

    if not os.path.exists(runs_dir):
        return runs

    for filename in os.listdir(runs_dir):
        if filename.endswith('.json'):
            try:
                filepath = os.path.join(runs_dir, filename)
                run_data = read_json_file(filepath)
                runs.append(run_data)
            except FileOperationError:
                continue

    return runs

def pin_exists(pin_code: str) -> bool:
    """
    Check whether *pin_code* is already active across all users' runs.

    A PIN is considered active if it exists in a run file whose ``expires_at``
    field is in the future.  Expired or corrupt files are skipped.

    Args:
        pin_code: The 6-digit PIN string to check.

    Returns:
        ``True`` if the PIN is already in use and unexpired, ``False``
        otherwise.
    """
    all_run_paths = get_all_run_paths_across_users()

    for run_path in all_run_paths:
        try:
            run_data = read_json_file(run_path)

            if run_data.get('pin_code') == pin_code:
                try:
                    expires_at = datetime.fromisoformat(run_data.get('expires_at'))
                    if expires_at > datetime.now():
                        return True  # PIN exists and is not expired
                except (ValueError, TypeError):
                    continue
        except FileOperationError:
            continue

    return False

def cleanup_expired_runs(username: str) -> None:
    """
    Delete all expired run files for *username*.

    Called at the start of :func:`~services.pin_service.get_or_renew_pin`
    to keep the runs directory tidy.

    Args:
        username: Instructor username.
    """
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
            run_data = read_json_file(run_path)
            
            if run_data.get('pin_code') == pin_code:
                # Check if the run is not expired
                try:
                    expires_at = datetime.fromisoformat(run_data.get('expires_at'))
                    if expires_at > datetime.now():
                        return run_data
                except (ValueError, TypeError):
                    # If no expiration or invalid format, return the run
                    return run_data
        except FileOperationError:
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
    """
    Register a new participant in a run and persist the change.

    Creates a :class:`~models.participant.Participant` object, strips
    session-level fields that are redundant in the run file (they are
    already implicit from the run record itself), appends the participant
    to the ``participants`` list, and saves the run file.

    Args:
        run: Run data dict as loaded from the JSON file.
        nickname: Display name chosen by the participant.

    Returns:
        The newly created :class:`~models.participant.Participant` instance.
    """
    participant = Participant(
        session_uuid=run['session_uuid'],
        nickname=nickname,
        presentation_uuid=run['presentation_uuid'],
        presentation_instructor_username=run['username'],
    )

    if 'participants' not in run:
        run['participants'] = []

    # Only store the fields that are meaningful in the run scope;
    # session_uuid, presentation_uuid, and instructor username are
    # already captured at the run level.
    participant_dict = participant.to_dict()
    participant_dict.pop('session_uuid')
    participant_dict.pop('presentation_uuid')
    participant_dict.pop('presentation_instructor_username')
    run['participants'].append(participant_dict)

    save_run_data(
        run['username'],
        run['presentation_uuid'],
        run['session_uuid'],
        run['pin_code'],
        datetime.fromisoformat(run['expires_at']),
        run['created_at'],
        run['participants'],
    )

    return participant
