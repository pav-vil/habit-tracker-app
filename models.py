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

    # Subscription fields
    subscription_status = db.Column(
        db.String(20),
        default='free',
        nullable=False,
        index=True
    )  # Values: 'free', 'monthly', 'annual', 'lifetime'
    stripe_customer_id = db.Column(db.String(100), nullable=True, index=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    habit_limit = db.Column(db.Integer, default=3, nullable=False)

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

    def is_premium_active(self):
        """Check if user has an active premium subscription."""
        if self.subscription_status == 'lifetime':
            return True

        if self.subscription_status in ['monthly', 'annual']:
            if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
                return True
            # Subscription expired - downgrade to free
            self.subscription_status = 'free'
            self.habit_limit = 3
            return False

        return False

    def can_add_more_habits(self):
        """Check if user can create additional habits."""
        if self.is_premium_active():
            return True

        # Free tier - check against limit
        active_habit_count = Habit.query.filter_by(
            user_id=self.id,
            archived=False
        ).count()

        return active_habit_count < self.habit_limit

    def get_habit_limit(self):
        """Get user's current habit limit."""
        if self.is_premium_active():
            return None  # Unlimited
        return self.habit_limit

    def __repr__(self):
        return f"<User id={self.id} email={self.email} status={self.subscription_status}>"


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


class SubscriptionHistory(db.Model):
    """Track all subscription changes for audit and billing history."""
    __tablename__ = "subscription_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # Subscription details
    subscription_type = db.Column(db.String(20), nullable=False)  # 'monthly', 'annual', 'lifetime'
    status = db.Column(db.String(20), nullable=False)  # 'active', 'cancelled', 'expired', 'upgraded', 'downgraded'

    # Dates
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)

    # Payment tracking
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=True)  # Amount paid
    currency = db.Column(db.String(3), default='USD', nullable=False)

    # Metadata
    notes = db.Column(db.String(500), nullable=True)  # For manual adjustments, cancellation reasons, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = db.relationship("User", backref=db.backref("subscription_history", lazy="dynamic"))

    def __repr__(self):
        return f"<SubscriptionHistory user_id={self.user_id} type={self.subscription_type} status={self.status}>"


class PaymentTransaction(db.Model):
    """Track all payment transactions for comprehensive billing records."""
    __tablename__ = "payment_transaction"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # Payment provider details
    provider = db.Column(db.String(20), default='stripe', nullable=False)  # 'stripe', 'paypal', 'coinbase'
    provider_transaction_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    stripe_invoice_id = db.Column(db.String(100), nullable=True)

    # Transaction details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'pending', 'completed', 'failed', 'refunded'

    # Subscription link
    subscription_type = db.Column(db.String(20), nullable=False)  # 'monthly', 'annual', 'lifetime'
    subscription_history_id = db.Column(
        db.Integer,
        db.ForeignKey("subscription_history.id"),
        nullable=True
    )

    # Timestamps
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Payment metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = db.Column(db.JSON, nullable=True)  # Store additional provider-specific data

    # Relationships
    user = db.relationship("User", backref=db.backref("payment_transactions", lazy="dynamic"))
    subscription_history = db.relationship(
        "SubscriptionHistory",
        backref=db.backref("payment_transactions", lazy="dynamic")
    )

    def __repr__(self):
        return f"<PaymentTransaction id={self.id} user_id={self.user_id} amount={self.amount} status={self.status}>"
