"""
Database Migration Script - Add Manual Payment Support
Adds PaymentRequest table and is_admin field to User table
"""

from app import app
from models import db, User, PaymentRequest
from sqlalchemy import inspect

def migrate():
    """Run database migrations for manual payment feature."""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        print("[MIGRATION] Starting migration for manual payment feature...")

        # Create all tables (will skip existing ones)
        db.create_all()
        print("[OK] Database tables created/verified")

        # Check if is_admin column exists in User table
        user_columns = [col['name'] for col in inspector.get_columns('user')]

        if 'is_admin' not in user_columns:
            print("[MIGRATION] Adding is_admin column to user table...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
                conn.execute(db.text("CREATE INDEX ix_user_is_admin ON user (is_admin)"))
                conn.commit()
            print("[OK] Added is_admin column with index")
        else:
            print("[OK] is_admin column already exists")

        # Check if payment_request table exists
        if 'payment_request' not in existing_tables:
            print("[MIGRATION] Creating payment_request table...")
            PaymentRequest.__table__.create(db.engine)
            print("[OK] payment_request table created")
        else:
            print("[OK] payment_request table already exists")

        print("\n[SUCCESS] Migration completed successfully!")
        print("\n[NEXT STEPS]:")
        print("1. Make yourself an admin by running:")
        print("   python make_admin.py your-email@example.com")
        print("2. Access admin dashboard at: /payment/admin/dashboard")
        print("3. Users can view plans at: /payment/plans")

if __name__ == '__main__':
    migrate()
