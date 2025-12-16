"""
Initialize Database

Creates all database tables with correct schema.
Run this ONCE before first use: python init_db.py
"""

from app import app
from models import db

def init_database():
    """Create all database tables."""
    with app.app_context():
        print("=" * 60)
        print("Initializing Database")
        print("=" * 60)
        print("\n[*] Creating database tables...")

        db.create_all()

        print("[SUCCESS] Database initialized successfully!")
        print("\nTables created:")
        print("  - user (email, password_hash, timezone)")
        print("  - habit (name, description, streak_count, archived)")
        print("  - completion_log (habit tracking history)")
        print("\nYou can now run: python app.py")
        print("=" * 60)

if __name__ == '__main__':
    init_database()
