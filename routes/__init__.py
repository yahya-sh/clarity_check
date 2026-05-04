"""
routes/__init__.py — HTTP route handlers package initialization.

This package contains all Flask route modules organized by functionality:
- auth: User authentication and session management
- public: Public pages and PIN-based access
- dashboard: Instructor dashboard and presentation management
- presentations: Presentation CRUD operations
- objectives: Objective management within presentations
- questions: Question management within objectives
- sessions: Live session management and control
- participant: Participant session access and interaction
- api: JSON API endpoints for both participants and instructors
"""

from .public import routes as public_routes
from .dashboard import routes as dashboard_routes
from .presentations import routes as presentations_routes
from .objectives import routes as objectives_routes
from .questions import routes as questions_routes
from .sessions import routes as sessions_routes
from .participant import routes as participant_routes
from .api import routes as api_routes