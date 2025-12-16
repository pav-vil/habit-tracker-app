"""
Database Migration Script: Add 'archived' field to Habit table

Run this script ONCE to update your existing database with the new archived field.
Usage: python migrate_add_archived.py
"""

import sqlite3
import os

def migrate_database():
    """Add archived column to habit table if it doesn't exist."""

    db_path = 'habits.db'

    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found.")
        print("No migration needed - database will be created with correct schema on first run.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if archived column already exists
        cursor.execute("PRAGMA table_info(habit)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'archived' in columns:
            print("✅ Column 'archived' already exists. No migration needed.")
            conn.close()
            return

        print("🔄 Adding 'archived' column to habit table...")

        # Add the archived column with default value False (0)
        cursor.execute("""
            ALTER TABLE habit
            ADD COLUMN archived BOOLEAN DEFAULT 0 NOT NULL
        """)

        # Create index on archived field for better query performance
        print("🔄 Creating index on 'archived' column...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habit_archived
            ON habit(archived)
        """)

        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Added 'archived' column to habit table")
        print("   - Created index on 'archived' column")
        print("   - All existing habits set to archived=False (active)")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add Archived Field")
    print("=" * 60)
    migrate_database()
    print("=" * 60)
