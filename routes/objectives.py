"""
routes/objectives.py — Objective management routes.

Handles objective CRUD operations within presentations.
Extracted from instructor.py for better separation of concerns.
"""
from flask import Blueprint, render_template, flash, redirect, g, url_for, request
from app import require_instructor
from services.presentation_service import PresentationService
from repositories.base import NotFoundError, ValidationError
from config.constants import FLASH_SUCCESS, FLASH_ERROR

routes = Blueprint('objectives', __name__)

def _load_presentation_or_abort(username: str, presentation_id: str, *, json_response: bool = False):
    """
    Load a presentation by *presentation_id* for *username*.

    On success returns a :class:`~models.presentation.Presentation` instance.
    On failure returns an appropriate Flask response.
    """
    try:
        from repositories import presentations_repo
        return presentations_repo.load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        if json_response:
            from flask import jsonify
            return jsonify({'error': 'Presentation not found.'}), 404
        flash('Presentation not found.', FLASH_ERROR)
        return redirect(url_for('dashboard.dashboard'))

@routes.route('/presentations/<presentation_id>/objectives/create', methods=['POST'])
@require_instructor
def create_objective_route(presentation_id):
    """Create a new objective and append it to the presentation."""
    username = g.user.username
    objective_text = (request.form.get('objective_text') or '').strip()

    try:
        PresentationService.add_objective(
            presentation_id=presentation_id,
            username=username,
            objective_text=objective_text
        )
        flash('Objective created successfully.', FLASH_SUCCESS)
    except ValidationError as e:
        flash(str(e), FLASH_ERROR)
    except Exception as e:
        flash(f'Failed to create objective: {str(e)}', FLASH_ERROR)

    return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/update', methods=['POST'])
@require_instructor
def update_objective_route(presentation_id, objective_id):
    """Update the text of an existing objective."""
    username = g.user.username
    objective_text = (request.form.get('objective_text') or '').strip()

    try:
        PresentationService.update_objective(
            presentation_id=presentation_id,
            username=username,
            objective_id=objective_id,
            objective_text=objective_text
        )
        flash('Objective updated successfully.', FLASH_SUCCESS)
    except (NotFoundError, ValidationError) as e:
        flash(str(e), FLASH_ERROR)
    except Exception as e:
        flash(f'Failed to update objective: {str(e)}', FLASH_ERROR)

    return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/delete', methods=['POST'])
@require_instructor
def delete_objective_route(presentation_id, objective_id):
    """Delete an objective and re-sequence the remaining objectives' order values."""
    username = g.user.username

    try:
        PresentationService.delete_objective(
            presentation_id=presentation_id,
            username=username,
            objective_id=objective_id
        )
        flash('Objective deleted successfully.', FLASH_SUCCESS)
    except NotFoundError as e:
        flash(str(e), FLASH_ERROR)
    except Exception as e:
        flash(f'Failed to delete objective: {str(e)}', FLASH_ERROR)

    return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))
