from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager, login_required, current_user
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from config import config

app = Flask(__name__)

# Load configuration from config.py based on FLASK_ENV
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize SQLAlchemy with the app
from models import db
db.init_app(app)

# Create database tables if they don't exist (MUST run first!)
with app.app_context():
    db.create_all()

# Auto-migrate database on startup (adds missing columns safely)
# This runs AFTER tables are created
from auto_migrate import auto_migrate_database
auto_migrate_database(app, db)

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