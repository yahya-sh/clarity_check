"""
routes/questions.py — Question management routes.

Handles question CRUD operations within presentation objectives.
Extracted from instructor.py for better separation of concerns.
"""
from flask import Blueprint, render_template, flash, redirect, g, url_for, request, jsonify
from auth import require_instructor
from forms.question import SaveQuestionForm
from models.presentation import Presentation
from services.presentation_service import PresentationService
from services.question_service import QuestionService
from repositories.base import NotFoundError, ValidationError
from config.constants import FLASH_SUCCESS, FLASH_ERROR
from routes._helpers import _load_presentation_or_abort, _save_with_status_check

routes = Blueprint('questions', __name__)



@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions', methods=['POST'])
@require_instructor
def get_objective_questions_route(presentation_id, objective_id):
    """
    Return a JSON list of questions for a given objective.

    Used by the frontend editor to populate the questions panel without
    a full page reload.
    """
    username = g.user.username

    try:
        questions = PresentationService.get_objective_questions(
            presentation_id=presentation_id,
            username=username,
            objective_id=objective_id
        )
        return jsonify({'questions': questions})
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to load questions: {str(e)}'}), 500

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions/save', methods=['POST'])
@require_instructor
def save_question_route(presentation_id, objective_id):
    """
    Create or update a question within an objective.

    Accepts multipart/form-data submitted by the question editor modal.
    Validates the payload with :class:`~forms.question.SaveQuestionForm`,
    then either inserts a new question or updates the matching existing one.

    Returns a JSON response with ``{'success': True, 'question_id': ...}``
    or ``{'error': ...}`` on validation failure.
    """
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id, json_response=True)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    # instructor_username is passed for any context-sensitive validation.
    form = SaveQuestionForm(formdata=request.form, instructor_username=username)
    
    # Validate form using QuestionService
    is_valid, error_message = QuestionService.validate_question_form(form, objective_id)
    if not is_valid:
        return jsonify({'error': error_message}), 400

    # Extract question data using QuestionService
    question_data = QuestionService.extract_question_data_from_form(form)

    # Save question using QuestionService
    success, error_message, question_id = QuestionService.save_question_to_objective(
        presentation, objective_id, question_data, _save_with_status_check
    )

    if not success:
        return jsonify({'error': error_message}), 404

    return jsonify({'success': True, 'question_id': question_id})

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions/<question_id>/delete', methods=['POST'])
@require_instructor
def delete_question_route(presentation_id, objective_id, question_id):
    """Delete a question from an objective and re-sequence remaining orders."""
    username = g.user.username
    result = _load_presentation_or_abort(username, presentation_id)
    if not isinstance(result, Presentation):
        return result
    presentation = result

    # Delete question using QuestionService
    success, error_message = QuestionService.delete_question_from_objective(
        presentation, objective_id, question_id, _save_with_status_check
    )

    if not success:
        flash(error_message, FLASH_ERROR)
        return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))

    flash('Question deleted successfully.', FLASH_SUCCESS)
    return redirect(url_for('presentations.presentation_page', presentation_id=presentation_id))
