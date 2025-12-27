"""
Configuration settings for different environments
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///habits.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'

    # Stripe configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Stripe Price IDs
    STRIPE_PRICE_ID_MONTHLY = os.environ.get('STRIPE_PRICE_ID_MONTHLY')
    STRIPE_PRICE_ID_ANNUAL = os.environ.get('STRIPE_PRICE_ID_ANNUAL')
    STRIPE_PRICE_ID_LIFETIME = os.environ.get('STRIPE_PRICE_ID_LIFETIME')

    # Email configuration (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@habitflow.app')
    MAIL_MAX_EMAILS = int(os.environ.get('MAIL_MAX_EMAILS', '100'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration - use in deployment"""
    DEBUG = False
    TESTING = False

    # SECRET_KEY must be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Warn if SECRET_KEY is not properly set (but don't crash)
    if not SECRET_KEY:
        print("WARNING: SECRET_KEY not set in environment variables!")
        print("WARNING: Using fallback key - THIS IS INSECURE!")
        SECRET_KEY = 'insecure-fallback-key-change-this-immediately'
    elif len(SECRET_KEY) < 32:
        print(f"WARNING: SECRET_KEY is too short ({len(SECRET_KEY)} chars, need 32+)")
        print("WARNING: This may cause security issues!")

    # Session security (HTTPS only)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Session timeout (1 hour for production)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    # PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Validate DATABASE_URL is set
    # Note: Commented out to allow imports in development
    # if not SQLALCHEMY_DATABASE_URI:
    #     print("ERROR: DATABASE_URL not set in environment variables!")
    #     raise ValueError("DATABASE_URL must be set in environment variables for production")

    # Fix for Heroku postgres:// -> postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    # Validate Stripe keys in production
    if not Config.STRIPE_SECRET_KEY or not Config.STRIPE_PUBLISHABLE_KEY:
        print("WARNING: Stripe keys not configured. Payment features will be disabled.")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
