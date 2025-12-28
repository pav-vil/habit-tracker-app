"""
Emergency migration script to add missing habit_limit column.
Run this ONCE on Render: python fix_habit_limit_migration.py
"""
from app import app, db
from sqlalchemy import text

def fix_habit_limit():
    """Add habit_limit column if it doesn't exist."""
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='user' AND column_name='habit_limit'"
                ))

                if result.fetchone() is None:
                    print("[FIX] Adding habit_limit column...")
                    # Add the column
                    conn.execute(text(
                        "ALTER TABLE \"user\" ADD COLUMN habit_limit INTEGER NOT NULL DEFAULT 3"
                    ))
                    conn.commit()
                    print("[FIX] ✓ Successfully added habit_limit column")
                else:
                    print("[FIX] habit_limit column already exists")

        except Exception as e:
            print(f"[FIX] Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("="*60)
    print("FIXING HABIT_LIMIT COLUMN")
    print("="*60)
    fix_habit_limit()
    print("="*60)
