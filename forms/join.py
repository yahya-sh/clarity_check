from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp


class JoinForm(FlaskForm):
    nickname = StringField('Nickname', [
        DataRequired(message='Nickname is required.'),
        Length(min=2, max=20, message='Nickname must be between 2 and 20 characters.'),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Nickname can only contain letters, numbers, underscores, and hyphens.')
    ])
    pin = StringField('PIN Code', [
        DataRequired(message='PIN code is required.'),
        Length(min=3, max=10, message='PIN code must be between 3 and 10 characters.')
    ])
