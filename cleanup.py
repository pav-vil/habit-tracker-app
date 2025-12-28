"""
Cleanup Script for HabitFlow
Handles permanent deletion of accounts scheduled for deletion (30-day grace period)

This script should be run daily as a cron job:
    0 2 * * * cd /path/to/habitflow && python cleanup.py

What it does:
- Finds all users with account_deleted=True and deletion_scheduled_date > 30 days ago
- Permanently deletes their data (habits, logs, subscriptions, payments, audit logs)
- Removes the user account

GDPR Compliance: Users have 30 days to change their mind before permanent deletion
"""

from app import app, db
from models import User, Habit, CompletionLog, Subscription, Payment, AuditLog, SubscriptionHistory, PaymentTransaction
from datetime import datetime, timedelta


def delete_expired_accounts():
    """
    Permanently delete user accounts that have been soft-deleted for 30+ days.

    Returns:
        int: Number of accounts permanently deleted
    """
    # Calculate cutoff date (30 days ago)
    cutoff_date = datetime.utcnow() - timedelta(days=30)

    # Find users scheduled for deletion who have passed the grace period
    users_to_delete = User.query.filter(
        User.account_deleted == True,
        User.deletion_scheduled_date <= cutoff_date
    ).all()

    deleted_count = 0

    for user in users_to_delete:
        try:
            print(f"[CLEANUP] Permanently deleting user {user.id} ({user.email})")
            print(f"[CLEANUP] Deletion scheduled on: {user.deletion_scheduled_date}")

            # Log the permanent deletion
            user_id = user.id
            user_email = user.email

            # Delete all user data (cascade will handle most of this, but being explicit)

            # Delete habits and their completion logs (should cascade)
            habits = Habit.query.filter_by(user_id=user.id).all()
            for habit in habits:
                CompletionLog.query.filter_by(habit_id=habit.id).delete()
                db.session.delete(habit)

            # Delete subscriptions
            Subscription.query.filter_by(user_id=user.id).delete()
            SubscriptionHistory.query.filter_by(user_id=user.id).delete()

            # Delete payments
            Payment.query.filter_by(user_id=user.id).delete()
            PaymentTransaction.query.filter_by(user_id=user.id).delete()

            # Delete audit logs
            AuditLog.query.filter_by(user_id=user.id).delete()

            # Finally, delete the user account
            db.session.delete(user)
            db.session.commit()

            deleted_count += 1
            print(f"[CLEANUP] ✓ Successfully deleted user {user_id} ({user_email})")

        except Exception as e:
            db.session.rollback()
            print(f"[CLEANUP] ✗ Error deleting user {user.id}: {e}")

    return deleted_count


def main():
    """
    Main cleanup function
    """
    with app.app_context():
        print(f"[CLEANUP] Starting cleanup at {datetime.utcnow().isoformat()}")
        print(f"[CLEANUP] Looking for accounts deleted more than 30 days ago...")

        deleted_count = delete_expired_accounts()

        if deleted_count > 0:
            print(f"[CLEANUP] ✓ Permanently deleted {deleted_count} user account(s)")
        else:
            print(f"[CLEANUP] No accounts to delete")

        print(f"[CLEANUP] Cleanup complete at {datetime.utcnow().isoformat()}")


if __name__ == '__main__':
    main()
