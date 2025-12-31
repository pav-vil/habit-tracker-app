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

    # Stripe Payment Configuration (Phase 3)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # Stripe Price IDs (set these after creating products in Stripe Dashboard)
    STRIPE_PRICE_ID_MONTHLY = os.environ.get('STRIPE_PRICE_ID_MONTHLY')
    STRIPE_PRICE_ID_ANNUAL = os.environ.get('STRIPE_PRICE_ID_ANNUAL')
    STRIPE_PRICE_ID_LIFETIME = os.environ.get('STRIPE_PRICE_ID_LIFETIME')

    # App URL (for payment redirects)
    APP_URL = os.environ.get('APP_URL') or 'http://localhost:5000'

    # PayPal Configuration (Phase 5)
    PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    PAYPAL_WEBHOOK_ID = os.environ.get('PAYPAL_WEBHOOK_ID')  # For webhook signature verification

    # PayPal Plan IDs (set these after creating subscription plans in PayPal Dashboard)
    PAYPAL_PLAN_ID_MONTHLY = os.environ.get('PAYPAL_PLAN_ID_MONTHLY')
    PAYPAL_PLAN_ID_ANNUAL = os.environ.get('PAYPAL_PLAN_ID_ANNUAL')

    # Coinbase Commerce Configuration (Phase 6)
    COINBASE_COMMERCE_API_KEY = os.environ.get('COINBASE_COMMERCE_API_KEY')
    COINBASE_COMMERCE_WEBHOOK_SECRET = os.environ.get('COINBASE_COMMERCE_WEBHOOK_SECRET')

    # Coinbase Commerce Pricing
    COINBASE_LIFETIME_PRICE = float(os.environ.get('COINBASE_LIFETIME_PRICE', '59.99'))

    # TiloPay Configuration (Costa Rica Local Gateway)
    TILOPAY_MODE = os.environ.get('TILOPAY_MODE', 'test')  # 'test' or 'production'
    TILOPAY_API_KEY = os.environ.get('TILOPAY_API_KEY')  # Integration key from TiloPay portal
    TILOPAY_API_USER = os.environ.get('TILOPAY_API_USER')  # API username
    TILOPAY_API_PASSWORD = os.environ.get('TILOPAY_API_PASSWORD')  # API password
    TILOPAY_WEBHOOK_SECRET = os.environ.get('TILOPAY_WEBHOOK_SECRET')  # Webhook verification secret

    # TiloPay Test Credentials (for development)
    TILOPAY_TEST_API_KEY = '6609-5850-8330-8034-3464'
    TILOPAY_TEST_API_USER = 'lSrT45'
    TILOPAY_TEST_API_PASSWORD = 'Zlb8H9'

    # TiloPay API URLs
    TILOPAY_API_URL_TEST = 'https://test.tilopay.com/api/v1'  # Test environment
    TILOPAY_API_URL_PRODUCTION = 'https://api.tilopay.com/api/v1'  # Production environment

    # Currency Configuration
    SUPPORTED_CURRENCIES = ['USD', 'CRC']
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'USD')

    # Exchange Rate (USD to CRC) - Update periodically
    # As of Dec 2025: 1 USD = ~497 CRC
    USD_TO_CRC_RATE = float(os.environ.get('USD_TO_CRC_RATE', '500'))

    # Pricing in different currencies
    PRICING = {
        'USD': {
            'monthly': 2.99,
            'annual': 19.99,
            'lifetime': 59.99
        },
        'CRC': {
            'monthly': 1500,    # Rounded from ~1,485 CRC
            'annual': 10000,    # Rounded from ~9,995 CRC
            'lifetime': 30000   # Rounded from ~29,995 CRC
        }
    }

    # Currency display formats
    CURRENCY_SYMBOLS = {
        'USD': '$',
        'CRC': '₡'
    }

    # Email Configuration (Flask-Mail - Phase 5)
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

    # Session security (HTTPS only)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Session timeout (1 hour for production)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    def __init__(self):
        """Initialize production config and validate environment variables"""
        # SECRET_KEY must be set via environment variable
        secret_key = os.environ.get('SECRET_KEY')

        # Warn if SECRET_KEY is not properly set (but don't crash)
        if not secret_key:
            print("⚠️  WARNING: SECRET_KEY not set in environment variables!")
            print("⚠️  Using fallback key - THIS IS INSECURE!")
            self.SECRET_KEY = 'insecure-fallback-key-change-this-immediately'
        elif len(secret_key) < 32:
            print(f"⚠️  WARNING: SECRET_KEY is too short ({len(secret_key)} chars, need 32+)")
            print("⚠️  This may cause security issues!")
            self.SECRET_KEY = secret_key
        else:
            self.SECRET_KEY = secret_key

        # PostgreSQL for production
        database_url = os.environ.get('DATABASE_URL')

        # Validate DATABASE_URL is set
        if not database_url:
            print("❌ ERROR: DATABASE_URL not set in environment variables!")
            raise ValueError("DATABASE_URL must be set in environment variables for production")

        # Fix for Heroku postgres:// -> postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        self.SQLALCHEMY_DATABASE_URI = database_url

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
