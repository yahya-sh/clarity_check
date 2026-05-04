from flask import Blueprint, flash, g, redirect, render_template, session, url_for

from config.constants import FLASH_ERROR, FLASH_SUCCESS
from forms.login import LoginForm
from forms.register import RegisterForm
from services.auth_service import AuthService
from utils.form_utils import FormUtils
from utils.session_utils import populate_participant_in_context, populate_user_in_context

################################################
############## Routes Setup ####################
################################################

router = Blueprint('auth', __name__)

@router.app_context_processor
def inject_current_user():
    """Make ``current_user`` available in all Jinja2 templates."""
    return {'current_user': getattr(g, 'user', None)}


@router.before_app_request
def add_auth_participant_to_context():
    """
    Populate ``g.participant`` before every request.

    Reads participant identity from the Flask session and constructs a
    :class:`~models.participant.Participant` instance so that downstream
    route handlers and decorators can reference ``g.participant`` directly.
    Set to ``None`` when no participant session is active.
    """
    populate_participant_in_context()


@router.before_app_request
def add_auth_user_to_context():
    """
    Populate ``g.user`` before every request.

    Looks up the instructor user from the file store using the username
    stored in the Flask session.  Set to ``None`` when not logged in.
    """
    populate_user_in_context()



################################################
############## Routes Start ####################
################################################

@router.route('/login', methods=['GET', 'POST'])
def login():
    """
    Render the login form (GET) or authenticate an instructor (POST).

    On success, stores ``username`` in the Flask session and redirects to
    the dashboard.  On failure, flashes an error and re-renders the form.
    """
    form = LoginForm()
    if form.validate_on_submit():
        username, password = FormUtils.prepare_login_credentials(form)
        
        success, error_message, user = AuthService.authenticate_user(username, password)
        
        if success and user:
            session.update({'username': user.username, 'permanent': True})
            
            flash("Login successful!", FLASH_SUCCESS)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash("Invalid username or password", FLASH_ERROR)
    
    return render_template('instructor/login.html', form=form)

@router.route('/register', methods=['GET', 'POST'])
def register():
    """
    Render the registration form (GET) or create a new instructor (POST).

    On success, redirects to login.  On duplicate username, re-renders the
    form with an error flash.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        username, password = FormUtils.prepare_registration_data(form)
        
        success, error_message, user = AuthService.register_user(username, password)
        
        if success and user:
            flash("Registration successful! You can now log in.", FLASH_SUCCESS)
            return redirect(url_for('auth.login'))
        else:
            flash("Username is already taken. Please choose another one.", FLASH_ERROR)
            return render_template('instructor/register.html', form=form)
    
    return render_template('instructor/register.html', form=form)


@router.route('/logout')
def logout():
    """Clear the instructor session and redirect to the login page."""
    session.clear()
    flash("You have been logged out", FLASH_SUCCESS)
    return redirect('/login')

