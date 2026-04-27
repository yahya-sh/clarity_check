from flask import Blueprint, render_template, session, flash, redirect, g, url_for, request
from functools import wraps
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
    return redirect(url_for('instructor.presentation_page', presentation_id=presentation.id))


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

    return render_template('instructor/presentation.html', presentation=presentation)

@routes.route('/presentations/<presentation_id>/delete', methods=['POST'])
@require_instructor
def delete_presentation_route(presentation_id):
    username = session.get('username')
    if delete_presentation(username, presentation_id):
        flash('Presentation deleted successfully!', 'success')
    else:
        flash('Presentation not found.', 'error')
    return redirect(url_for('instructor.dashboard'))
