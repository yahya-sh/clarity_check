from flask_wtf.csrf import CSRFProtect
from flask import Flask, redirect, flash, session, g, url_for
from functools import wraps
import os
from datetime import timedelta
from models.participant import Participant
from repositories import users_repo
from repositories.sessions import get_session_file_path, load_session

app = Flask(__name__)

# Configure Flask session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_PATH'] = '/'

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

def require_participant(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        participant_uuid = session.get('participant_uuid')
        participant_session_uuid = session.get('participant_session_uuid')
        participant_nickname = session.get('participant_nickname')
        presentation_uuid = session.get('presentation_uuid')
        presentation_instructor_username = session.get('presentation_instructor_username')
        if not participant_uuid or not participant_session_uuid or not participant_nickname or not presentation_uuid or not presentation_instructor_username:
            flash('Please join a session to access this page', 'info')
            return redirect(url_for('main.join_session'))
        
        session_data = load_session(presentation_instructor_username, presentation_uuid, participant_session_uuid)
        participant_exist_in_session = any(p.get('uuid') == participant_uuid for p in session_data.get('participants', []))
        if not session_data or not participant_exist_in_session:
            session.clear()
            flash('Session not found. Please join a session again.', 'error')
            return redirect(url_for('main.join_session'))
        
        session_data = get_session(presentation_instructor_username, presentation_uuid, participant_session_uuid)
        if session_data.get('status') != 'active':
            session.clear()
            flash('This session is not active.', 'info')
            return redirect(url_for('main.join_session'))
        
        # allow participant to access the page
        return f(*args, **kwargs)
        
    return decorated_function

@app.before_request
def add_auth_participant_to_context():
    participant_uuid = session.get('participant_uuid')
    participant_session_uuid = session.get('participant_session_uuid')
    participant_nickname = session.get('participant_nickname')
    presentation_uuid = session.get('presentation_uuid')
    presentation_instructor_username = session.get('presentation_instructor_username')
    if participant_uuid and participant_session_uuid and participant_nickname and presentation_uuid and presentation_instructor_username:
        g.participant = Participant(
            session_uuid=participant_session_uuid,
            nickname=participant_nickname,
            presentation_uuid=presentation_uuid,
            presentation_instructor_username=presentation_instructor_username,
            participant_uuid=participant_uuid
        )
    else:
        g.participant = None

@app.before_request
def add_auth_user_to_context():
    username = session.get('username')
    # Store user in Flask.g for request-scoped access
    if username:
        g.user = users_repo.get_user(username)
    else:
        g.user = None

@app.context_processor
def inject_current_user():
    """Make current_user available in all templates"""
    return {'current_user': getattr(g, 'user', None)}

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'insecure-bc054a63d0f9c2b537d4b0f6bebadb3630dd73495a140241')



