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
                print("[AUTO-MIGRATE] OK Fresh database - no migrations needed")
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

                    print("[AUTO-MIGRATE] OK Successfully added longest_streak column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding column: {e}")

            # Check and add subscription fields to user table
            if 'user' in inspector.get_table_names():
                user_columns = [col['name'] for col in inspector.get_columns('user')]

                subscription_migrations = [
                    ('subscription_status', "ALTER TABLE user ADD COLUMN subscription_status VARCHAR(20) NOT NULL DEFAULT 'free'"),
                    ('stripe_customer_id', "ALTER TABLE user ADD COLUMN stripe_customer_id VARCHAR(100)"),
                    ('subscription_end_date', "ALTER TABLE user ADD COLUMN subscription_end_date TIMESTAMP"),
                    ('habit_limit', "ALTER TABLE user ADD COLUMN habit_limit INTEGER NOT NULL DEFAULT 3"),
                ]

                for column_name, sql in subscription_migrations:
                    if column_name not in user_columns:
                        print(f"[AUTO-MIGRATE] Adding {column_name} to user table...")
                        try:
                            with db.engine.connect() as conn:
                                conn.execute(text(sql))
                                conn.commit()
                            print(f"[AUTO-MIGRATE] OK Successfully added {column_name}")
                        except Exception as e:
                            print(f"[AUTO-MIGRATE] Error adding {column_name}: {e}")

            print("[AUTO-MIGRATE] OK Database schema is up to date")
        except Exception as e:
            print(f"[AUTO-MIGRATE] Error during migration check: {e}")
            # Don't crash the app if migration fails
            pass
