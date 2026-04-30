"""
forms/__init__.py — Form validation package initialization.

This package contains all WTForms form classes used throughout the application:
- LoginForm: Instructor authentication form
- RegisterForm: New instructor account registration
- SaveQuestionForm: Question creation and editing
- JoinForm: Participant session joining with PIN validation

All forms include comprehensive validation and error handling
to ensure data integrity and user experience.
"""

from .login import LoginForm
from .register import RegisterForm
from .question import SaveQuestionForm
from .join import JoinForm
