"""
Automatic migration helper - runs on app startup
Safely adds missing columns without breaking the app
"""
from sqlalchemy import text, inspect


def auto_migrate_database(app, db):
    """
    Automatically add missing columns to the database.
    Runs safely on every app startup - won't break if column already exists.
    """
    with app.app_context():
        try:
            inspector = inspect(db.engine)

            # Check if habit table exists first
            if 'habit' not in inspector.get_table_names():
                print("[AUTO-MIGRATE] ✓ Fresh database - no migrations needed")
                return

            # Check if longest_streak column exists in habit table
            habit_columns = [col['name'] for col in inspector.get_columns('habit')]

            if 'longest_streak' not in habit_columns:
                print("[AUTO-MIGRATE] Adding longest_streak column to habit table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE habit ADD COLUMN longest_streak INTEGER NOT NULL DEFAULT 0'
                        ))
                        conn.commit()

                    # Update existing habits to set longest_streak = streak_count
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'UPDATE habit SET longest_streak = streak_count'
                        ))
                        conn.commit()

                    print("[AUTO-MIGRATE] ✓ Successfully added longest_streak column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding column: {e}")
            else:
                print("[AUTO-MIGRATE] ✓ Database schema is up to date")
        except Exception as e:
            print(f"[AUTO-MIGRATE] Error during migration check: {e}")
            # Don't crash the app if migration fails
            pass
