import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config

db            = SQLAlchemy()
migrate       = Migrate()
login_manager = LoginManager()
csrf          = CSRFProtect()

login_manager.login_view             = 'auth.login'
login_manager.login_message          = 'يرجى تسجيل الدخول'
login_manager.login_message_category = 'warning'


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__,
                template_folder='../templates',
                static_folder='static')
    app.config.from_object(config[config_name])

    # ── Extensions ────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── Security headers (production only) ───────────────────
    if config_name == 'production' or os.environ.get('FLASK_ENV') == 'production':
        try:
            from flask_talisman import Talisman
            Talisman(app,
                     force_https=True,
                     strict_transport_security=True,
                     session_cookie_secure=True,
                     content_security_policy={
                         'default-src': ["'self'", 'https:'],
                         'script-src':  ["'self'", "'unsafe-inline'",
                                         'https://cdnjs.cloudflare.com',
                                         'https://cdn.quilljs.com',
                                         'https://fonts.googleapis.com'],
                         'style-src':   ["'self'", "'unsafe-inline'",
                                         'https://cdnjs.cloudflare.com',
                                         'https://cdn.quilljs.com',
                                         'https://fonts.googleapis.com'],
                         'font-src':    ["'self'", 'https://fonts.gstatic.com',
                                         'https://cdnjs.cloudflare.com'],
                         'img-src':     ["'self'", 'data:', 'https:'],
                         'frame-src':   ['https://www.youtube.com'],
                     })
        except ImportError:
            pass

    # ── Rate limiting ─────────────────────────────────────────
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=['200 per day', '50 per hour'],
            storage_uri=os.environ.get('REDIS_URL', 'memory://'),
        )
        # Stricter limit on login
        from app.auth import auth as auth_bp_ref
        # Applied in auth routes
        app.limiter = limiter
    except Exception:
        app.limiter = None

    # ── Blueprints ────────────────────────────────────────────
    from app.auth    import auth    as auth_bp
    from app.admin   import admin   as admin_bp
    from app.student import student as student_bp

    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(admin_bp,   url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/')

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def rate_limit(e):
        return render_template('errors/429.html'), 429

    # ── Context processors ────────────────────────────────────
    @app.context_processor
    def inject_globals():
        from app.models import Subject
        subjects = Subject.query.filter_by(is_active=True).order_by(Subject.order).all()
        return dict(nav_subjects=subjects)

    # ── Ensure upload folder exists ───────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app
