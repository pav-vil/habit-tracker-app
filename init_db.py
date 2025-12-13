"""
Database initialization script for HabitFlow
Creates database tables and adds sample data for testing
"""

from app import app, db
from models import User, Habit
from datetime import datetime, timedelta


def init_database():
    """Initialize database with tables and sample data."""
    
    with app.app_context():
        print("🗑️  Dropping existing tables...")
        db.drop_all()
        
        print("📊 Creating new tables...")
        db.create_all()
        
        print("👤 Creating test user...")
        # Create a test user
        test_user = User(email="test@habitflow.com")
        test_user.set_password("password123")
        db.session.add(test_user)
        db.session.commit()
        
        print("✅ Creating sample habits...")
        # Create 3 sample habits
        habits = [
            Habit(
                user_id=test_user.id,
                name="Morning Workout",
                description="30 minutes of exercise every morning",
                streak_count=5,
                last_completed=datetime.now().date()
            ),
            Habit(
                user_id=test_user.id,
                name="Read for 20 Minutes",
                description="Read books or articles daily",
                streak_count=3,
                last_completed=(datetime.now() - timedelta(days=1)).date()
            ),
            Habit(
                user_id=test_user.id,
                name="Drink 8 Glasses of Water",
                description="Stay hydrated throughout the day",
                streak_count=0,
                last_completed=None
            )
        ]
        
        db.session.add_all(habits)
        db.session.commit()
        
        print("\n✅ Database initialized successfully!")
        print(f"📧 Test user email: test@habitflow.com")
        print(f"🔑 Test user password: password123")
        print(f"🎯 Sample habits created: {len(habits)}")
        print("\n🧪 Test it with:")
        print("   flask shell")
        print("   >>> from models import User, Habit")
        print("   >>> User.query.all()")
        print("   >>> Habit.query.all()")


if __name__ == "__main__":
    init_database()
    