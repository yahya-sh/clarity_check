from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, redirect, flash, session, g
from functools import wraps
from forms.register import RegisterForm
from forms.login import LoginForm
import os
from datetime import timedelta
from repositories import users as users_repo

app = Flask(__name__)

# Configure Flask session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_PATH'] = '/'

def require_auth(f):
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = form.to_model()
        
        # Save user using repository (handles duplicate check internally)
        saved_user = users_repo.create_user(user)
        
        if saved_user:
            flash('Registration successful! You can now log in.', 'success')
            return redirect('/')
        else:
            flash('Username is already taken. Please choose another one.', 'error')
            return render_template('register.html', form=form)
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.data.get('username')
        password = form.data.get('password')
        user = users_repo.get_user(username)
        if user and user.check_password(password):
            # Store username in Flask session
            session['username'] = username
            session.permanent = True
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@require_auth
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect('/login')

# TODO: remove debug=True in production
if __name__ == "__main__":
    app.run(debug=True)