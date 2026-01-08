"""
Script to create production user account
Run this on Render console or production server:
    python create_production_user.py
"""

from app import app, db
from models import User

def create_production_user():
    """Create habitprueba@aol.co account in production database"""

    with app.app_context():
        email = 'habitprueba@aol.co'
        password = 'Prueba123'  # Strong password: 8+ chars, uppercase, number

        print(f"Creating user account: {email}")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            print(f"User {email} already exists!")
            print("Resetting password...")
            existing_user.set_password(password)
            db.session.commit()
            print("✓ Password reset successfully")
        else:
            # Create new user
            new_user = User(
                email=email,
                timezone='America/Costa_Rica',
                subscription_tier='free',
                subscription_status='active',
                habit_limit=3
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()
            print("✓ User created successfully")

        # Verify account
        user = User.query.filter_by(email=email).first()
        password_ok = user.check_password(password)

        print("\n" + "="*50)
        print("PRODUCTION ACCOUNT READY")
        print("="*50)
        print(f"Email:        {email}")
        print(f"Password:     {password}")
        print(f"Verified:     {'✓ YES' if password_ok else '✗ FAILED'}")
        print(f"Tier:         {user.subscription_tier}")
        print(f"Habit Limit:  {user.habit_limit}")
        print("="*50)

if __name__ == '__main__':
    create_production_user()
