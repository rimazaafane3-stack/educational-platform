import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'نجوم-التعلم-2024-سرية'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    WTF_CSRF_ENABLED = True

    @staticmethod
    def get_db_url():
        # Railway / production PostgreSQL
        db_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PRIVATE_URL')
        if db_url and db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url or 'sqlite:///' + os.path.join(BASE_DIR, 'platform.db')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.get_db_url()

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = Config.get_db_url()

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig
}
