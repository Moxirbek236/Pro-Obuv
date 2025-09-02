
"""
Universal Restaurant System Configuration
Bu modul barcha konfiguratsiya sozlamalarini boshqaradi
"""

import os
import secrets
from dotenv import load_dotenv

# Environment variables yuklash
load_dotenv()

class BaseConfig:
    """Asosiy konfiguratsiya sinfi"""
    
    # Environment
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
    IS_DEVELOPMENT = ENVIRONMENT == 'development'
    IS_PRODUCTION = ENVIRONMENT == 'production'
    
    # Flask asosiy sozlamalari
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///restaurant.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7200
    WTF_CSRF_ENABLED = True
    
    # File upload
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # Localization
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'uz')
    SUPPORTED_LANGUAGES = ['uz', 'ru', 'en', 'tr', 'ar', 'fa']
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'UZS')
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Tashkent')
    
    # Business logic
    AVG_PREP_MINUTES = int(os.environ.get("AVG_PREP_MINUTES", "7"))
    DELIVERY_BASE_PRICE = int(os.environ.get("DELIVERY_BASE_PRICE", "10000"))
    COURIER_BASE_RATE = int(os.environ.get("COURIER_BASE_RATE", "8000"))
    CASHBACK_PERCENTAGE = float(os.environ.get("CASHBACK_PERCENTAGE", "1.0"))
    MAX_DELIVERY_DISTANCE = float(os.environ.get("MAX_DELIVERY_DISTANCE", "50.0"))
    MIN_ORDER_AMOUNT = int(os.environ.get("MIN_ORDER_AMOUNT", "20000"))
    
    # External APIs
    YANDEX_GEOCODER_API = os.environ.get('YANDEX_GEOCODER_API', '')
    GOOGLE_MAPS_API = os.environ.get('GOOGLE_MAPS_API', '')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '1b077296f67499a12ee28ce232bb48221d29be14')
    
    # Admin credentials
    SUPER_ADMIN_USERNAME = os.environ.get('SUPER_ADMIN_USERNAME', 'masteradmin')
    SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'SuperAdmin2025!@#$%')
    
    # Performance settings
    THREAD_POOL_MAX_WORKERS = int(os.environ.get('THREAD_POOL_MAX_WORKERS', '10'))
    DB_POOL_MAX_CONNECTIONS = int(os.environ.get('DB_POOL_MAX_CONNECTIONS', '20'))
    
    # Rate limiting
    RATE_LIMIT_DAILY = int(os.environ.get("RATE_LIMIT_DAILY", "1000"))
    RATE_LIMIT_HOURLY = int(os.environ.get("RATE_LIMIT_HOURLY", "200"))
    RATE_LIMIT_MINUTE = int(os.environ.get("RATE_LIMIT_MINUTE", "50"))
    
    # Cache settings
    REDIS_URL = os.environ.get('REDIS_URL', 'memory://')
    CACHE_DEFAULT_TTL = int(os.environ.get('CACHE_DEFAULT_TTL', '300'))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE_MAX_SIZE = int(os.environ.get('LOG_FILE_MAX_SIZE', '10485760'))
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '5'))

class DevelopmentConfig(BaseConfig):
    """Development muhiti uchun konfiguratsiya"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
    JSONIFY_PRETTYPRINT_REGULAR = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(BaseConfig):
    """Production muhiti uchun konfiguratsiya"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = 'WARNING'
    
class TestingConfig(BaseConfig):
    """Testing muhiti uchun konfiguratsiya"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration selector
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config():
    """Muhit bo'yicha konfiguratsiyani qaytarish"""
    env = os.environ.get('FLASK_ENV', 'production')
    return config_map.get(env, ProductionConfig)

# Apply universal configuration
app.config.from_object(get_config())</old_str>
