"""
routes/presentations.py — Presentation CRUD routes.

Handles presentation creation, reading, updating, and deletion operations.
Extracted from instructor.py for better separation of concerns.
"""
from flask import Blueprint, render_template, flash, redirect, g, url_for, request
from auth import require_instructor
from repositories import presentations_repo
from repositories.base import NotFoundError, ValidationError
from services.presentation_service import PresentationService
from utils.form_utils import FormUtils
from config.constants import FLASH_SUCCESS, FLASH_ERROR, FLASH_WARNING
from models.presentation import Presentation
from routes._helpers import _load_presentation_or_abort, _save_with_status_check

routes = Blueprint('presentations', __name__)



@routes.route('/presentations/new', methods=['GET'])
@require_instructor
def create_presentation():
    """Create a new blank presentation and redirect to its edit page."""
    try:
        presentation = PresentationService.create_presentation(
            username=g.user.username,
            title='Untitled',
            description=''
        )
        return redirect(url_for(
            'presentations.presentation_page',
            presentation_id=presentation.id,
            edit='true',
        ))
    except Exception as e:
        flash(f'Failed to create presentation: {str(e)}', FLASH_ERROR)
        return redirect(url_for('dashboard.dashboard'))

@routes.route('/presentations/<presentation_id>', methods=['GET', 'POST'])
@require_instructor
def presentation_page(presentation_id):
    """
    Display or update a single presentation.

    GET  — renders the presentation editor.
    POST — validates and saves title, description, and status changes.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    if request.method == 'POST':
        title, description, status = FormUtils.prepare_presentation_data(request.form)

        try:
            updated_presentation, warning = PresentationService.update_presentation_basic_info(
                presentation_id=presentation_id,
                username=username,
                title=title,
                description=description,
                status=status
            )

            if warning:
                flash(warning, FLASH_WARNING)

            flash('Presentation saved successfully.', FLASH_SUCCESS)
            return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))

        except ValidationError as e:
            flash(str(e), FLASH_ERROR)
            return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))
        except Exception as e:
            flash(f'Failed to save presentation: {str(e)}', FLASH_ERROR)
            return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    presentation.objectives = sorted(objectives, key=lambda o: o.get('order', 0))
    return render_template('instructor/presentation.html', presentation=presentation)

@routes.route('/presentations/<presentation_id>/delete', methods=['POST'])
@require_instructor
def delete_presentation_route(presentation_id):
    """Permanently delete a presentation and all its data."""
    if presentations_repo.delete_presentation(g.user.username, presentation_id):
        flash('Presentation deleted successfully!', FLASH_SUCCESS)
    else:
        flash('Presentation not found.', FLASH_ERROR)
    return redirect(url_for('dashboard.dashboard'))
