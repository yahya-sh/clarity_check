from functools import wraps

from utils.session_utils import SessionValidationError, get_session_error_response, validate_instructor_session, validate_participant_session


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
