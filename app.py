"""
app.py — Flask application factory.

Creates and configures the Flask :data:`app` instance, registers CSRF
protection, sets up session security settings, and defines the
:func:`require_instructor` / :func:`require_participant` auth decorators
as well as ``before_request`` hooks that inject the current user /
participant into :data:`flask.g`.
"""
from flask_wtf.csrf import CSRFProtect
from flask import Flask, redirect, flash, session, g, url_for
from functools import wraps
import os
from datetime import timedelta

from repositories import users_repo
from utils.session_utils import (
    validate_instructor_session,
    validate_participant_session,
    populate_participant_in_context,
    populate_user_in_context,
    get_session_error_response,
    SessionValidationError
)
from config.constants import SESSION_LIFETIME_HOURS

app = Flask(__name__)

# ── Security ──────────────────────────────────────────────────────────────
# SECRET_KEY must be set before CSRFProtect is initialised so that CSRF
# token signing always uses the correct key.
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'insecure-bc054a63d0f9c2b537d4b0f6bebadb3630dd73495a140241'
)

# ── Session settings ──────────────────────────────────────────────────────
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=SESSION_LIFETIME_HOURS)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_PATH'] = '/'

csrf = CSRFProtect(app)


def require_instructor(f):
    """
    Route decorator that enforces an authenticated instructor session.

    Checks that a ``username`` key exists in the Flask session and that the
    corresponding user record still exists on disk.  On failure the session
    is cleared and the user is redirected to the login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            validate_instructor_session()
            return f(*args, **kwargs)
        except SessionValidationError as e:
            return get_session_error_response(str(e), 'auth.login')
    return decorated_function


def require_participant(f):
    """
    Route decorator that enforces an active participant session.

    Checks that all required participant session keys exist in the Flask
    session, that the participant is still registered in the live session
    file, and that the session status is ``'active'``.  On any failure
    the Flask session is cleared and the user is redirected to the join
    page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            validate_participant_session()
            return f(*args, **kwargs)
        except SessionValidationError as e:
            return get_session_error_response(str(e), 'participant.join_session')
    return decorated_function


@app.before_request
def add_auth_participant_to_context():
    """
    Populate ``g.participant`` before every request.

    Reads participant identity from the Flask session and constructs a
    :class:`~models.participant.Participant` instance so that downstream
    route handlers and decorators can reference ``g.participant`` directly.
    Set to ``None`` when no participant session is active.
    """
    populate_participant_in_context()


@app.before_request
def add_auth_user_to_context():
    """
    Populate ``g.user`` before every request.

    Looks up the instructor user from the file store using the username
    stored in the Flask session.  Set to ``None`` when not logged in.
    """
    populate_user_in_context()


@app.context_processor
def inject_current_user():
    """Make ``current_user`` available in all Jinja2 templates."""
    return {'current_user': getattr(g, 'user', None)}
