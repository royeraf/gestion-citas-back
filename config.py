import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super_clave_secreta_desarrollo")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Config
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # IMPORTANTE: Para usar cookies HttpOnly
    JWT_TOKEN_LOCATION = ['cookies'] 
    
    # Configuración de Cookies Dinámica
    def _get_env_bool(name, default):
        val = os.getenv(name, str(default)).strip().strip('"').strip("'").lower()
        return val == 'true'

    def _get_env_str(name, default):
        return os.getenv(name, default).strip().strip('"').strip("'")

    JWT_COOKIE_SECURE = _get_env_bool('JWT_COOKIE_SECURE', False)
    _samesite = _get_env_str('JWT_COOKIE_SAMESITE', 'Lax')
    
    # Manejar caso especial "None" (requerido para cross-domain en HTTPS)
    if _samesite.lower() == 'none':
        JWT_COOKIE_SAMESITE = 'None'
        JWT_COOKIE_SECURE = True # Los navegadores obligan a Secure=True si SameSite=None
    else:
        JWT_COOKIE_SAMESITE = _samesite

    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    JWT_COOKIE_CSRF_PROTECT = False # Desactivar CSRF para simplificar desarrollo
    JWT_ACCESS_CSRF_COOKIE_NAME = "csrf_access_token"
    JWT_REFRESH_CSRF_COOKIE_NAME = "csrf_refresh_token"
    
    # Configuración de CORS para cookies
    CORS_SUPPORTS_CREDENTIALS = True

    
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
