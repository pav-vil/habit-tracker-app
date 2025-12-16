"""
Database Migration Script: Complete Schema Update

Adds missing columns:
- user.timezone (for timezone support)
- habit.archived (for soft delete/archiving)

Run this script ONCE to update your existing database.
Usage: python migrate_database.py
"""

import sqlite3
import os

def migrate_database():
    """Add missing columns to user and habit tables."""

    db_path = 'habits.db'

    if not os.path.exists(db_path):
        print(f"[X] Database file '{db_path}' not found.")
        print("[OK] No migration needed - database will be created with correct schema on first run.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check and add timezone column to user table
        print("[*] Checking user table...")
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [column[1] for column in cursor.fetchall()]

        if 'timezone' not in user_columns:
            print("[*] Adding 'timezone' column to user table...")
            cursor.execute("""
                ALTER TABLE user
                ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL
            """)
            print("[OK] Added 'timezone' column to user table")
        else:
            print("[OK] Column 'timezone' already exists in user table")

        # Check and add archived column to habit table
        print("\n[*] Checking habit table...")
        cursor.execute("PRAGMA table_info(habit)")
        habit_columns = [column[1] for column in cursor.fetchall()]

        if 'archived' not in habit_columns:
            print("[*] Adding 'archived' column to habit table...")
            cursor.execute("""
                ALTER TABLE habit
                ADD COLUMN archived BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("[OK] Added 'archived' column to habit table")

            # Create index on archived field for better query performance
            print("[*] Creating index on 'archived' column...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_habit_archived
                ON habit(archived)
            """)
            print("[OK] Created index on 'archived' column")
        else:
            print("[OK] Column 'archived' already exists in habit table")

        conn.commit()
        print("\n" + "=" * 60)
        print("[SUCCESS] Migration completed successfully!")
        print("=" * 60)
        print("\nSummary:")
        print("  - User table: timezone column ready")
        print("  - Habit table: archived column ready")
        print("  - All existing data preserved")
        print("\nYou can now run: python app.py")

    except sqlite3.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        conn.rollback()
        print("\n[WARNING] If the error persists, consider:")
        print("   1. Backup your database: cp habits.db habits_backup.db")
        print("   2. Delete old database: rm habits.db")
        print("   3. Restart app: python app.py (will create new database)")

    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Complete Schema Update")
    print("=" * 60)
    print()
    migrate_database()
