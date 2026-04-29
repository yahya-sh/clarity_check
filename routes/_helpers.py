"""
routes/_helpers.py — Shared route helper functions.

Contains helper utilities used across multiple route modules to avoid
code duplication.
"""
from flask import flash, redirect, url_for, jsonify
from repositories import presentations_repo
from models.presentation import Presentation
from config.constants import FLASH_ERROR


def _load_presentation_or_abort(username: str, presentation_id: str, *, json_response: bool = False):
    """
    Load a presentation by presentation_id for username.

    On success returns a Presentation instance.
    On failure returns an appropriate Flask response — either a JSON error
    (when json_response is True) or a flash-and-redirect to the dashboard.
    """
    try:
        return presentations_repo.load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        if json_response:
            return jsonify({'error': 'Presentation not found.'}), 404
        flash('Presentation not found.', FLASH_ERROR)
        return redirect(url_for('dashboard.dashboard'))


def _save_with_status_check(presentation) -> str | None:
    """
    Validate-and-fix the presentation status, save it, and return a warning.

    If the presentation was automatically demoted from 'published' to
    'draft', the warning message is returned so the caller can surface it.
    """
    status_changed, message = presentation.validate_and_fix_status()
    presentations_repo.save_presentation(presentation)
    return message if status_changed else None
