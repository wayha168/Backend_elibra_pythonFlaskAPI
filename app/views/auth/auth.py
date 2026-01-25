from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .form import LoginForm
from app.models import *
from app.extensions import *

auth_bp = Blueprint('auth', __name__ )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        form = LoginForm()
        return render_template('auth/login.html', form=form)
    
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        login_user(user, remember=remember)
        # Create JWT token
        access_token = create_access_token(identity=user.username)
        # Store token in session for use in templates/API
        flash('Login successful', 'success')
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    else:
        flash('Invalid username or password. Please try again.', 'danger')
        return redirect(url_for('auth.login')) 

@auth_bp.route('/signup')
def signup():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    return render_template('auth/signup.html', form=form)

@auth_bp.route('/signup', methods=['POST','GET'])
def signup_post():
    # If already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    gender = request.form.get('gender')
    
    user = User.query.filter_by(username=username).first()
    email_exists = User.query.filter_by(email=email).first()
    
    if user:
        flash('Username already exists. Please choose a different one.', 'danger')
        return redirect(url_for('auth.signup'))
    if email_exists:
        flash('Email already exists. Please choose a different one.', 'danger')
        return redirect(url_for('auth.signup'))
    
    new_user = User(username=username, 
                    email=email,
                    password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
                    gender=gender)
    
    db.session.add(new_user)
    db.session.commit()
    
    # Create profile for the user
    new_profile = Profile(username=username, 
                    email=email,
                    password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
                    gender=gender,
                    user_id=new_user.id)
    
    db.session.add(new_profile)
    db.session.commit()
    
    # Fetch the user from the database after committing the session
    user = User.query.filter_by(username=username).first()
    login_user(user)
    
    flash('Account created successfully!', 'success')
    return redirect(url_for('main.dashboard'))
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
