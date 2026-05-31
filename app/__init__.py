from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config

db       = SQLAlchemy()
migrate  = Migrate()
login_manager = LoginManager()
csrf     = CSRFProtect()

login_manager.login_view     = 'auth.login'
login_manager.login_message  = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    app = Flask(__name__, template_folder='../templates',
                static_folder='static')
    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.auth   import auth   as auth_bp
    from app.admin  import admin  as admin_bp
    from app.student import student as student_bp

    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(admin_bp,   url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/')

    # Context processors
    @app.context_processor
    def inject_globals():
        from app.models import Subject
        subjects = Subject.query.filter_by(is_active=True).order_by(Subject.order).all()
        return dict(nav_subjects=subjects)

    return app
