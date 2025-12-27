"""
Migration script to add email notification fields to User model.
Run this once: python migrate_email_notifications.py
"""
from app import app, db
from sqlalchemy import text


def migrate_email_notifications():
    """Add email notification columns to user table."""
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Add email_notifications_enabled
                print("[MIGRATION] Adding email_notifications_enabled column...")
                conn.execute(text(
                    "ALTER TABLE user ADD COLUMN email_notifications_enabled BOOLEAN NOT NULL DEFAULT 1"
                ))

                # Add reminder_time (default 9 AM)
                print("[MIGRATION] Adding reminder_time column...")
                conn.execute(text(
                    "ALTER TABLE user ADD COLUMN reminder_time VARCHAR(5) NOT NULL DEFAULT '09:00'"
                ))

                # Add reminder_days (default 'all')
                print("[MIGRATION] Adding reminder_days column...")
                conn.execute(text(
                    "ALTER TABLE user ADD COLUMN reminder_days VARCHAR(20) NOT NULL DEFAULT 'all'"
                ))

                # Add last_reminder_sent
                print("[MIGRATION] Adding last_reminder_sent column...")
                conn.execute(text(
                    "ALTER TABLE user ADD COLUMN last_reminder_sent DATE"
                ))

                conn.commit()

            print("[MIGRATION] SUCCESS - All email notification fields added")
            print("[MIGRATION] Fields added:")
            print("  - email_notifications_enabled (BOOLEAN, default: TRUE)")
            print("  - reminder_time (VARCHAR(5), default: '09:00')")
            print("  - reminder_days (VARCHAR(20), default: 'all')")
            print("  - last_reminder_sent (DATE, nullable)")

        except Exception as e:
            print(f"[MIGRATION] ERROR: {e}")
            print("[MIGRATION] Note: If columns already exist, this is expected and OK")


if __name__ == '__main__':
    print("="*60)
    print("EMAIL NOTIFICATIONS MIGRATION")
    print("="*60)
    migrate_email_notifications()
    print("="*60)
