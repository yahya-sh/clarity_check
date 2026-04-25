from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, redirect, flash, session, g
from functools import wraps
from forms.register import RegisterForm
from forms.login import LoginForm
import os
from datetime import timedelta
from repositories import users as users_repo
from routes.auth import auth as auth_routes

app = Flask(__name__)

# Configure Flask session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_PATH'] = '/'

def require_instructor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash('Please log in to access this page', 'info')
            return redirect('/login')
        
        # Verify user still exists in the database
        user = users_repo.get_user(username)
        if not user:
            g.user= None
            session.clear()
            flash('User not found. Please log in again.', 'info')
            return redirect('/login')
            
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def add_auth_user_to_context():
    username = session.get('username')
    # Store user in Flask.g for request-scoped access
    if username:
        g.user = users_repo.get_user(username)
    else:
        g.user = None

@app.context_processor
def inject_current_user():
    """Make current_user available in all templates"""
    return {'current_user': getattr(g, 'user', None)}

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'insecure-bc054a63d0f9c2b537d4b0f6bebadb3630dd73495a140241')



