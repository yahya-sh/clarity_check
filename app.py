from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, redirect, flash
from forms.register import RegisterForm
from forms.login import LoginForm
import os
from repositories import users as users_repo

app = Flask(__name__)
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
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# TODO: remove debug=True in production
if __name__ == "__main__":
    app.run(debug=True)