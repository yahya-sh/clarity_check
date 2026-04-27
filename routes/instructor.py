from flask import Blueprint, render_template, session, flash, redirect, g, url_for, request
from functools import wraps
import uuid
from repositories import users_repo
from repositories.presentations import (
    get_user_presentations,
    save_presentation,
    delete_presentation,
    load_presentation,
)
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

@routes.route('/presentations/<presentation_id>/delete', methods=['POST'])
@require_instructor
def delete_presentation_route(presentation_id):
    username = session.get('username')
    if delete_presentation(username, presentation_id):
        flash('Presentation deleted successfully!', 'success')
    else:
        flash('Presentation not found.', 'error')
    return redirect(url_for('instructor.dashboard'))
