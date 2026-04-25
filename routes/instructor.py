from flask import Blueprint, render_template, session, flash, redirect, g
from functools import wraps
from repositories import users_repo

routes = Blueprint('instructor', __name__)

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


@routes.route('/dashboard')
@require_instructor
def dashboard():
    return render_template('instructor/dashboard.html')