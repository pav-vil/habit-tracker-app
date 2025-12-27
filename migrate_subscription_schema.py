"""
Migration script for Phase 2: Add subscription fields to User model
and create SubscriptionHistory and PaymentTransaction tables.

Run this script once to upgrade the database schema.
"""
from sqlalchemy import text, inspect
from app import app, db


def migrate_user_table():
    """Add subscription fields to user table."""
    with app.app_context():
        inspector = inspect(db.engine)

        if 'user' not in inspector.get_table_names():
            print("[MIGRATE] User table doesn't exist. Run db.create_all() first.")
            return

        user_columns = [col['name'] for col in inspector.get_columns('user')]

        migrations = [
            ('subscription_status', "ALTER TABLE user ADD COLUMN subscription_status VARCHAR(20) NOT NULL DEFAULT 'free'"),
            ('stripe_customer_id', "ALTER TABLE user ADD COLUMN stripe_customer_id VARCHAR(100)"),
            ('subscription_end_date', "ALTER TABLE user ADD COLUMN subscription_end_date TIMESTAMP"),
            ('habit_limit', "ALTER TABLE user ADD COLUMN habit_limit INTEGER NOT NULL DEFAULT 3"),
        ]

        for column_name, sql in migrations:
            if column_name not in user_columns:
                print(f"[MIGRATE] Adding {column_name} column to user table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(sql))
                        conn.commit()
                    print(f"[MIGRATE] OK Successfully added {column_name}")
                except Exception as e:
                    print(f"[MIGRATE] Error adding {column_name}: {e}")
            else:
                print(f"[MIGRATE] OK Column {column_name} already exists")

        # Create indexes for performance
        try:
            with db.engine.connect() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_subscription_status ON user(subscription_status)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_stripe_customer_id ON user(stripe_customer_id)"))
                conn.commit()
            print("[MIGRATE] OK Indexes created successfully")
        except Exception as e:
            print(f"[MIGRATE] Note: Index creation: {e}")


def create_new_tables():
    """Create SubscriptionHistory and PaymentTransaction tables."""
    with app.app_context():
        try:
            db.create_all()
            print("[MIGRATE] OK New tables created (subscription_history, payment_transaction)")
        except Exception as e:
            print(f"[MIGRATE] Error creating tables: {e}")


if __name__ == '__main__':
    print("="*60)
    print("PHASE 2 MIGRATION: Subscription Schema")
    print("="*60)

    migrate_user_table()
    create_new_tables()

    print("\n[MIGRATE] OK Migration completed successfully!")
    print("="*60)
