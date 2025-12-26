"""
Form classes for HabitFlow using Flask-WTF and WTForms
Handles validation for registration and login forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re


def password_strength(form, field):
    """
    Custom validator for password strength.
    Requires:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 number
    """
    password = field.data

    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')

    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least 1 uppercase letter.')

    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least 1 number.')


class RegistrationForm(FlaskForm):
    """Form for user registration"""
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ],
        render_kw={"placeholder": "your.email@example.com", "class": "form-control"}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=8, max=50, message='Password must be between 8 and 50 characters'),
            password_strength
        ],
        render_kw={"placeholder": "Enter a secure password", "class": "form-control"}
    )
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Re-enter your password", "class": "form-control"}
    )

    timezone = SelectField(
        'Timezone',
        choices=[
            ('UTC', 'UTC (Coordinated Universal Time)'),
            ('America/New_York', 'America/New York (EST/EDT)'),
            ('America/Chicago', 'America/Chicago (CST/CDT)'),
            ('America/Denver', 'America/Denver (MST/MDT)'),
            ('America/Los_Angeles', 'America/Los Angeles (PST/PDT)'),
            ('America/Phoenix', 'America/Phoenix (MST - No DST)'),
            ('America/Anchorage', 'America/Anchorage (AKST/AKDT)'),
            ('Pacific/Honolulu', 'Pacific/Honolulu (HST)'),
            ('Europe/London', 'Europe/London (GMT/BST)'),
            ('Europe/Paris', 'Europe/Paris (CET/CEST)'),
            ('Europe/Berlin', 'Europe/Berlin (CET/CEST)'),
            ('Europe/Rome', 'Europe/Rome (CET/CEST)'),
            ('Europe/Madrid', 'Europe/Madrid (CET/CEST)'),
            ('Europe/Moscow', 'Europe/Moscow (MSK)'),
            ('Asia/Dubai', 'Asia/Dubai (GST)'),
            ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
            ('Asia/Shanghai', 'Asia/Shanghai (CST)'),
            ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
            ('Asia/Seoul', 'Asia/Seoul (KST)'),
            ('Asia/Singapore', 'Asia/Singapore (SGT)'),
            ('Asia/Hong_Kong', 'Asia/Hong Kong (HKT)'),
            ('Australia/Sydney', 'Australia/Sydney (AEDT/AEST)'),
            ('Australia/Melbourne', 'Australia/Melbourne (AEDT/AEST)'),
            ('Australia/Perth', 'Australia/Perth (AWST)'),
            ('Pacific/Auckland', 'Pacific/Auckland (NZDT/NZST)'),
        ],
        validators=[DataRequired(message='Please select your timezone')],
        render_kw={"class": "form-select"}
    )

    submit = SubmitField('Register', render_kw={"class": "btn btn-primary w-100"})


class LoginForm(FlaskForm):
    """Form for user login"""
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ],
        render_kw={"placeholder": "your.email@example.com", "class": "form-control"}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ],
        render_kw={"placeholder": "Enter your password", "class": "form-control"}
    )
    
    remember_me = BooleanField(
        'Remember Me',
        render_kw={"class": "form-check-input"}
    )
    
    submit = SubmitField('Login', render_kw={"class": "btn btn-primary w-100"})

class HabitForm(FlaskForm):
    """Form for creating/editing habits"""

    name = StringField(
        'Habit Name',
        validators=[
            DataRequired(message='Habit name is required'),
            Length(min=2, max=100, message='Name must be between 2 and 100 characters')
        ],
        render_kw={"placeholder": "e.g., Morning Workout", "class": "form-control"}
    )

    description = StringField(
        'Description (optional)',
        validators=[
            Length(max=500, message='Description must be less than 500 characters')
        ],
        render_kw={"placeholder": "Add details about your habit", "class": "form-control"}
    )

    why = TextAreaField(
        'Why track this habit? (optional)',
        validators=[
            Length(max=1000, message='Why section must be less than 1000 characters')
        ],
        render_kw={
            "placeholder": "e.g., I want to track this habit because it helps me stay healthy and energized throughout the day. It's important for my long-term fitness goals.",
            "class": "form-control",
            "rows": "4"
        }
    )

    submit = SubmitField('Save Habit', render_kw={"class": "btn btn-primary"})


class EditEmailForm(FlaskForm):
    """Form for editing user email address"""

    email = StringField(
        'New Email Address',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must be less than 120 characters')
        ],
        render_kw={"placeholder": "your.new.email@example.com", "class": "form-control"}
    )

    submit = SubmitField('Update Email', render_kw={"class": "btn btn-primary"})


class EditPasswordForm(FlaskForm):
    """Form for changing user password"""

    current_password = PasswordField(
        'Current Password',
        validators=[
            DataRequired(message='Current password is required')
        ],
        render_kw={"placeholder": "Enter your current password", "class": "form-control"}
    )

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='New password is required'),
            Length(min=8, max=50, message='Password must be between 8 and 50 characters'),
            password_strength
        ],
        render_kw={"placeholder": "Enter your new password", "class": "form-control"}
    )

    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your new password'),
            EqualTo('new_password', message='Passwords must match')
        ],
        render_kw={"placeholder": "Re-enter your new password", "class": "form-control"}
    )

    submit = SubmitField('Update Password', render_kw={"class": "btn btn-primary"})


class SettingsForm(FlaskForm):
    """Form for user settings (timezone, dark mode, newsletter)"""

    timezone = SelectField(
        'Timezone',
        choices=[
            ('UTC', 'UTC (Coordinated Universal Time)'),
            ('America/New_York', 'America/New York (EST/EDT)'),
            ('America/Chicago', 'America/Chicago (CST/CDT)'),
            ('America/Denver', 'America/Denver (MST/MDT)'),
            ('America/Los_Angeles', 'America/Los Angeles (PST/PDT)'),
            ('America/Phoenix', 'America/Phoenix (MST - No DST)'),
            ('America/Anchorage', 'America/Anchorage (AKST/AKDT)'),
            ('Pacific/Honolulu', 'Pacific/Honolulu (HST)'),
            ('Europe/London', 'Europe/London (GMT/BST)'),
            ('Europe/Paris', 'Europe/Paris (CET/CEST)'),
            ('Europe/Berlin', 'Europe/Berlin (CET/CEST)'),
            ('Europe/Rome', 'Europe/Rome (CET/CEST)'),
            ('Europe/Madrid', 'Europe/Madrid (CET/CEST)'),
            ('Europe/Moscow', 'Europe/Moscow (MSK)'),
            ('Asia/Dubai', 'Asia/Dubai (GST)'),
            ('Asia/Kolkata', 'Asia/Kolkata (IST)'),
            ('Asia/Shanghai', 'Asia/Shanghai (CST)'),
            ('Asia/Tokyo', 'Asia/Tokyo (JST)'),
            ('Asia/Seoul', 'Asia/Seoul (KST)'),
            ('Asia/Singapore', 'Asia/Singapore (SGT)'),
            ('Asia/Hong_Kong', 'Asia/Hong Kong (HKT)'),
            ('Australia/Sydney', 'Australia/Sydney (AEDT/AEST)'),
            ('Australia/Melbourne', 'Australia/Melbourne (AEDT/AEST)'),
            ('Australia/Perth', 'Australia/Perth (AWST)'),
            ('Pacific/Auckland', 'Pacific/Auckland (NZDT/NZST)'),
        ],
        validators=[DataRequired(message='Please select your timezone')],
        render_kw={"class": "form-select"}
    )

    dark_mode = BooleanField(
        'Dark Mode',
        render_kw={"class": "form-check-input"}
    )

    newsletter_subscribed = BooleanField(
        'Subscribe to Newsletter',
        render_kw={"class": "form-check-input"}
    )

    submit = SubmitField('Save Settings', render_kw={"class": "btn btn-primary"})


class DeleteAccountForm(FlaskForm):
    """Form for account deletion confirmation"""

    password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Password is required to delete your account')
        ],
        render_kw={"placeholder": "Enter your password to confirm", "class": "form-control"}
    )

    confirm_deletion = BooleanField(
        'I understand that this action cannot be undone',
        validators=[
            DataRequired(message='You must confirm account deletion')
        ],
        render_kw={"class": "form-check-input"}
    )

    submit = SubmitField('Delete My Account', render_kw={"class": "btn btn-danger"})