from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from datetime import timedelta
from flask import jsonify

app = Flask(__name__)

# Secret key for sessions (change this in production!)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///habits.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
from models import db
db.init_app(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for session management."""
    from models import User
    return User.query.get(int(user_id))

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

if __name__ == '__main__':
    # Run the app - accessible on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/api/chart-data')
@login_required
def chart_data():
    """API endpoint for dashboard chart data"""
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