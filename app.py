from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager

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

@app.route('/')
def home():
    """Home page"""
    return render_template('home.html')

if __name__ == '__main__':
    # Run the app - accessible on all network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)
    