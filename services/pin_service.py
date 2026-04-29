"""
services/pin_service.py — PIN code generation and lifecycle management.

Responsibilities
----------------
- Generate cryptographically-safe random 6-digit PIN codes.
- Guarantee global uniqueness across all active runs.
- Determine whether an existing PIN is still valid or needs renewal.
- Coordinate PIN renewal (atomic file rename + expiry update) via the
  :mod:`repositories.runs` repository.

This module contains **no HTTP or Flask-specific code**; it receives and
returns plain Python values so it can be tested independently.
"""
import uuid
import random
import string
from datetime import datetime, timedelta

from repositories import runs_repo

# How long a newly created or refreshed PIN stays valid.
PIN_LIFETIME_MINUTES: int = 30

# Upper bound on generation attempts before raising.
_MAX_PIN_ATTEMPTS: int = 100


def generate_pin_code() -> str:
    """
    Generate a random 6-digit numeric PIN code string.

    Returns:
        A string of exactly 6 decimal digits, e.g. ``'047312'``.
    """
    return ''.join(random.choices(string.digits, k=6))


def generate_unique_pin() -> str:
    """
    Generate a PIN code that does not collide with any active run globally.

    Calls :func:`generate_pin_code` in a loop and checks each candidate
    against :func:`~repositories.runs.pin_exists` until a unique value is
    found or ``_MAX_PIN_ATTEMPTS`` is exhausted.

    Returns:
        A unique 6-digit PIN string.

    Raises:
        RuntimeError: If a unique PIN cannot be generated after
            :data:`_MAX_PIN_ATTEMPTS` attempts (should be astronomically
            rare with 1 000 000 possible codes).
    """
    for _ in range(_MAX_PIN_ATTEMPTS):
        pin = generate_pin_code()
        if not runs_repo.pin_exists(pin):
            return pin
    raise RuntimeError(
        f"Unable to generate a unique PIN after {_MAX_PIN_ATTEMPTS} attempts."
    )


def get_or_renew_pin(username: str, presentation_id: str) -> str:
    """
    Return the current valid PIN for a presentation, renewing it if expired.

    Behaviour
    ---------
    1. Cleans up any expired runs for *username*.
    2. If a run file already exists for *presentation_id*:
       - Returns the existing PIN if it has not expired.
       - Renames the file with a new PIN and updates the expiry otherwise.
    3. If no run file exists, creates a brand-new run (new PIN + new
       ``session_uuid``).

    All file I/O is delegated to :mod:`repositories.runs`.

    Args:
        username: Instructor username (used to locate the runs directory).
        presentation_id: UUID of the presentation.

    Returns:
        The active 6-digit PIN string.
    """
    now = datetime.now()
    expires_delta = timedelta(minutes=PIN_LIFETIME_MINUTES)

    # Remove stale run files first so they don't pollute uniqueness checks.
    runs_repo.cleanup_expired_runs(username)

    run_data = runs_repo.load_run_data(username, presentation_id)

    if run_data:
        try:
            expires_at = datetime.fromisoformat(run_data['expires_at'])
            if expires_at > now:
                # Still valid — return the existing PIN unchanged.
                return run_data['pin_code']

            # Expired — rename the file to a fresh PIN, preserve session_uuid.
            old_pin = run_data['pin_code']
            new_pin = generate_unique_pin()
            new_expires_at = now + expires_delta

            success, result = runs_repo.rename_run_file(
                username, presentation_id, old_pin, new_pin
            )
            if success:
                # result is the updated run_data dict returned by rename_run_file.
                runs_repo.update_run_data(
                    username, presentation_id, new_pin,
                    {'expires_at': new_expires_at.isoformat()}
                )
            else:
                # Rename failed — fall back to creating a fresh run file,
                # but preserve the existing session_uuid so participants
                # already holding it are not orphaned.
                session_uuid = run_data.get('session_uuid', str(uuid.uuid4()))
                runs_repo.save_run_data(
                    username, presentation_id, session_uuid, new_pin, new_expires_at
                )
            return new_pin

        except (ValueError, TypeError):
            # Corrupted expiry field — fall through to create a new run.
            pass

    # No run exists (or corrupted) — create a brand-new one.
    new_pin = generate_unique_pin()
    new_expires_at = now + expires_delta
    session_uuid = str(uuid.uuid4())
    runs_repo.save_run_data(
        username, presentation_id, session_uuid, new_pin, new_expires_at
    )
    return new_pin


def refresh_pin(username: str, presentation_id: str) -> dict:
    """
    Generate a brand-new PIN for an existing run, clearing its participant list.

    Unlike :func:`get_or_renew_pin`, this is an **explicit** instructor action
    that always produces a fresh PIN regardless of whether the current one has
    expired.

    Args:
        username: Instructor username.
        presentation_id: UUID of the presentation.

    Returns:
        A dict with keys ``pin``, ``expires_at`` (ISO-format string),
        and ``join_url`` placeholder ``None`` (caller fills this in).

    Raises:
        ValueError: If no active run is found for the presentation.
        RuntimeError: If the file rename or update fails.
    """
    existing_run = runs_repo.load_run_data(username, presentation_id)
    if not existing_run:
        raise ValueError("No active run found for this presentation.")

    old_pin = existing_run.get('pin_code')
    if not old_pin:
        raise ValueError("Existing run has no PIN code.")

    new_pin = generate_unique_pin()
    new_expires_at = datetime.now() + timedelta(minutes=PIN_LIFETIME_MINUTES)

    success, result = runs_repo.rename_run_file(
        username, presentation_id, old_pin, new_pin
    )
    if not success:
        raise RuntimeError(f"Failed to rename run file: {result}")

    # Clear participants and set new expiry in the renamed file.
    runs_repo.update_run_data(
        username, presentation_id, new_pin,
        {
            'expires_at': new_expires_at.isoformat(),
            'participants': [],
        }
    )

    return {
        'pin': new_pin,
        'expires_at': new_expires_at.isoformat(),
    }
