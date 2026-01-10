#!/usr/bin/env python3
"""
Script to grant premium access to a user.
Usage: python grant_premium.py <email> [tier]

Tier options: lifetime (default), annual, monthly
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app import app, db
from models import User, SubscriptionHistory


def grant_premium(email, tier='lifetime'):
    """Grant premium access to a user by email."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"Error: User with email '{email}' not found.")
            return False

        # Store previous state
        previous_tier = user.subscription_tier
        previous_status = user.subscription_status

        # Update user subscription
        user.subscription_tier = tier
        user.subscription_status = 'active'
        user.subscription_start_date = datetime.utcnow()
        user.habit_limit = 999  # Effectively unlimited

        # Set end date based on tier
        if tier == 'lifetime':
            user.subscription_end_date = None
        elif tier == 'monthly':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        elif tier == 'annual':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)

        # Create subscription history record
        subscription_record = SubscriptionHistory(
            user_id=user.id,
            subscription_type=tier,
            status='active',
            amount=0,
            currency='USD',
            notes='Premium access granted via script'
        )
        db.session.add(subscription_record)

        try:
            db.session.commit()
            print(f"Success! Granted {tier} premium to {email}")
            print(f"  Previous tier: {previous_tier}")
            print(f"  Previous status: {previous_status}")
            print(f"  New tier: {user.subscription_tier}")
            print(f"  New status: {user.subscription_status}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            return False


def make_admin(email):
    """Grant admin privileges to a user."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"Error: User with email '{email}' not found.")
            return False

        user.is_admin = True

        try:
            db.session.commit()
            print(f"Success! {email} is now an admin.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python grant_premium.py <email> [tier]")
        print("       python grant_premium.py --admin <email>")
        print("\nTier options: lifetime (default), annual, monthly")
        sys.exit(1)

    if sys.argv[1] == '--admin':
        if len(sys.argv) < 3:
            print("Error: Email required for --admin flag")
            sys.exit(1)
        make_admin(sys.argv[2])
    else:
        email = sys.argv[1]
        tier = sys.argv[2] if len(sys.argv) > 2 else 'lifetime'

        if tier not in ['lifetime', 'annual', 'monthly']:
            print(f"Error: Invalid tier '{tier}'. Use: lifetime, annual, or monthly")
            sys.exit(1)

        grant_premium(email, tier)
