from flask import Blueprint, render_template, session, flash, redirect, g, url_for, request, jsonify
from functools import wraps
import uuid
from repositories import users_repo
from repositories.presentations import (
    get_user_presentations,
    save_presentation,
    delete_presentation,
    load_presentation,
)
from forms.question import SaveQuestionForm
from models.presentation import Presentation

routes = Blueprint('instructor', __name__)

def require_instructor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash('Please log in to access this page', 'info')
            return redirect('/login')
        
        # Verify user still exists in the database
        user = users_repo.get_user(username)
        if not user:
            g.user= None
            session.clear()
            flash('User not found. Please log in again.', 'info')
            return redirect('/login')
            
        return f(*args, **kwargs)
    return decorated_function


@routes.route('/dashboard')
@require_instructor
def dashboard():
    username = session.get('username')
    presentations = get_user_presentations(username)
    return render_template('instructor/dashboard.html', presentations=presentations)

@routes.route('/presentations/new', methods=['GET'])
@require_instructor
def create_presentation():
    username = session.get('username')
    presentation = Presentation(
        title='Untitled',
        description='',
        username=username,
        status='draft'
    )
    save_presentation(presentation)
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id, edit='true'))


@routes.route('/presentations/<presentation_id>', methods=['GET', 'POST'])
@require_instructor
def presentation_page(presentation_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        flash('Presentation not found.', 'error')
        return redirect(url_for('instructor.dashboard'))

    if request.method == 'POST':
        status_options = {'draft', 'published', 'archived'}
        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()
        status = (request.form.get('status') or '').strip().lower()

        if not title:
            title = 'Untitled'
        if status not in status_options:
            flash('Invalid status selected.', 'error')
            return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

        presentation.title = title
        presentation.description = description
        presentation.status = status
        save_presentation(presentation)
        flash('Presentation saved successfully.', 'success')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    presentation.objectives = sorted(objectives, key=lambda objective: objective.get('order', 0))
    return render_template('instructor/presentation.html', presentation=presentation)


@routes.route('/presentations/<presentation_id>/objectives/create', methods=['POST'])
@require_instructor
def create_objective_route(presentation_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        flash('Presentation not found.', 'error')
        return redirect(url_for('instructor.dashboard'))

    objective_text = (request.form.get('objective_text') or '').strip()
    if not objective_text:
        flash('Objective title cannot be empty.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

    if not isinstance(presentation.objectives, list):
        presentation.objectives = []

    next_order = max((objective.get('order', -1) for objective in presentation.objectives), default=-1) + 1
    presentation.objectives.append({
        'objective_id': str(uuid.uuid4()),
        'text': objective_text,
        'order': next_order,
        'questions': []
    })
    save_presentation(presentation)
    flash('Objective created successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/update', methods=['POST'])
@require_instructor
def update_objective_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        flash('Presentation not found.', 'error')
        return redirect(url_for('instructor.dashboard'))

    objective_text = (request.form.get('objective_text') or '').strip()
    if not objective_text:
        flash('Objective title cannot be empty.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    objective_found = False

    for objective in objectives:
        if objective.get('objective_id') == objective_id:
            objective['text'] = objective_text
            objective_found = True
            break

    if not objective_found:
        flash('Objective not found.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

    presentation.objectives = objectives
    save_presentation(presentation)
    flash('Objective updated successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/delete', methods=['POST'])
@require_instructor
def delete_objective_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        flash('Presentation not found.', 'error')
        return redirect(url_for('instructor.dashboard'))

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    filtered_objectives = [objective for objective in objectives if objective.get('objective_id') != objective_id]

    if len(filtered_objectives) == len(objectives):
        flash('Objective not found.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

    for index, objective in enumerate(sorted(filtered_objectives, key=lambda item: item.get('order', 0))):
        objective['order'] = index

    presentation.objectives = filtered_objectives
    save_presentation(presentation)
    flash('Objective deleted successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions', methods=['POST'])
@require_instructor
def get_objective_questions_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        return jsonify({'error': 'Presentation not found.'}), 404

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    objective = next((item for item in objectives if item.get('objective_id') == objective_id), None)
    if objective is None:
        return jsonify({'error': 'Objective not found.'}), 404

    questions = objective.get('questions', [])
    if not isinstance(questions, list):
        questions = []

    sorted_questions = sorted(questions, key=lambda question: question.get('order', 0))
    payload = []
    for question in sorted_questions:
        payload.append({
            'question_id': question.get('question_id'),
            'text': question.get('text', ''),
            'type': question.get('type', 'single_choice'),
            'choices': question.get('choices', []),
            'correct_indices': question.get('correct_indices', question.get('correct_indicies', [])),
            'points': question.get('points'),
            'time_limit': question.get('time_limit'),
            'order': question.get('order', 0),
        })

    return jsonify({'questions': payload})


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions/save', methods=['POST'])
@require_instructor
def save_question_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        return jsonify({'error': 'Presentation not found.'}), 404

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    objective = next((item for item in objectives if item.get('objective_id') == objective_id), None)
    if objective is None:
        return jsonify({'error': 'Objective not found.'}), 404

    questions = objective.get('questions', [])
    if not isinstance(questions, list):
        questions = []
        objective['questions'] = questions

    # Instructor username is passed to the form instance for context-sensitive validation/logic.
    form = SaveQuestionForm(formdata=request.form, meta={'csrf': False}, instructor_username=username)
    if not form.validate():
        first_error = next((errors[0] for errors in form.errors.values() if errors), 'Invalid question payload.')
        return jsonify({'error': first_error}), 400
    if (form.objective_id.data or '').strip() != objective_id:
        return jsonify({'error': 'Objective ID mismatch.'}), 400

    question_id = (form.question_id.data or '').strip()
    text = (form.text.data or '').strip()
    question_type = (form.type.data or '').strip().lower()
    clean_choices = form.cleaned_choices
    normalized_indices = form.cleaned_correct_indices
    points = form.points.data
    time_limit = form.time_limit.data

    existing_question = None
    if question_id:
        for question in questions:
            if question.get('question_id') == question_id:
                existing_question = question
                break
    else:
        question_id = str(uuid.uuid4())

    if existing_question is None:
        order = max((question.get('order', -1) for question in questions), default=-1) + 1

        questions.append({
            'question_id': question_id,
            'text': text,
            'type': question_type,
            'choices': clean_choices,
            'correct_indices': normalized_indices,
            'order': order,
            'points': points,
            'time_limit': time_limit,
        })
    else:
        existing_question['text'] = text
        existing_question['type'] = question_type
        existing_question['choices'] = clean_choices
        existing_question['correct_indices'] = normalized_indices
        existing_question['points'] = points
        existing_question['time_limit'] = time_limit

    save_presentation(presentation)
    return jsonify({'success': True, 'question_id': question_id})

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions/<question_id>/delete', methods=['POST'])
@require_instructor
def delete_question_route(presentation_id, objective_id, question_id):
    username = session.get('username')
    try:
        presentation = load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        flash('Presentation not found.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation_id))

    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    objective = next((item for item in objectives if item.get('objective_id') == objective_id), None)
    if objective is None:
        flash('Objective not found.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation_id))

    questions = objective.get('questions', [])
    if not isinstance(questions, list):
        questions = []
        objective['questions'] = questions

    filtered_questions = [question for question in questions if question.get('question_id') != question_id]

    if len(filtered_questions) == len(questions):
        flash('Question not found.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation_id))

    for index, question in enumerate(sorted(filtered_questions, key=lambda item: item.get('order', 0))):
        question['order'] = index

    objective['questions'] = filtered_questions
    save_presentation(presentation)
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation_id))


@routes.route('/presentations/<presentation_id>/delete', methods=['POST'])
@require_instructor
def delete_presentation_route(presentation_id):
    username = session.get('username')
    if delete_presentation(username, presentation_id):
        flash('Presentation deleted successfully!', 'success')
    else:
        flash('Presentation not found.', 'error')
    return redirect(url_for('instructor.dashboard'))
