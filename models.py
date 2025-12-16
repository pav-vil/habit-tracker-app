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
    
    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class Habit(db.Model):
    __tablename__ = "habit"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    streak_count = db.Column(db.Integer, default=0, nullable=False)
    last_completed = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def complete(self):
        today = date.today()
        if self.last_completed == today:
            return False
        if self.last_completed:
            yesterday = today - timedelta(days=1)
            if self.last_completed == yesterday:
                self.streak_count += 1
            else:
                self.streak_count = 1
        else:
            self.streak_count = 1
        self.last_completed = today
        return True
    
    def __repr__(self):
        return f"<Habit id={self.id} name='{self.name}' streak={self.streak_count}>"


class CompletionLog(db.Model):
    __tablename__ = "completion_log"
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    completed_at = db.Column(db.Date, nullable=False)
    
    habit = db.relationship(
        'Habit',
        backref=db.backref('completions', lazy='dynamic', cascade='all, delete-orphan')
    )
    
    def __repr__(self):
        return f'<CompletionLog {self.habit_id} on {self.completed_at}>'
