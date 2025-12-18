"""
Database models for HabitFlow - Habit Tracker App
Models: User, Habit, CompletionLog
"""

from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(150), nullable=False)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    habits = db.relationship(
        "Habit",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_user_date(self):
        """Get current date in user's timezone."""
        from zoneinfo import ZoneInfo
        from datetime import datetime
        user_tz = ZoneInfo(self.timezone)
        return datetime.now(user_tz).date()

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class Habit(db.Model):
    __tablename__ = "habit"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    streak_count = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)  # Track all-time best streak
    last_completed = db.Column(db.Date, nullable=True)
    archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def complete(self, today=None):
        """
        Mark habit as completed for today.
        Updates current streak and longest streak if a new record is set.
        Returns True if completed successfully, False if already completed today.

        Args:
            today: Optional date to use (for testing or timezone support).
                   If None, uses date.today()
        """
        if today is None:
            today = date.today()

        # Check if already completed today
        if self.last_completed == today:
            return False

        # Calculate current streak
        if self.last_completed:
            yesterday = today - timedelta(days=1)
            if self.last_completed == yesterday:
                # Continue the streak
                self.streak_count += 1
            else:
                # Streak broken, restart at 1
                self.streak_count = 1
        else:
            # First completion ever
            self.streak_count = 1

        # Update longest streak if current streak is a new record
        if self.streak_count > self.longest_streak:
            self.longest_streak = self.streak_count

        self.last_completed = today
        return True
    
    def __repr__(self):
        return f"<Habit id={self.id} name='{self.name}' streak={self.streak_count}>"


class CompletionLog(db.Model):
    __tablename__ = "completion_log"

    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False, index=True)
    completed_at = db.Column(db.Date, nullable=False, index=True)
    
    habit = db.relationship(
        'Habit',
        backref=db.backref('completions', lazy='dynamic', cascade='all, delete-orphan')
    )
    
    def __repr__(self):
        return f'<CompletionLog {self.habit_id} on {self.completed_at}>'
