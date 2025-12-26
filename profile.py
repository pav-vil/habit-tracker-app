# profile.py - User Profile Management Blueprint for HabitFlow
# Handles user profile viewing, editing, settings management, and account deletion

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User
from forms import EditEmailForm, EditPasswordForm, SettingsForm, DeleteAccountForm
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

# Create blueprint for profile routes
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def view():
    """
    Display user profile overview.
    Shows email, member since date, and current subscription tier.
    """
    return render_template('profile/view.html',
                           user=current_user,
                           now=datetime.now())


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """
    Edit user email and password.
    Validates email uniqueness and password strength.
    Requires current password confirmation for security.
    """
    email_form = EditEmailForm()
    password_form = EditPasswordForm()

    # Handle email change
    if email_form.validate_on_submit() and request.form.get('form_type') == 'email':
        new_email = email_form.email.data.strip().lower()

        # Check if email is already taken by another user
        existing_user = User.query.filter(
            User.email == new_email,
            User.id != current_user.id
        ).first()

        if existing_user:
            flash('This email is already registered to another account.', 'danger')
            return redirect(url_for('profile.edit'))

        try:
            # Update email
            current_user.email = new_email
            db.session.commit()

            flash('Email updated successfully!', 'success')
            return redirect(url_for('profile.view'))

        except IntegrityError:
            db.session.rollback()
            flash('Error updating email. Please try again.', 'danger')
            return redirect(url_for('profile.edit'))

    # Handle password change
    if password_form.validate_on_submit() and request.form.get('form_type') == 'password':
        # Verify current password
        if not current_user.check_password(password_form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('profile.edit'))

        try:
            # Update password
            current_user.set_password(password_form.new_password.data)
            db.session.commit()

            flash('Password updated successfully!', 'success')
            return redirect(url_for('profile.view'))

        except Exception as e:
            db.session.rollback()
            flash('Error updating password. Please try again.', 'danger')
            return redirect(url_for('profile.edit'))

    # Pre-fill email form with current email
    if request.method == 'GET':
        email_form.email.data = current_user.email

    return render_template('profile/edit.html',
                           email_form=email_form,
                           password_form=password_form)


@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Consolidated settings page.
    Manage timezone, dark mode, and newsletter subscription preferences.
    """
    form = SettingsForm()

    if form.validate_on_submit():
        try:
            # Update user settings
            current_user.timezone = form.timezone.data
            current_user.dark_mode = form.dark_mode.data
            current_user.newsletter_subscribed = form.newsletter_subscribed.data

            db.session.commit()

            flash('Settings updated successfully!', 'success')
            return redirect(url_for('profile.view'))

        except Exception as e:
            db.session.rollback()
            flash('Error updating settings. Please try again.', 'danger')
            return redirect(url_for('profile.settings'))

    # Pre-fill form with current settings
    if request.method == 'GET':
        form.timezone.data = current_user.timezone
        form.dark_mode.data = current_user.dark_mode
        form.newsletter_subscribed.data = current_user.newsletter_subscribed

    return render_template('profile/settings.html', form=form)


@profile_bp.route('/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    """
    Delete user account (soft delete with 30-day grace period).
    Requires password confirmation for security.
    Account and all data will be permanently deleted after 30 days.
    """
    form = DeleteAccountForm()

    if form.validate_on_submit():
        # Verify password
        if not current_user.check_password(form.password.data):
            flash('Password is incorrect. Account deletion cancelled.', 'danger')
            return redirect(url_for('profile.delete_account'))

        # Check if user confirmed deletion
        if not form.confirm_deletion.data:
            flash('Please confirm that you want to delete your account.', 'danger')
            return redirect(url_for('profile.delete_account'))

        try:
            # Soft delete: Mark account for deletion
            current_user.account_deleted = True
            current_user.deletion_scheduled_date = datetime.utcnow()

            db.session.commit()

            # Log user out
            from flask_login import logout_user
            logout_user()

            flash(
                'Your account has been scheduled for deletion. '
                'You have 30 days to change your mind. '
                'After 30 days, your account and all data will be permanently deleted.',
                'info'
            )
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash('Error deleting account. Please contact support.', 'danger')
            return redirect(url_for('profile.delete_account'))

    return render_template('profile/delete_account.html', form=form)


@profile_bp.route('/subscription')
@login_required
def subscription():
    """
    Subscription management page.
    View current plan, billing cycle, and manage subscription.
    (Payment integration to be added in Phase 3)
    """
    # Get subscription tier (default to 'free' for now)
    subscription_tier = getattr(current_user, 'subscription_tier', 'free')
    subscription_status = getattr(current_user, 'subscription_status', 'active')

    return render_template('profile/subscription.html',
                           subscription_tier=subscription_tier,
                           subscription_status=subscription_status)


@profile_bp.route('/billing')
@login_required
def billing():
    """
    Billing history page.
    Shows all past payments and transactions.
    (Payment records to be added in Phase 3)
    """
    # Placeholder for billing history (will be populated in Phase 3)
    payments = []

    return render_template('profile/billing.html',
                           payments=payments)


@profile_bp.route('/about')
def about():
    """
    About page - App philosophy, features, and mission.
    Public route - no login required.
    """
    return render_template('profile/about.html')
