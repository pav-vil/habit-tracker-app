"""
Scheduled task to send daily habit reminders to users.
This script should be run daily via cron job or scheduled task.

Example cron entry (runs daily at 9 AM):
0 9 * * * cd /path/to/habit-tracker-app && python send_daily_reminders.py

NOTE: The actual reminder time is determined by each user's preference settings.
This script should run early in the morning to catch all users across timezones.
"""
from app import app, db
from models import User
from email_service import send_daily_reminder

if __name__ == '__main__':
    with app.app_context():
        print("="*60)
        print("SENDING DAILY HABIT REMINDERS")
        print("="*60)

        # Get all users with email notifications enabled
        users_to_notify = User.query.filter_by(
            email_notifications_enabled=True
        ).all()

        print(f"[INFO] Found {len(users_to_notify)} users with notifications enabled")

        sent_count = 0
        skipped_count = 0
        error_count = 0

        for user in users_to_notify:
            try:
                # send_daily_reminder handles time/day filtering internally
                success = send_daily_reminder(user)

                if success:
                    sent_count += 1
                    print(f"[OK] Sent reminder to user {user.id} ({user.email})")
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                print(f"[ERROR] Failed to send reminder to user {user.id}: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "="*60)
        print(f"[COMPLETE] Summary:")
        print(f"  - Reminders sent: {sent_count}")
        print(f"  - Skipped: {skipped_count}")
        print(f"  - Errors: {error_count}")
        print("="*60)
