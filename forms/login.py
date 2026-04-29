"""
forms/login.py — Instructor login form.

Validates that username and password are present and well-formed before
the route checks credentials against the user store.
"""
from flask_wtf import FlaskForm
import wtforms as forms
from wtforms import validators

class LoginForm(FlaskForm):
    """Form for authenticating an instructor."""
    username = forms.StringField('Username', [
        validators.DataRequired(message='Username is required'),
        validators.Length(min=3, max=50, message='Username must be between 3 and 50 characters'),
        validators.Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    password = forms.PasswordField('Password', [
        validators.DataRequired(message='Password is required'),
    ])