"""
routes/dashboard.py — Instructor dashboard routes.

Handles instructor dashboard and overview pages, including
presentation listings and navigation.
"""
from flask import Blueprint, render_template, g
from app import require_instructor
from repositories import presentations_repo

routes = Blueprint('dashboard', __name__)

def _render_dashboard(username: str):
    """Fetch presentations and render the dashboard template."""
    presentations = presentations_repo.get_user_presentations(username)
    return render_template('instructor/dashboard.html', presentations=presentations)

@routes.route('/dashboard')
@require_instructor
def dashboard():
    """Render the instructor dashboard with all their presentations."""
    return _render_dashboard(g.user.username)

@routes.route('/presentations')
@require_instructor
def presentations_list():
    """Render the presentations list page (alternative to dashboard)."""
    return _render_dashboard(g.user.username)
