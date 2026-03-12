import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://valita_user:supersecret@db:5432/chocolates_valita')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', '')
    MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY', '')
    MP_WEBHOOK_SECRET = os.environ.get('MP_WEBHOOK_SECRET', '')
    
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost')
    
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@chocolatesvalita.cl')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin1234!')
