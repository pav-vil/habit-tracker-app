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

    # Basic user information
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)  # Increased from 150 to 255 for scrypt hashes
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    newsletter_subscribed = db.Column(db.Boolean, default=False, nullable=False)  # Newsletter subscription status
    dark_mode = db.Column(db.Boolean, default=False, nullable=False)  # Dark mode preference
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Subscription fields
    subscription_tier = db.Column(db.String(20), default='free', nullable=False)  # 'free', 'monthly', 'annual', 'lifetime'
    subscription_status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'cancelled', 'expired', 'trial'
    subscription_start_date = db.Column(db.DateTime, nullable=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)  # For cancelled/expired subscriptions
    trial_end_date = db.Column(db.DateTime, nullable=True)  # Optional trial period

    # Payment provider IDs (for linking to external payment systems)
    stripe_customer_id = db.Column(db.String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True, index=True)
    paypal_subscription_id = db.Column(db.String(255), nullable=True, index=True)
    coinbase_charge_code = db.Column(db.String(255), nullable=True, index=True)

    # Billing information
    billing_email = db.Column(db.String(120), nullable=True)  # May differ from login email
    last_payment_date = db.Column(db.DateTime, nullable=True)
    payment_failures = db.Column(db.Integer, default=0, nullable=False)

    # Account deletion
    account_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deletion_scheduled_date = db.Column(db.DateTime, nullable=True)

    # Relationships
    habits = db.relationship(
        "Habit",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Hash and set user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_user_date(self):
        """Get current date in user's timezone."""
        from zoneinfo import ZoneInfo
        from datetime import datetime
        user_tz = ZoneInfo(self.timezone)
        return datetime.now(user_tz).date()

    def is_premium(self):
        """Check if user has a premium subscription (monthly, annual, or lifetime)."""
        return self.subscription_tier in ['monthly', 'annual', 'lifetime']

    def can_create_habit(self):
        """
        Check if user can create a new habit.
        Free tier: Limited to 3 habits
        Premium tiers: Unlimited habits
        """
        if self.is_premium():
            return True

        # Count active (non-archived) habits
        active_count = Habit.query.filter_by(
            user_id=self.id,
            archived=False
        ).count()

        return active_count < 3

    def get_habit_limit(self):
        """
        Get the habit limit for this user.
        Returns None for unlimited (premium) or 3 for free tier.
        """
        return None if self.is_premium() else 3

    def __repr__(self):
        return f"<User id={self.id} email={self.email} tier={self.subscription_tier}>"


class Habit(db.Model):
    __tablename__ = "habit"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    why = db.Column(db.Text, nullable=True)  # Why the user wants to track this habit (motivation)
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


class Subscription(db.Model):
    """
    Tracks subscription history and changes for each user.
    Each record represents a subscription period (created when user subscribes/upgrades/downgrades).
    """
    __tablename__ = "subscription"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Subscription details
    tier = db.Column(db.String(20), nullable=False)  # 'monthly', 'annual', 'lifetime'
    status = db.Column(db.String(20), nullable=False, index=True)  # 'active', 'cancelled', 'expired'

    # Payment provider information
    payment_provider = db.Column(db.String(20), nullable=False, index=True)  # 'stripe', 'paypal', 'coinbase'
    provider_subscription_id = db.Column(db.String(255), nullable=True, index=True)  # External subscription ID

    # Subscription timeline
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)  # When cancelled or expired
    next_billing_date = db.Column(db.DateTime, nullable=True)  # For active recurring subscriptions

    # Pricing information (stored for historical record)
    amount_paid = db.Column(db.Float, nullable=False)  # Amount paid for this subscription
    currency = db.Column(db.String(3), default='USD', nullable=False)  # USD, EUR, etc.

    # Relationships
    user = db.relationship('User', backref=db.backref('subscription_history', lazy='dynamic'))

    def __repr__(self):
        return f'<Subscription user_id={self.user_id} tier={self.tier} status={self.status} provider={self.payment_provider}>'


class Payment(db.Model):
    """
    Tracks all payment transactions (successful, failed, pending, refunded).
    Each record represents a single payment attempt or transaction.
    """
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True, index=True)

    # Payment provider information
    payment_provider = db.Column(db.String(20), nullable=False, index=True)  # 'stripe', 'paypal', 'coinbase'
    provider_transaction_id = db.Column(db.String(255), nullable=False, unique=True, index=True)  # External transaction ID

    # Transaction details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.String(20), nullable=False, index=True)  # 'completed', 'pending', 'failed', 'refunded'

    # Payment type
    payment_type = db.Column(db.String(20), nullable=False)  # 'subscription', 'upgrade', 'renewal', 'lifetime'

    # Metadata
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)  # Error messages, refund reasons, admin notes

    # Relationships
    user = db.relationship('User', backref=db.backref('payments', lazy='dynamic'))
    subscription = db.relationship('Subscription', backref=db.backref('payments', lazy='dynamic'))

    def __repr__(self):
        return f'<Payment user_id={self.user_id} provider={self.payment_provider} amount={self.amount} status={self.status}>'
