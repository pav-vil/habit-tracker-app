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

            # Migration 1: Increase password_hash column length in user table
            user_columns = inspector.get_columns('user')
            password_hash_col = next((col for col in user_columns if col['name'] == 'password_hash'), None)

            if password_hash_col and password_hash_col.get('type').length and password_hash_col['type'].length < 255:
                print(f"[AUTO-MIGRATE] Increasing password_hash column from {password_hash_col['type'].length} to 255 characters...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255)'
                        ))
                        conn.commit()
                    print("[AUTO-MIGRATE] ✓ Successfully increased password_hash column length")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error altering password_hash column: {e}")

            # Migration 1.5: Add newsletter_subscribed column to user table
            user_column_names = [col['name'] for col in user_columns]
            if 'newsletter_subscribed' not in user_column_names:
                print("[AUTO-MIGRATE] Adding newsletter_subscribed column to user table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE "user" ADD COLUMN newsletter_subscribed BOOLEAN NOT NULL DEFAULT FALSE'
                        ))
                        conn.commit()
                    print("[AUTO-MIGRATE] ✓ Successfully added newsletter_subscribed column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding newsletter_subscribed column: {e}")

            # Migration 2: Check if longest_streak column exists in habit table
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
                    print(f"[AUTO-MIGRATE] Error adding longest_streak column: {e}")

            # Migration 3: Add 'why' column to habit table for motivation/reason tracking
            habit_columns = [col['name'] for col in inspector.get_columns('habit')]

            if 'why' not in habit_columns:
                print("[AUTO-MIGRATE] Adding 'why' column to habit table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE habit ADD COLUMN why TEXT'
                        ))
                        conn.commit()

                    print("[AUTO-MIGRATE] ✓ Successfully added 'why' column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding 'why' column: {e}")

            print("[AUTO-MIGRATE] ✓ All migrations completed successfully")
        except Exception as e:
            print(f"[AUTO-MIGRATE] Error during migration check: {e}")
            # Don't crash the app if migration fails
            pass
