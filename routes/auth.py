from forms.register import RegisterForm
from forms.login import LoginForm
from flask import Blueprint, render_template, redirect, flash, session
from repositories import users as users_repo


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
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

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
            user = form.to_model()
            
            # Save user using repository (handles duplicate check internally)
            saved_user = users_repo.create_user(user)
            
            if saved_user:
                flash('Registration successful! You can now log in.', 'success')
                return redirect('/login')
            else:
                flash('Username is already taken. Please choose another one.', 'error')
                return render_template('register.html', form=form)
        
    return render_template('register.html', form=form)


@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect('/login')
