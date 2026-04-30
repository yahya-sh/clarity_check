"""
models/__init__.py — Domain models package initialization.

This package contains the core domain models for the presentation system:
- User: Instructor accounts and authentication
- Participant: Session attendees and their session state
- Presentation: Presentations with objectives and questions

All models are designed to be independent of Flask and persistence concerns,
focusing purely on business logic and data validation.
"""

from . import participant
from . import user
from . import presentation