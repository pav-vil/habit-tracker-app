"""
Scheduled task to check for expired subscriptions and downgrade users.
This script should be run daily via cron job or scheduled task.

Example cron entry (runs daily at 2 AM):
0 2 * * * cd /path/to/habit-tracker-app && python check_expired_subscriptions.py
"""
from app import app, db
from stripe_handler import check_expired_subscriptions

if __name__ == '__main__':
    with app.app_context():
        print("="*60)
        print("CHECKING EXPIRED SUBSCRIPTIONS")
        print("="*60)

        downgraded_count = check_expired_subscriptions()

        print(f"\n[COMPLETE] Total users downgraded: {downgraded_count}")
        print("="*60)
