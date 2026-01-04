"""
Authentication Blueprint for HabitFlow
Handles user registration, login, and logout
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import RegistrationForm, LoginForm

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    GET: Display registration form
    POST: Process registration and create new user
    """
    # If user already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    
    # If form submitted and valid
    if form.validate_on_submit():
        try:
            # Check if email already exists
            existing_user = User.query.filter_by(email=form.email.data).first()

            if existing_user:
                flash('Email already registered. Please login or use a different email.', 'danger')
                return redirect(url_for('auth.register'))

            # Create new user
            new_user = User(
                email=form.email.data,
                timezone=form.timezone.data
            )
            new_user.set_password(form.password.data)  # Hash the password

            # Save to database
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"[AUTH] Registration error: {e}")
            import traceback
            traceback.print_exc()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
    
    # GET request or form validation failed
    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    GET: Display login form
    POST: Authenticate user and create session
    """
    # If user already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    
    # If form submitted and valid
    if form.validate_on_submit():
        try:
            # Find user by email
            user = User.query.filter_by(email=form.email.data).first()

            # Check if user exists and password is correct
            if user is None or not user.check_password(form.password.data):
                flash('Invalid email or password. Please try again.', 'danger')
                return redirect(url_for('auth.login'))

            # Login successful - create session
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.email}!', 'success')

            # Redirect to next page if specified, otherwise home
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        except Exception as e:
            print(f"[AUTH] Login error: {e}")
            import traceback
            traceback.print_exc()
            flash('An error occurred during login. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
    
    # GET request or form validation failed
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required  # Must be logged in to logout
def logout():
    """
    User logout route.
    Ends the user session and redirects to home
    """
    logout_user()  # Clear the session
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    User settings page.
    Allows users to configure email notification preferences, timezone, and language.
    """
    if request.method == 'POST':
        try:
            # Update email notification preferences
            current_user.email_notifications_enabled = request.form.get('email_notifications_enabled') == 'on'
            current_user.reminder_time = request.form.get('reminder_time', '09:00')
            current_user.reminder_days = request.form.get('reminder_days', 'all')

            # Update language
            language = request.form.get('language', 'en')
            if language in ['en', 'es']:  # Validate language choice
                current_user.language = language

            # Update timezone
            timezone = request.form.get('timezone', 'UTC')
            # Validate timezone is in pytz
            try:
                import pytz
                pytz.timezone(timezone)  # Will raise exception if invalid
                current_user.timezone = timezone
            except Exception as tz_error:
                print(f"[AUTH] Invalid timezone: {timezone}, error: {tz_error}")
                # Keep existing timezone if invalid
                pass

            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('auth.settings'))

        except Exception as e:
            db.session.rollback()
            print(f"[AUTH] Settings update error: {e}")
            import traceback
            traceback.print_exc()
            flash('An error occurred while updating settings. Please try again.', 'danger')
            return redirect(url_for('auth.settings'))

    # GET request - show settings form
    return render_template('settings.html')