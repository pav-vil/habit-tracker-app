"""
Form classes for HabitFlow using Flask-WTF and WTForms
Handles validation for registration and login forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
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
    
    submit = SubmitField('Save Habit', render_kw={"class": "btn btn-primary"})