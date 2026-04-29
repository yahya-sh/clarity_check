"""
routes/public.py — Public-facing routes.

Handles public pages that don't require authentication, including
the landing page and other public content.
"""
from flask import Blueprint, render_template

routes = Blueprint('public', __name__)

@routes.route('/')
def index():
    """Render the main landing page."""
    return render_template('index.html')
