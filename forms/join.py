"""
forms/join.py — Participant session-join form.

Collects the 6-digit PIN code and a display nickname from a participant
before they are admitted to a run lobby.
"""
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError


class JoinForm(FlaskForm):
    """Form for a participant joining a session via PIN code."""
    nickname = StringField('Nickname', [
        DataRequired(message='Nickname is required.'),
        Length(min=2, max=20, message='Nickname must be between 2 and 20 characters.'),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Nickname can only contain letters, numbers, underscores, and hyphens.')
    ])

    pin = StringField('PIN Code', render_kw={"pattern": "[0-9]{6}", "maxlength": "6", "inputmode": "numeric"},
        validators=[
            DataRequired(message='PIN code is required.'),
            Length(min=6, max=6, message='Must be exactly 6 digits.'),
            Regexp(r'^\d{6}$', message='Must be exactly 6 digits.'),
        ])
