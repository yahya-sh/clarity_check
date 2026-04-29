"""
routes/auth.py — Authentication routes.

Handles instructor login, logout, and registration.  No
:func:`~app.require_instructor` decorator is needed here because these
routes are intentionally public.
"""
from forms.register import RegisterForm
from forms.login import LoginForm
from flask import Blueprint, render_template, redirect, flash, session, url_for
from services.auth_service import AuthService
from utils.form_utils import FormUtils
from config.constants import FLASH_SUCCESS, FLASH_ERROR


routes = Blueprint('auth', __name__)

@routes.route('/login', methods=['GET', 'POST'])
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

@routes.route('/register', methods=['GET', 'POST'])
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


@routes.route('/logout')
def logout():
    """Clear the instructor session and redirect to the login page."""
    session.clear()
    flash("You have been logged out", FLASH_SUCCESS)
    return redirect('/login')
