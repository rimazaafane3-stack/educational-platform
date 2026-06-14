import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_db_url():
    url = (os.environ.get('DATABASE_URL') or
           os.environ.get('DATABASE_PRIVATE_URL') or
           'sqlite:///' + os.path.join(BASE_DIR, 'platform.db'))
    # Railway/Heroku returns postgres:// — SQLAlchemy needs postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    # ── Security ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    WTF_CSRF_ENABLED      = True
    WTF_CSRF_TIME_LIMIT   = None   # No expiry — fixes Bad Request on Railway
    WTF_CSRF_SSL_STRICT   = False  # Allow HTTP + HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 * 7   # 7 days

    # ── Database ──────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI        = get_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS      = {
        'pool_pre_ping': True,
        'pool_recycle':  300,
    }

    # ── Upload ────────────────────────────────────────────────
    UPLOAD_FOLDER      = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Force HTTPS in production
    PREFERRED_URL_SCHEME = 'https'


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
