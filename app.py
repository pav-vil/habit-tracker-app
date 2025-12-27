from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager, login_required, current_user
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import config
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Load configuration from config.py based on FLASK_ENV
env = os.environ.get('FLASK_ENV', 'development')
print(f"[INIT] Loading configuration for environment: {env}")

try:
    app.config.from_object(config[env])
    print(f"[INIT] Configuration loaded successfully")
    print(f"[INIT] DEBUG mode: {app.config.get('DEBUG')}")
    print(f"[INIT] SECRET_KEY length: {len(app.config.get('SECRET_KEY', ''))}")
except Exception as e:
    print(f"[INIT] ERROR loading configuration: {e}")
    raise

# Handle proxy headers for HTTPS on Render/Heroku
# This allows SESSION_COOKIE_SECURE to work properly
if env == 'production':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    print("[INIT] ProxyFix middleware enabled for production")

# Initialize SQLAlchemy with the app
from models import db
db.init_app(app)

# Create database tables if they don't exist (MUST run first!)
try:
    with app.app_context():
        print(f"[INIT] Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI'][:30]}...")
        db.create_all()
        print("[INIT] Database tables created/verified successfully")
except Exception as e:
    print(f"[INIT] ERROR creating database tables: {e}")
    if env == 'production':
        raise  # Fail fast in production

# Auto-migrate database on startup (adds missing columns safely)
# This runs AFTER tables are created
from auto_migrate import auto_migrate_database
try:
    auto_migrate_database(app, db)
except Exception as e:
    print(f"[INIT] WARNING: Auto-migration failed: {e}")
    # Don't crash the app if migration fails

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for session management."""
    from models import User
    return db.session.get(User, int(user_id))

# CSRF Protection Setup
csrf = CSRFProtect(app)

# Email Setup (Flask-Mail)
from flask_mail import Mail
mail = Mail(app)
print(f"[INIT] OK Flask-Mail initialized (server: {app.config.get('MAIL_SERVER')})")

# Rate Limiting Setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
)

# Register Blueprints
from auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
from habits import habits_bp
app.register_blueprint(habits_bp, url_prefix='/habits')

# Import and register stats blueprint
from stats import stats_bp
app.register_blueprint(stats_bp)

# Import and register profile blueprint
from profile import profile_bp
app.register_blueprint(profile_bp)

# Import and register subscription blueprint
from subscription import subscription_bp
app.register_blueprint(subscription_bp, url_prefix='/subscription')

# Import and register payments blueprint
from payments import payments_bp
app.register_blueprint(payments_bp)

# Import and register webhooks blueprint
from webhooks import webhooks_bp
app.register_blueprint(webhooks_bp, url_prefix='/webhooks')

# Exempt webhooks from CSRF protection
csrf.exempt(webhooks_bp)

@app.route('/')
def home():
    """Home page"""
    return render_template('home.html')

# Apply rate limiting to login endpoint (5 attempts per minute)
app.view_functions['auth.login'] = limiter.limit("5 per minute")(app.view_functions['auth.login'])

if __name__ == '__main__':
    # Run the app - accessible on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/api/chart-data')
@login_required
def chart_data():
    """API endpoint for dashboard chart data"""
    from models import Habit
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    user_date = current_user.get_user_date()

    # Last 7 days labels
    dates = [(user_date - timedelta(days=i)).strftime('%m/%d') for i in range(6, -1, -1)]

    # Count completions per day
    completions_per_day = []
    for i in range(6, -1, -1):
        check_date = user_date - timedelta(days=i)
        count = sum(1 for h in habits if h.last_completed == check_date)
        completions_per_day.append(count)

    # Active vs inactive habits
    active_count = sum(1 for h in habits if h.streak_count > 0)
    inactive_count = len(habits) - active_count

    return jsonify({
        'dates': dates,
        'completions': completions_per_day,
        'active': active_count,
        'inactive': inactive_count
    })

@app.route('/api/30-day-completions')
@login_required
def thirty_day_completions():
    """
    API endpoint for 30-day completion trend data.
    Returns total habits completed per day for the last 30 days.
    """
    from models import Habit, CompletionLog
    from datetime import datetime, timedelta

    user_date = current_user.get_user_date()

    # Generate labels for last 30 days (oldest to newest)
    labels = []
    completions = []

    for i in range(29, -1, -1):  # 29 days ago to today
        check_date = user_date - timedelta(days=i)

        # Format label - show month/day for readability
        label = check_date.strftime('%m/%d')
        labels.append(label)

        # Count how many habits were completed on this day
        # Query CompletionLog for this user's habits on this date
        count = CompletionLog.query.join(Habit).filter(
            Habit.user_id == current_user.id,
            CompletionLog.completed_at == check_date
        ).count()

        completions.append(count)

    return jsonify({
        'labels': labels,
        'completions': completions
    })