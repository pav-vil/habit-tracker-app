"""
Migration script to add notes, mood, and created_at columns to CompletionLog table
"""
import sqlite3
from datetime import datetime

def migrate_completion_log():
    """Add missing columns to completion_log table"""

    db_path = 'instance/habits.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("[MIGRATION] Starting CompletionLog migration...")

    # Check current schema
    cursor.execute("PRAGMA table_info(completion_log)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"[MIGRATION] Current columns: {list(columns.keys())}")

    migrations_applied = []

    # Add notes column if missing
    if 'notes' not in columns:
        try:
            cursor.execute("ALTER TABLE completion_log ADD COLUMN notes TEXT")
            print("[MIGRATION] [+] Added 'notes' column (TEXT)")
            migrations_applied.append('notes')
        except Exception as e:
            print(f"[MIGRATION] [X] Error adding 'notes' column: {e}")
    else:
        print("[MIGRATION] - 'notes' column already exists")

    # Add mood column if missing
    if 'mood' not in columns:
        try:
            cursor.execute("ALTER TABLE completion_log ADD COLUMN mood VARCHAR(10)")
            print("[MIGRATION] [+] Added 'mood' column (VARCHAR(10))")
            migrations_applied.append('mood')
        except Exception as e:
            print(f"[MIGRATION] [X] Error adding 'mood' column: {e}")
    else:
        print("[MIGRATION] - 'mood' column already exists")

    # Add created_at column if missing
    if 'created_at' not in columns:
        try:
            # Add column with default value for existing rows
            default_date = datetime.utcnow().isoformat()
            cursor.execute(f"ALTER TABLE completion_log ADD COLUMN created_at DATETIME DEFAULT '{default_date}'")
            print("[MIGRATION] [+] Added 'created_at' column (DATETIME)")
            migrations_applied.append('created_at')
        except Exception as e:
            print(f"[MIGRATION] [X] Error adding 'created_at' column: {e}")
    else:
        print("[MIGRATION] - 'created_at' column already exists")

    # Commit changes
    conn.commit()

    # Verify migration
    cursor.execute("PRAGMA table_info(completion_log)")
    new_columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"\n[MIGRATION] Updated columns: {list(new_columns.keys())}")

    conn.close()

    if migrations_applied:
        print(f"\n[MIGRATION] [+] Migration completed successfully!")
        print(f"[MIGRATION] Applied: {', '.join(migrations_applied)}")
    else:
        print(f"\n[MIGRATION] - No migrations needed. Schema is up to date.")

    return True

if __name__ == '__main__':
    migrate_completion_log()
