"""
Migration script to add longest_streak column to Habit model
Run this script once to update the database schema and initialize longest_streak values.

Usage: python migrate_longest_streak.py
"""

from app import app
from models import db, Habit
from sqlalchemy import text


def migrate():
    """Add longest_streak column and initialize values for existing habits."""
    with app.app_context():
        print("Starting database migration...")

        # Check if column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('habit')]

        if 'longest_streak' in columns:
            print("[OK] Column 'longest_streak' already exists. Skipping migration.")
            return

        try:
            # Add the longest_streak column to the habit table
            print("Adding 'longest_streak' column to habit table...")
            with db.engine.connect() as conn:
                # SQLite syntax to add column
                conn.execute(text('ALTER TABLE habit ADD COLUMN longest_streak INTEGER NOT NULL DEFAULT 0'))
                conn.commit()

            print("[OK] Column added successfully!")

            # Initialize longest_streak values for existing habits
            # Set longest_streak to current streak_count for all habits
            # Using raw SQL to avoid ORM schema conflicts
            print("Initializing longest_streak values for existing habits...")
            with db.engine.connect() as conn:
                # Update all habits: set longest_streak = streak_count
                result = conn.execute(text('UPDATE habit SET longest_streak = streak_count'))
                conn.commit()
                print(f"[OK] Updated habits with initial longest_streak values!")

            print("\n[SUCCESS] Migration completed successfully!")
            print("All existing habits now have longest_streak initialized to their current streak.")

        except Exception as e:
            print(f"[ERROR] Error during migration: {e}")
            db.session.rollback()
            raise


if __name__ == '__main__':
    migrate()
