import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super_clave_secreta_desarrollo")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Config
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60) # Increased to 60m for better UX
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers', 'cookies'] # Allow both for flexibility
    JWT_COOKIE_SECURE = False # Set to True in production
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_COOKIE_CSRF_PROTECT = False # Disable CSRF for simplicity in this dev stage

    
    # Custom Configs
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    API_PERU_DEV_TOKEN = os.getenv('API_PERU_DEV_TOKEN')
    
    # Legacy/Other configs
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST'),
        'user': os.getenv('MYSQL_USER'),
        'password': os.getenv('MYSQL_PASSWORD'),
        'database': os.getenv('MYSQL_DB'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'cursorclass': 'DictCursor'
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///dev.db')
    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    JWT_COOKIE_SECURE = True
    
    # Optimizations for Supabase/Railway
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 2,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 30
    }

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
