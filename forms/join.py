from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

def digits_count(count: int):
    def _validator(form, field):
        if field.data is None:
            return
        
        length = len(str(abs(field.data)))  # handle negatives safely
        if length != count:
            raise ValidationError(f"Must be exactly {count} digits.")
    return _validator

class JoinForm(FlaskForm):
    nickname = StringField('Nickname', [
        DataRequired(message='Nickname is required.'),
        Length(min=2, max=20, message='Nickname must be between 2 and 20 characters.'),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Nickname can only contain letters, numbers, underscores, and hyphens.')
    ])

    pin = IntegerField('PIN Code', render_kw={"class": "no-spinner"},   
        validators=[
            DataRequired(message='PIN code is required.'),
            digits_count(6),
        ])
