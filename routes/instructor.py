from flask import Blueprint, render_template, session, flash, redirect, g, url_for, request, jsonify, make_response
from functools import wraps
import uuid
import random
import string
from datetime import datetime, timedelta
import qrcode
import io
import base64
from repositories import users_repo, runs_repo, presentations_repo

from forms.question import SaveQuestionForm
from models.presentation import Presentation

routes = Blueprint('instructor', __name__)

def generate_pin_code():
    """Generate a 6-digit PIN code"""
    return ''.join(random.choices(string.digits, k=6))

def get_or_create_pin(presentation: Presentation):
    """Get existing PIN or create new one if expired or missing"""
    username = presentation.username
    presentation_uuid = presentation.id
    now = datetime.now()
    
    # Cleanup expired runs first
    runs_repo.cleanup_expired_runs(username)
    
    # Check if run already exists for this presentation
    run_data = runs_repo.load_run_data(username, presentation_uuid)
    if run_data:
        try:
            expires_at = datetime.fromisoformat(run_data.get('expires_at'))
            if expires_at > now:
                return run_data.get('pin_code')
        except (ValueError, TypeError):
            pass
    
    # Generate unique PIN
    pin = generate_unique_pin()
    expires_at = now + timedelta(minutes=30)
    
    # Save run data
    runs_repo.save_run_data(username, presentation_uuid, pin, expires_at)
    
    return pin

def generate_unique_pin():
    """Generate a unique PIN code"""
    max_attempts = 100
    attempts = 0
    
    while attempts < max_attempts:
        pin = generate_pin_code()
        if not runs_repo.pin_exists(pin):
            return pin
        attempts += 1
    
    # If we can't generate unique PIN after many attempts, raise exception
    raise Exception("Unable to generate unique PIN after multiple attempts")

def generate_qr_code(join_url):
    """Generate QR code for the join URL"""
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(join_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def require_instructor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash('Please log in to access this page', 'info')
            return redirect(url_for('auth.login'))
        
        # Verify user still exists in the database
        user = users_repo.get_user(username)
        if not user:
            g.user= None
            session.clear()
            flash('User not found. Please log in again.', 'info')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function


@routes.route('/dashboard')
@require_instructor
def dashboard():
    username = session.get('username')
    presentations = presentations_repo.get_user_presentations(username)
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
    presentations_repo.save_presentation(presentation)
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id, edit='true'))


@routes.route('/presentations/<presentation_id>', methods=['GET', 'POST'])
@require_instructor
def presentation_page(presentation_id):
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
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

        # Validate publishing requirements
        if status == 'published':
            can_publish, error_message = presentation.can_be_published()
            if not can_publish:
                flash(error_message, 'error')
                return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))

        presentation.title = title
        presentation.description = description
        presentation.status = status
        
        # Check if presentation needs to be converted to draft after changes
        status_changed, message = presentation.validate_and_fix_status()
        if status_changed:
            flash(message, 'warning')
        
        presentations_repo.save_presentation(presentation)
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
        presentation = presentations_repo.load_presentation(username, presentation_id)
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
    
    # Check if presentation needs to be converted to draft
    status_changed, message = presentation.validate_and_fix_status()
    if status_changed:
        flash(message, 'warning')
    
    presentations_repo.save_presentation(presentation)
    flash('Objective created successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/update', methods=['POST'])
@require_instructor
def update_objective_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
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
    
    # Check if presentation needs to be converted to draft
    status_changed, message = presentation.validate_and_fix_status()
    if status_changed:
        flash(message, 'warning')
    
    presentations_repo.save_presentation(presentation)
    flash('Objective updated successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/delete', methods=['POST'])
@require_instructor
def delete_objective_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
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
    
    # Check if presentation needs to be converted to draft
    status_changed, message = presentation.validate_and_fix_status()
    if status_changed:
        flash(message, 'warning')
    
    presentations_repo.save_presentation(presentation)
    flash('Objective deleted successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions', methods=['POST'])
@require_instructor
def get_objective_questions_route(presentation_id, objective_id):
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
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
        presentation = presentations_repo.load_presentation(username, presentation_id)
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
    form = SaveQuestionForm(formdata=request.form, instructor_username=username)
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

    # Check if presentation needs to be converted to draft
    status_changed, message = presentation.validate_and_fix_status()
    if status_changed:
        # Save the presentation to update the status
        presentations_repo.save_presentation(presentation)
        return jsonify({'success': True, 'question_id': question_id, 'warning': message})

    presentations_repo.save_presentation(presentation)
    return jsonify({'success': True, 'question_id': question_id})

@routes.route('/presentations/<presentation_id>/objectives/<objective_id>/questions/<question_id>/delete', methods=['POST'])
@require_instructor
def delete_question_route(presentation_id, objective_id, question_id):
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
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
    
    # Check if presentation needs to be converted to draft
    status_changed, message = presentation.validate_and_fix_status()
    if status_changed:
        flash(message, 'warning')
    
    presentations_repo.save_presentation(presentation)
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation_id))


@routes.route('/presentations/<presentation_id>/delete', methods=['POST'])
@require_instructor
def delete_presentation_route(presentation_id):
    username = session.get('username')
    if presentations_repo.delete_presentation(username, presentation_id):
        flash('Presentation deleted successfully!', 'success')
    else:
        flash('Presentation not found.', 'error')
    return redirect(url_for('instructor.dashboard'))


@routes.route('/presentations/<presentation_id>/run', methods=['GET'])
@require_instructor
def run_presentation(presentation_id):
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        flash('Presentation not found.', 'error')
        return redirect(url_for('instructor.dashboard'))
    
    # Check if presentation is published
    if presentation.status != 'published':
        flash('Presentation must be published to run a session.', 'error')
        return redirect(url_for('instructor.presentation_page', presentation_id=presentation_id))
    
    # Get or create PIN
    pin = get_or_create_pin(presentation)
    
    # Generate join URL and QR code
    join_url = url_for('main.join_session', pin=pin, _external=True)
    qr_code_data = generate_qr_code(join_url)
    
    # Calculate presentation stats
    objectives = presentation.objectives if isinstance(presentation.objectives, list) else []
    total_questions = sum(len(obj.get('questions', [])) for obj in objectives)
    
    # Calculate estimated duration using the presentation method
    estimated_duration = presentation.calculate_estimated_duration()
    
    # Get participants from run data
    run_data = runs_repo.load_run_data(username, presentation_id)
    participants = run_data.get('participants', []) if run_data else []
    
    return render_template('instructor/run.html', 
                         presentation=presentation,
                         pin=pin,
                         join_url=join_url,
                         qr_code=qr_code_data,
                         objectives_count=len(objectives),
                         questions_count=total_questions,
                         estimated_duration=estimated_duration,
                         participants=participants)


@routes.route('/presentations/<presentation_id>/refresh-pin', methods=['POST'])
@require_instructor
def refresh_pin(presentation_id):
    """Refresh the PIN code for a presentation"""
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        return jsonify({'error': 'Presentation not found.'}), 404
    
    # Check if presentation is published
    if presentation.status != 'published':
        return jsonify({'error': 'Presentation must be published to refresh PIN.'}), 400
    
    # Generate new PIN and expiration
    pin = generate_unique_pin(username)
    expires_at = datetime.now() + timedelta(minutes=30)
    
    # Save new run data
    runs_repo.save_run_data(username, presentation_id, pin, expires_at)
    
    # Generate new join URL and QR code
    join_url = url_for('main.join_session', pin=pin, _external=True)
    qr_code_data = generate_qr_code(join_url)
    
    return jsonify({
        'pin': pin,
        'expires_at': expires_at.isoformat(),
        'join_url': join_url,
        'qr_code': qr_code_data
    })


@routes.route('/presentations/<presentation_id>/pin-status', methods=['GET'])
@require_instructor
def pin_status(presentation_id):
    """Get the current PIN status and expiration time"""
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        return jsonify({'error': 'Presentation not found.'}), 404
    
    # Get current run data
    run_data = runs_repo.load_run_data(username, presentation_id)
    if not run_data:
        return jsonify({'error': 'No active session found.'}), 404
    
    return jsonify({
        'pin': run_data.get('pin_code'),
        'expires_at': run_data.get('expires_at')
    })


@routes.route('/presentations/<presentation_id>/participants', methods=['GET'])
@require_instructor
def get_participants(presentation_id):
    """Get the current list of participants for a run"""
    username = session.get('username')
    try:
        presentation = presentations_repo.load_presentation(username, presentation_id)
    except (FileNotFoundError, KeyError, ValueError):
        return jsonify({'error': 'Presentation not found.'}), 404
    
    # Get current run data
    run_data = runs_repo.load_run_data(username, presentation_id)
    if not run_data:
        return jsonify({'participants': []})
    
    participants = run_data.get('participants', [])
    return jsonify({'participants': participants})
