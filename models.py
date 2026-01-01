"""
Database models for HabitFlow - Habit Tracker App
Models: User, Habit, CompletionLog, SubscriptionHistory, PaymentTransaction, Subscription, Payment
"""

from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import secrets

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

    # Subscription fields (merged from both versions)
    subscription_tier = db.Column(db.String(20), default='free', nullable=False)  # 'free', 'monthly', 'annual', 'lifetime'
    subscription_status = db.Column(db.String(20), default='active', nullable=False, index=True)  # 'active', 'cancelled', 'expired', 'trial'
    subscription_start_date = db.Column(db.DateTime, nullable=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)  # For cancelled/expired subscriptions
    trial_end_date = db.Column(db.DateTime, nullable=True)  # Optional trial period
    habit_limit = db.Column(db.Integer, default=3, nullable=False)

    # Payment provider IDs (for linking to external payment systems)
    stripe_customer_id = db.Column(db.String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True, index=True)
    paypal_subscription_id = db.Column(db.String(255), nullable=True, index=True)
    coinbase_charge_code = db.Column(db.String(255), nullable=True, index=True)

    # Billing information
    billing_email = db.Column(db.String(120), nullable=True)  # May differ from login email
    last_payment_date = db.Column(db.DateTime, nullable=True)
    payment_failures = db.Column(db.Integer, default=0, nullable=False)

    # Email notification settings
    email_notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    reminder_time = db.Column(db.String(5), default='09:00', nullable=False)
    reminder_days = db.Column(db.String(20), default='all', nullable=False)
    last_reminder_sent = db.Column(db.Date, nullable=True)

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

    def is_premium_active(self):
        """Check if user has an active premium subscription."""
        if self.subscription_tier == 'lifetime':
            return True

        if self.subscription_tier in ['monthly', 'annual']:
            if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
                return True
            # Subscription expired - downgrade to free
            self.subscription_tier = 'free'
            self.subscription_status = 'expired'
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

    def can_create_habit(self):
        """
        Check if user can create a new habit.
        Free tier: Limited to 3 habits
        Premium tiers: Unlimited habits
        """
        return self.can_add_more_habits()

    def get_habit_limit(self):
        """
        Get the habit limit for this user.
        Returns None for unlimited (premium) or habit_limit value for free tier.
        """
        if self.is_premium_active():
            return None  # Unlimited
        return self.habit_limit

    def __repr__(self):
        return f"<User id={self.id} email={self.email} tier={self.subscription_tier} status={self.subscription_status}>"


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


class PomodoroSession(db.Model):
    """Track Pomodoro timer sessions for habits."""
    __tablename__ = "pomodoro_session"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Session details
    duration_minutes = db.Column(db.Integer, default=25, nullable=False)  # Standard pomodoro is 25 min
    session_type = db.Column(db.String(20), default='work', nullable=False)  # 'work', 'short_break', 'long_break'
    completed = db.Column(db.Boolean, default=True, nullable=False)  # False if session was abandoned

    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    habit = db.relationship(
        'Habit',
        backref=db.backref('pomodoro_sessions', lazy='dynamic', cascade='all, delete-orphan')
    )
    user = db.relationship('User', backref=db.backref('pomodoro_sessions', lazy='dynamic'))

    def __repr__(self):
        return f'<PomodoroSession habit_id={self.habit_id} duration={self.duration_minutes}min type={self.session_type}>'


class SubscriptionHistory(db.Model):
    """Track all subscription changes for audit and billing history (LOCAL/HEAD version)."""
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
    """Track all payment transactions for comprehensive billing records (LOCAL/HEAD version)."""
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


class Subscription(db.Model):
    """
    Tracks subscription history and changes for each user (REMOTE version).
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
    user = db.relationship('User', backref=db.backref('subscriptions', lazy='dynamic'))

    def __repr__(self):
        return f'<Subscription user_id={self.user_id} tier={self.tier} status={self.status} provider={self.payment_provider}>'


class Payment(db.Model):
    """
    Tracks all payment transactions (successful, failed, pending, refunded) (REMOTE version).
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


class AuditLog(db.Model):
    """
    Audit log for security events and sensitive user actions.
    Tracks login attempts, password changes, account modifications, etc.
    Used for security monitoring and GDPR compliance.
    """
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # None for failed logins

    # Event details
    event_type = db.Column(db.String(50), nullable=False, index=True)  # 'login', 'logout', 'password_change', etc.
    event_description = db.Column(db.String(255), nullable=False)  # Human-readable description
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)  # Browser/device info

    # Event result
    success = db.Column(db.Boolean, default=True, nullable=False)  # True if action succeeded
    error_message = db.Column(db.Text, nullable=True)  # Error details if action failed

    # Additional metadata (JSON)
    event_metadata = db.Column(db.Text, nullable=True)  # Store extra details as JSON string

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<AuditLog user_id={self.user_id} event={self.event_type} success={self.success}>'


def log_security_event(user_id, event_type, description, success=True, error_message=None, metadata=None, ip_address=None, user_agent=None):
    """
    Helper function to log security events to the audit log.

    Args:
        user_id: User ID (None for unauthenticated events like failed logins)
        event_type: Type of event (login, logout, password_change, account_delete, etc.)
        description: Human-readable description
        success: Whether the action succeeded
        error_message: Error details if action failed
        metadata: Additional details as dict (will be JSON serialized)
        ip_address: Client IP address
        user_agent: Client user agent string

    Returns:
        AuditLog object that was created
    """
    import json
    from flask import request

    # Auto-capture IP and user agent from request context if not provided
    if ip_address is None:
        try:
            ip_address = request.remote_addr
        except:
            ip_address = None

    if user_agent is None:
        try:
            user_agent = request.headers.get('User-Agent', '')[:255]  # Truncate to 255 chars
        except:
            user_agent = None

    # Convert metadata dict to JSON string
    metadata_json = None
    if metadata:
        try:
            metadata_json = json.dumps(metadata)
        except:
            metadata_json = str(metadata)

    # Create audit log entry
    audit_entry = AuditLog(
        user_id=user_id,
        event_type=event_type,
        event_description=description,
        success=success,
        error_message=error_message,
        event_metadata=metadata_json,
        ip_address=ip_address,
        user_agent=user_agent
    )

    try:
        db.session.add(audit_entry)
        db.session.commit()
        print(f"[AUDIT] {event_type}: {description} (user_id={user_id}, success={success})")
        return audit_entry
    except Exception as e:
        db.session.rollback()
        print(f"[AUDIT] Error logging event: {e}")
        return None


# ============================================================================
# PERIOD TRACKING MODELS
# ============================================================================

class PeriodCycle(db.Model):
    """
    Model for tracking menstrual cycles.
    Each instance represents one complete cycle from period start to the next period start.
    """
    __tablename__ = 'period_cycle'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Period Dates
    start_date = db.Column(db.Date, nullable=False, index=True)  # When period started
    end_date = db.Column(db.Date, nullable=True)  # When period ended (null if ongoing)

    # Cycle Metadata
    cycle_length = db.Column(db.Integer, nullable=True)  # Days from this period start to next (calculated later)
    is_predicted = db.Column(db.Boolean, default=False, nullable=False)  # True for future predictions

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('period_cycles', lazy='dynamic', cascade='all, delete-orphan'))
    daily_logs = db.relationship('PeriodDailyLog', backref='cycle', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PeriodCycle user_id={self.user_id} start={self.start_date} predicted={self.is_predicted}>'


class PeriodDailyLog(db.Model):
    """
    Model for tracking daily symptoms, mood, and flow intensity during menstrual cycle.
    One log per day per user for detailed tracking.
    """
    __tablename__ = 'period_daily_log'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    cycle_id = db.Column(db.Integer, db.ForeignKey('period_cycle.id'), nullable=True, index=True)  # Nullable - log can exist without cycle
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Date and Flow Tracking
    log_date = db.Column(db.Date, nullable=False, index=True)
    flow_intensity = db.Column(db.String(20), nullable=True)  # 'light', 'medium', 'heavy', or null

    # Symptoms (stored as JSON array)
    symptoms = db.Column(db.JSON, nullable=True, default=list)  # e.g., ["cramps", "headache", "fatigue"]

    # Mood Tracking
    mood = db.Column(db.String(20), nullable=True)  # 'happy', 'sad', 'irritable', 'anxious', 'normal'

    # Notes
    notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('period_logs', lazy='dynamic'))

    # Unique Constraint: One log per day per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'log_date', name='unique_user_date_log'),
    )

    def __repr__(self):
        return f'<PeriodDailyLog user_id={self.user_id} date={self.log_date} flow={self.flow_intensity}>'


class PeriodSettings(db.Model):
    """
    Model for storing user preferences for period tracking feature.
    One settings record per user.
    """
    __tablename__ = 'period_settings'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)

    # Feature Toggle
    period_tracking_enabled = db.Column(db.Boolean, default=False, nullable=False)

    # Cycle Preferences
    average_cycle_length = db.Column(db.Integer, default=28, nullable=False)  # User's typical cycle length in days
    average_period_duration = db.Column(db.Integer, default=5, nullable=False)  # Typical period length in days

    # Reminder Settings
    reminder_enabled = db.Column(db.Boolean, default=True, nullable=False)
    reminder_days_before = db.Column(db.Integer, default=2, nullable=False)  # Send reminder N days before predicted period
    last_reminder_sent = db.Column(db.Date, nullable=True)

    # Dashboard Widget
    show_on_dashboard = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('period_settings', uselist=False))

    def __repr__(self):
        return f'<PeriodSettings user_id={self.user_id} enabled={self.period_tracking_enabled}>'


# ============================================================================
# CHALLENGE SYSTEM MODELS
# ============================================================================

class Challenge(db.Model):
    """
    Model for community challenges where users compete or collaborate.
    Premium users can create challenges, free users can join.
    """
    __tablename__ = 'challenge'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Creator (must be premium)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Challenge Details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    icon = db.Column(db.String(10), default='🎯', nullable=False)  # Emoji icon

    # Challenge Type & Goals
    challenge_type = db.Column(db.String(20), nullable=False)  # 'competitive' or 'collaborative'
    goal_type = db.Column(db.String(30), nullable=False)  # 'streak', 'total_completions', 'participation_rate'
    goal_target = db.Column(db.Integer, nullable=True)  # Nullable for ongoing challenges

    # Status & Visibility
    status = db.Column(db.String(20), default='active', nullable=False, index=True)  # 'active', 'paused', 'archived'
    visibility = db.Column(db.String(20), default='invite_only', nullable=False)  # 'invite_only', future: 'public'

    # Participant Management
    allow_invites = db.Column(db.Boolean, default=True, nullable=False)
    max_participants = db.Column(db.Integer, nullable=True)  # Nullable for unlimited

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete

    # Relationships
    creator = db.relationship('User', backref=db.backref('created_challenges', lazy='dynamic'))
    participants = db.relationship('ChallengeParticipant', backref='challenge', lazy='dynamic', cascade='all, delete-orphan')
    invites = db.relationship('ChallengeInvite', backref='challenge', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('ChallengeActivity', backref='challenge', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Challenge id={self.id} name="{self.name}" type={self.challenge_type}>'


class ChallengeParticipant(db.Model):
    """
    Links users to challenges they've joined.
    Stores cached progress statistics for leaderboard performance.
    """
    __tablename__ = 'challenge_participant'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Participation Status
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'left', 'removed'
    role = db.Column(db.String(20), default='member', nullable=False)  # 'creator', 'member'

    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    left_at = db.Column(db.DateTime, nullable=True)

    # Cached Progress Statistics (updated when habits are completed)
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)
    total_completions = db.Column(db.Integer, default=0, nullable=False)
    last_activity = db.Column(db.Date, nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('challenge_participations', lazy='dynamic'))
    habit_links = db.relationship('HabitChallengeLink', backref='participant', lazy='dynamic', cascade='all, delete-orphan')

    # Unique Constraint: One participation per user per challenge
    __table_args__ = (
        db.UniqueConstraint('challenge_id', 'user_id', name='unique_challenge_user'),
    )

    def update_progress(self):
        """
        Recalculate progress statistics from all linked habits.
        Called after habit completion or when habits are linked/unlinked.
        """
        from sqlalchemy import func

        # Get all active habit links for this participant
        active_links = self.habit_links.filter_by(is_active=True).all()

        if not active_links:
            # No linked habits - reset to zero
            self.current_streak = 0
            self.longest_streak = 0
            self.total_completions = 0
            self.last_activity = None
            return

        # Aggregate stats from all linked habits
        total_current_streak = 0
        total_longest_streak = 0
        total_completions = 0
        most_recent_activity = None

        for link in active_links:
            habit = link.habit
            total_current_streak += habit.streak_count
            total_longest_streak += habit.longest_streak

            # Count total completions for this habit
            completion_count = habit.completions.count()
            total_completions += completion_count

            # Track most recent activity
            if habit.last_completed:
                if most_recent_activity is None or habit.last_completed > most_recent_activity:
                    most_recent_activity = habit.last_completed

        # Update cached statistics
        self.current_streak = total_current_streak
        self.longest_streak = total_longest_streak
        self.total_completions = total_completions
        self.last_activity = most_recent_activity

    def __repr__(self):
        return f'<ChallengeParticipant challenge_id={self.challenge_id} user_id={self.user_id} role={self.role}>'


class ChallengeInvite(db.Model):
    """
    Token-based invitations to challenges.
    Supports both email invites (30 days) and shareable links (90 days).
    """
    __tablename__ = 'challenge_invite'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False, index=True)
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Invite Details
    invitee_email = db.Column(db.String(120), nullable=True)  # Nullable for shareable links
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)  # URL-safe token

    # Status & Metadata
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # 'pending', 'accepted', 'rejected', 'expired'
    personal_message = db.Column(db.String(500), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    accepted_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    inviter = db.relationship('User', foreign_keys=[inviter_id], backref=db.backref('sent_invites', lazy='dynamic'))
    accepted_by = db.relationship('User', foreign_keys=[accepted_by_user_id], backref=db.backref('accepted_invites', lazy='dynamic'))

    @staticmethod
    def generate_token():
        """Generate a secure 64-character URL-safe token."""
        return secrets.token_urlsafe(32)  # 32 bytes = 64 characters in base64

    def is_expired(self):
        """Check if invite has expired."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<ChallengeInvite challenge_id={self.challenge_id} status={self.status} email={self.invitee_email}>'


class HabitChallengeLink(db.Model):
    """
    Links a user's habit to a challenge they're participating in.
    Allows participants to track challenge progress with their own habits.
    """
    __tablename__ = 'habit_challenge_link'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False, index=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('challenge_participant.id'), nullable=False, index=True)

    # Link Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    linked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    unlinked_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    habit = db.relationship('Habit', backref=db.backref('challenge_links', lazy='dynamic', cascade='all, delete-orphan'))

    # Unique Constraint: One link per habit per challenge
    __table_args__ = (
        db.UniqueConstraint('habit_id', 'challenge_id', name='unique_habit_challenge'),
    )

    def __repr__(self):
        return f'<HabitChallengeLink habit_id={self.habit_id} challenge_id={self.challenge_id} active={self.is_active}>'


class ChallengeActivity(db.Model):
    """
    Activity feed/timeline for challenges.
    Tracks events like user joins, milestones reached, etc.
    """
    __tablename__ = 'challenge_activity'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for system events

    # Activity Details
    activity_type = db.Column(db.String(50), nullable=False, index=True)  # 'challenge_created', 'user_joined', 'milestone_reached', etc.
    description = db.Column(db.String(500), nullable=False)
    activity_metadata = db.Column(db.JSON, nullable=True)  # Additional event data (renamed from 'metadata' to avoid SQLAlchemy reserved word)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('challenge_activities', lazy='dynamic'))

    def __repr__(self):
        return f'<ChallengeActivity challenge_id={self.challenge_id} type={self.activity_type}>'


class Badge(db.Model):
    """
    Badge definitions for gamification system.
    Badges are earned when users achieve specific milestones.
    """
    __tablename__ = 'badge'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Badge Details
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)  # URL-safe identifier
    description = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(10), nullable=False)  # Emoji icon
    color = db.Column(db.String(20), default='purple', nullable=False)  # Badge color theme
    
    # Achievement Requirements
    category = db.Column(db.String(50), nullable=False, index=True)  # 'streak', 'completion', 'habit_count', 'challenge', 'special'
    requirement_type = db.Column(db.String(50), nullable=False)  # 'streak_days', 'total_completions', 'habits_created', etc.
    requirement_value = db.Column(db.Integer, nullable=False)  # Threshold value
    
    # Display Order & Rarity
    display_order = db.Column(db.Integer, default=0, nullable=False)
    rarity = db.Column(db.String(20), default='common', nullable=False)  # 'common', 'rare', 'epic', 'legendary'
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_badges = db.relationship('UserBadge', back_populates='badge', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Badge {self.name} ({self.slug})>'


class UserBadge(db.Model):
    """
    Junction table tracking which badges users have earned.
    Stores when badges were earned.
    """
    __tablename__ = 'user_badge'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False, index=True)

    # Tracking
    earned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notification_seen = db.Column(db.Boolean, default=False, nullable=False)  # Track if user has seen badge notification
    
    # Context (what triggered the badge)
    trigger_context = db.Column(db.JSON, nullable=True)  # Store context like habit_id, streak_value, etc.

    # Unique constraint: user can only earn each badge once
    __table_args__ = (
        db.UniqueConstraint('user_id', 'badge_id', name='unique_user_badge'),
    )

    # Relationships
    user = db.relationship('User', backref=db.backref('earned_badges', lazy='dynamic'))
    badge = db.relationship('Badge', back_populates='user_badges')

    def __repr__(self):
        return f'<UserBadge user_id={self.user_id} badge_id={self.badge_id}>'
