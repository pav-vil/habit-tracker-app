"""
Migration: Add PomodoroSession table
Run this migration to add Pomodoro timer tracking functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, PomodoroSession

# Import Flask app
import app as flask_app

def migrate():
    """Create pomodoro_session table"""
    with flask_app.app.app_context():
        print("[MIGRATION] Creating pomodoro_session table...")
        db.create_all()
        print("[MIGRATION] ✅ pomodoro_session table created successfully!")

if __name__ == '__main__':
    migrate()
