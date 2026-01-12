"""
Script to create test user accounts for development/testing
Run this to create the test accounts shown on the login page:
    python create_test_users.py
"""

from app import app, db
from models import User

def create_test_users():
    """Create test accounts that match the login page credentials"""

    test_accounts = [
        {
            'email': 'test@habitflow.com',
            'password': 'Test1234',  # 8+ chars, uppercase, number
            'timezone': 'UTC'
        },
        {
            'email': 'demo@habitflow.com',
            'password': 'Demo1234',  # 8+ chars, uppercase, number
            'timezone': 'UTC'
        }
    ]

    with app.app_context():
        for account in test_accounts:
            email = account['email']
            password = account['password']

            print(f"\nProcessing: {email}")

            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()

            if existing_user:
                print(f"  User exists - resetting password...")
                existing_user.set_password(password)
                db.session.commit()
                print(f"  Password reset successfully")
            else:
                # Create new user
                new_user = User(
                    email=email,
                    timezone=account['timezone'],
                    subscription_tier='free',
                    subscription_status='active',
                    habit_limit=3
                )
                new_user.set_password(password)

                db.session.add(new_user)
                db.session.commit()
                print(f"  User created successfully")

            # Verify account
            user = User.query.filter_by(email=email).first()
            password_ok = user.check_password(password)
            print(f"  Verified: {'YES' if password_ok else 'FAILED'}")

        print("\n" + "="*50)
        print("TEST ACCOUNTS READY")
        print("="*50)
        print("Account 1: test@habitflow.com / Test1234")
        print("Account 2: demo@habitflow.com / Demo1234")
        print("="*50)

if __name__ == '__main__':
    create_test_users()
