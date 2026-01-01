"""
Script to initialize badge definitions in the database.
Run this once to populate the Badge table with default badges.
"""

from app import app
from badge_service import initialize_badges

if __name__ == '__main__':
    with app.app_context():
        print("[INIT-BADGES] Initializing badge definitions...")
        initialize_badges()
        print("[INIT-BADGES] Badge initialization complete!")
