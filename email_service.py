"""
Email service for HabitFlow
Handles sending payment notifications and daily habit reminders
"""
from flask import current_app, render_template
from flask_mail import Message
from models import User, Habit
from datetime import datetime, date
import traceback


def send_email(to, subject, template_name, **template_vars):
    """
    Send an email using Flask-Mail with HTML and plain text versions.

    Args:
        to: Recipient email address or list of addresses
        subject: Email subject line
        template_name: Name of template (e.g., 'payment_success')
        **template_vars: Variables to pass to templates

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Import mail instance from app
        from app import mail

        # Ensure to is a list
        if isinstance(to, str):
            to = [to]

        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=to
        )

        # Render HTML and plain text versions
        msg.html = render_template(f'emails/{template_name}.html', **template_vars)
        msg.body = render_template(f'emails/{template_name}.txt', **template_vars)

        mail.send(msg)

        print(f"[EMAIL] Sent '{subject}' to {to[0]}")
        return True

    except Exception as e:
        print(f"[EMAIL] ERROR sending email: {e}")
        print(traceback.format_exc())
        return False


# ============================================
# PAYMENT NOTIFICATION EMAILS
# ============================================

def send_payment_success_email(user, amount, subscription_type):
    """Send payment receipt email."""
    return send_email(
        to=user.email,
        subject='Payment Successful - HabitFlow',
        template_name='payment_success',
        user=user,
        amount=amount,
        subscription_type=subscription_type,
        date=datetime.utcnow().strftime('%B %d, %Y')
    )


def send_payment_failed_email(user, amount):
    """Send payment failure notification."""
    return send_email(
        to=user.email,
        subject='Payment Failed - HabitFlow',
        template_name='payment_failed',
        user=user,
        amount=amount
    )


def send_subscription_cancelled_email(user, end_date):
    """Send subscription cancellation confirmation."""
    return send_email(
        to=user.email,
        subject='Subscription Cancelled - HabitFlow',
        template_name='subscription_cancelled',
        user=user,
        end_date=end_date.strftime('%B %d, %Y') if end_date else 'immediately'
    )


def send_subscription_expired_email(user, habits_to_archive=0):
    """Send subscription expiry notification."""
    return send_email(
        to=user.email,
        subject='Subscription Expired - HabitFlow',
        template_name='subscription_expired',
        user=user,
        habits_to_archive=habits_to_archive
    )


# ============================================
# DAILY HABIT REMINDER
# ============================================

def send_daily_reminder(user):
    """
    Send daily habit reminder to user.

    Args:
        user: User model instance

    Returns:
        True if sent successfully, False otherwise
    """
    # Check if notifications enabled
    if not user.email_notifications_enabled:
        print(f"[EMAIL] Skipping reminder for user {user.id} - notifications disabled")
        return False

    # Check if already sent today
    user_date = user.get_user_date()
    if user.last_reminder_sent == user_date:
        print(f"[EMAIL] Skipping reminder for user {user.id} - already sent today")
        return False

    # Check day filter
    if not should_send_reminder_today(user, user_date):
        print(f"[EMAIL] Skipping reminder for user {user.id} - day filter")
        return False

    # Get incomplete habits for today
    incomplete_habits = Habit.query.filter_by(
        user_id=user.id,
        archived=False
    ).filter(
        (Habit.last_completed != user_date) | (Habit.last_completed == None)
    ).all()

    if not incomplete_habits:
        print(f"[EMAIL] Skipping reminder for user {user.id} - all habits complete")
        return False

    # Send reminder
    success = send_email(
        to=user.email,
        subject='Your Daily Habit Reminder - HabitFlow',
        template_name='daily_reminder',
        user=user,
        habits=incomplete_habits,
        date=user_date.strftime('%A, %B %d, %Y')
    )

    # Update last_reminder_sent
    if success:
        from models import db
        user.last_reminder_sent = user_date
        db.session.commit()

    return success


def should_send_reminder_today(user, today):
    """Check if reminder should be sent based on user's day preference."""
    if user.reminder_days == 'all':
        return True

    # 0 = Monday, 6 = Sunday
    weekday = today.weekday()

    if user.reminder_days == 'weekdays':
        return weekday < 5  # Monday-Friday

    if user.reminder_days == 'weekends':
        return weekday >= 5  # Saturday-Sunday

    return False
