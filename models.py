"""
Database models for HabitFlow - Habit Tracker App
Models: User, Habit
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# SQLAlchemy instance (initialized in app.py)
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model representing registered users of the habit tracker app."""
    
    __tablename__ = "user"
    
    # Primary key - auto-incrementing user ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # User email address (unique and indexed for fast lookup)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    # Hashed password stored using Werkzeug security
    password_hash = db.Column(db.String(150), nullable=False)
    
    # Timestamp when the user account was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # One-to-many relationship with Habit
    # Deleting a user will automatically delete all their habits
    habits = db.relationship(
        "Habit",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    def set_password(self, password):
        """
        Hash and store the user's password securely.
        
        Args:
            password (str): Plain text password to hash
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify a password against the stored hash.
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        """Debug-friendly string representation."""
        return f"<User id={self.id} email={self.email}>"


class Habit(db.Model):
    """Habit model representing a habit tracked by a user."""
    
    __tablename__ = "habit"
    
    # Primary key - auto-incrementing habit ID
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Foreign key linking the habit to its owner (User)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
    )

class CompletionLog(db.Model):
    """Tracks every habit completion for historical analysis."""
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    completed_at = db.Column(db.Date, nullable=False)  # Date of completion
    
    # Relationship back to habit
    habit = db.relationship('Habit', backref=db.backref('completions', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<CompletionLog {self.habit_id} on {self.completed_at}>'
    
    # Name/title of the habit (e.g., "Morning Workout")
    name = db.Column(db.String(100), nullable=False)
    
    # Optional longer description of the habit
    description = db.Column(db.String(500), nullable=True)
    
    # Current streak count for consecutive completions
    streak_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Date when the habit was last completed (for streak calculation)
    last_completed = db.Column(db.Date, nullable=True)
    
    # Timestamp when the habit was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def complete(self):
        """
        Mark habit as completed today and update streak.
        
        Logic:
        - If completed today already: do nothing
        - If completed yesterday: increment streak
        - If gap > 1 day: reset streak to 1
        """
        from datetime import date, timedelta
        
        today = date.today()
        
        # Check if already completed today
        if self.last_completed == today:
            return False  # Already completed today
        
        # Calculate streak
        if self.last_completed:
            yesterday = today - timedelta(days=1)
            if self.last_completed == yesterday:
                # Streak continues
                self.streak_count += 1
            else:
                # Streak broken, reset to 1
                self.streak_count = 1
        else:
            # First completion
            self.streak_count = 1
        
        # Update last completed date
        self.last_completed = today
        return True  # Successfully completed
    
    def __repr__(self):
        """Debug-friendly string representation."""
        return f"<Habit id={self.id} name='{self.name}' streak={self.streak_count} user_id={self.user_id}>"
    
