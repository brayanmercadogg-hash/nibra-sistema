import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nibra-erp-secret-key-change-in-production')
    DATABASE = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'nibra.db'))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'img', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
