import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://valita_user:supersecret@db:5432/chocolates_valita')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', '')
    MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY', '')
    
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost')
    
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@carolchocolates.cl')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin1234!')
