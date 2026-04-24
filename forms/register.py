from flask_wtf import FlaskForm
import wtforms as forms
from wtforms import validators
from models.user import User

class RegisterForm(FlaskForm):
    username = forms.StringField('Username', [
        validators.DataRequired(message='Username is required'),
        validators.Length(min=3, max=50, message='Username must be between 3 and 50 characters'),
        validators.Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    password = forms.PasswordField('Password', [
        validators.DataRequired(message='Password is required'),
        validators.Length(min=6, max=100, message='Password must be between 6 and 100 characters'),
        # validators.Regexp(r'^(?=.*[a-zA-Z])(?=.*\d)', message='Password must contain at least one letter and one number')
    ])
