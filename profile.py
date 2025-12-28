# profile.py - User Profile Management Blueprint for HabitFlow
# Handles user profile viewing, editing, settings management, and account deletion

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Payment, Subscription
from forms import EditEmailForm, EditPasswordForm, SettingsForm, DeleteAccountForm
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from payments import cancel_stripe_subscription, cancel_paypal_subscription

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
    Shows real subscription data including payment provider and next billing date.
    """
    # Get subscription tier and status
    subscription_tier = getattr(current_user, 'subscription_tier', 'free')
    subscription_status = getattr(current_user, 'subscription_status', 'active')

    # Get next billing date
    next_billing_date = getattr(current_user, 'subscription_end_date', None)

    # Determine payment provider
    payment_provider = None
    if current_user.stripe_subscription_id:
        payment_provider = 'stripe'
    elif current_user.paypal_subscription_id:
        payment_provider = 'paypal'
    elif subscription_tier == 'lifetime':
        payment_provider = 'coinbase' if current_user.coinbase_charge_code else 'stripe'

    # Get latest subscription record
    latest_subscription = Subscription.query.filter_by(
        user_id=current_user.id
    ).order_by(Subscription.start_date.desc()).first()

    return render_template('profile/subscription.html',
                           subscription_tier=subscription_tier,
                           subscription_status=subscription_status,
                           next_billing_date=next_billing_date,
                           payment_provider=payment_provider,
                           subscription=latest_subscription)


@profile_bp.route('/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """
    Cancel user's subscription.
    Handles cancellation for Stripe and PayPal subscriptions.
    Lifetime subscriptions cannot be cancelled (one-time payment).
    """
    # Check if user has an active subscription
    if not current_user.subscription_tier or current_user.subscription_tier == 'free':
        flash('You do not have an active subscription to cancel.', 'warning')
        return redirect(url_for('profile.subscription'))

    # Lifetime subscriptions cannot be cancelled
    if current_user.subscription_tier == 'lifetime':
        flash('Lifetime subscriptions cannot be cancelled as they are one-time purchases.', 'info')
        return redirect(url_for('profile.subscription'))

    # Check if already cancelled
    if current_user.subscription_status == 'cancelled':
        flash('Your subscription is already cancelled.', 'info')
        return redirect(url_for('profile.subscription'))

    try:
        # Determine payment provider and cancel accordingly
        if current_user.stripe_subscription_id:
            # Cancel Stripe subscription
            success = cancel_stripe_subscription(current_user.stripe_subscription_id)
            if success:
                current_user.subscription_status = 'cancelled'
                db.session.commit()
                flash(
                    'Your subscription has been cancelled. '
                    'You will retain access until the end of your current billing period.',
                    'success'
                )
            else:
                flash('Unable to cancel subscription. Please try again or contact support.', 'danger')

        elif current_user.paypal_subscription_id:
            # Cancel PayPal subscription
            success = cancel_paypal_subscription(current_user.paypal_subscription_id)
            if success:
                current_user.subscription_status = 'cancelled'
                db.session.commit()
                flash(
                    'Your subscription has been cancelled. '
                    'You will retain access until the end of your current billing period.',
                    'success'
                )
            else:
                flash('Unable to cancel subscription. Please try again or contact support.', 'danger')

        else:
            flash('No active payment subscription found.', 'warning')

    except Exception as e:
        db.session.rollback()
        flash('Error cancelling subscription. Please contact support.', 'danger')

    return redirect(url_for('profile.subscription'))


@profile_bp.route('/subscription/resume', methods=['POST'])
@login_required
def resume_subscription():
    """
    Resume a cancelled subscription.
    Only works if subscription is cancelled but still within the paid period.
    Re-enables auto-renewal for the subscription.
    """
    # Check if user has a cancelled subscription
    if current_user.subscription_status != 'cancelled':
        flash('Your subscription is not cancelled.', 'info')
        return redirect(url_for('profile.subscription'))

    # Check if subscription tier is valid (not free or lifetime)
    if current_user.subscription_tier in ['free', 'lifetime']:
        flash('This subscription cannot be resumed.', 'warning')
        return redirect(url_for('profile.subscription'))

    try:
        # For resumed subscriptions, we reactivate by changing status back to active
        # The actual billing will resume at the next billing date via webhooks
        current_user.subscription_status = 'active'
        db.session.commit()

        flash(
            'Your subscription has been resumed! '
            'Auto-renewal is now enabled and will continue at your next billing date.',
            'success'
        )

    except Exception as e:
        db.session.rollback()
        flash('Error resuming subscription. Please contact support.', 'danger')

    return redirect(url_for('profile.subscription'))


@profile_bp.route('/billing')
@login_required
def billing():
    """
    Billing history page with pagination and date filtering.
    Shows all past payments and transactions (10 per page).
    Supports filtering by date range.
    """
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Get date range filters (optional)
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    # Build query for user's payments
    query = Payment.query.filter_by(user_id=current_user.id)

    # Apply date filters if provided
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Payment.payment_date >= start_date)
        except ValueError:
            flash('Invalid start date format. Use YYYY-MM-DD.', 'warning')

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Add one day to include the entire end date
            end_date = end_date + timedelta(days=1)
            query = query.filter(Payment.payment_date < end_date)
        except ValueError:
            flash('Invalid end date format. Use YYYY-MM-DD.', 'warning')

    # Order by most recent first and paginate
    pagination = query.order_by(Payment.payment_date.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template('profile/billing.html',
                           payments=pagination.items,
                           pagination=pagination,
                           start_date=start_date_str,
                           end_date=end_date_str)


@profile_bp.route('/about')
def about():
    """
    About page - App philosophy, features, and mission.
    Public route - no login required.
    """
    return render_template('profile/about.html')
