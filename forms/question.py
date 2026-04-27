from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, IntegerField
from wtforms.validators import DataRequired, InputRequired, NumberRange, ValidationError, Length
import json


class SaveQuestionForm(FlaskForm):
    objective_id = HiddenField('Objective ID', [DataRequired(message='Objective ID is required.')])
    question_id = HiddenField('Question ID', [DataRequired(message='Question ID is required.')])
    text = StringField('Text', [
        DataRequired(message='Question text is required.'),
        Length(min=3, message='Question text must be at least 3 characters.')
    ])
    type = StringField('Type', [DataRequired(message='Question type is required.')])
    choices_json = HiddenField('Choices', [DataRequired(message='Choices are required.')])
    correct_indices_json = HiddenField('Correct Indices', [DataRequired(message='Correct answers are required.')])
    points = IntegerField('Points', [InputRequired(message='Points are required.'), NumberRange(min=1, message='Points must be a positive integer.')])
    time_limit = IntegerField('Time Limit', [InputRequired(message='Time limit is required.'), NumberRange(min=5, message='Time limit must be at least 5 seconds.')])

    def __init__(self, *args, instructor_username=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instructor_username = instructor_username
        self.cleaned_choices = []
        self.cleaned_correct_indices = []

    def validate_text(self, field):
        value = (field.data or '').strip()
        if not value:
            raise ValidationError('Question text is required.')
        if len(value) < 3:
            raise ValidationError('Question text must be at least 3 characters.')

    def validate_type(self, field):
        value = (field.data or '').strip().lower()
        if value not in {'single_choice', 'multiple_choice'}:
            raise ValidationError('Invalid question type.')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        try:
            choices = json.loads(self.choices_json.data or '[]')
        except json.JSONDecodeError:
            self.choices_json.errors.append('Invalid choices payload.')
            return False
        if not isinstance(choices, list):
            self.choices_json.errors.append('Choices must be a list.')
            return False

        clean_choices = [str(choice).strip() for choice in choices if str(choice).strip()]
        if len(clean_choices) < 2:
            self.choices_json.errors.append('There must be at least two options.')
            return False

        try:
            correct_indices = json.loads(self.correct_indices_json.data or '[]')
        except json.JSONDecodeError:
            self.correct_indices_json.errors.append('Invalid correct indices payload.')
            return False
        if not isinstance(correct_indices, list):
            self.correct_indices_json.errors.append('Correct indices must be a list.')
            return False

        normalized_indices = []
        for value in correct_indices:
            try:
                idx = int(value)
            except (TypeError, ValueError):
                continue
            if 0 <= idx < len(clean_choices):
                normalized_indices.append(idx)
        normalized_indices = sorted(set(normalized_indices))

        if len(normalized_indices) < 1:
            self.correct_indices_json.errors.append('There must be at least one correct answer.')
            return False

        question_type = (self.type.data or '').strip().lower()
        if question_type == 'single_choice' and len(normalized_indices) > 1:
            self.correct_indices_json.errors.append('Single choice questions can only have one correct answer.')
            return False

        self.cleaned_choices = clean_choices
        self.cleaned_correct_indices = normalized_indices
        return True
