import os
import secrets as secrets_module
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Universal dastur konfiguratsiyasi"""

    # Environment detection
    ENVIRONMENT = os.environ.get("FLASK_ENV", "production")
    IS_DEVELOPMENT = ENVIRONMENT == "development"
    IS_PRODUCTION = ENVIRONMENT == "production"

    # Database configuration
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///database.sqlite3")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLite-specific engine options
    if DATABASE_URL.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"check_same_thread": False, "timeout": 60}
        }
    else:
        # PostgreSQL options (if using PostgreSQL)
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        }

    # Security configuration
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets_module.token_urlsafe(32))
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 7200
    WTF_CSRF_ENABLED = True

    # File upload configuration
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # JSON configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = IS_DEVELOPMENT

    # Cache configuration
    SEND_FILE_MAX_AGE_DEFAULT = 31536000 if IS_PRODUCTION else 300
    REDIS_URL = os.environ.get("REDIS_URL", "memory://")

    # External APIs
    YANDEX_GEOCODER_API = os.environ.get("YANDEX_GEOCODER_API", "")
    # Deprecated: GOOGLE_MAPS_API is intentionally ignored to prefer Yandex maps.
    # If present in environment, do not expose or inject into templates to avoid
    # accidentally placing the literal 'None' into script src attributes.
    GOOGLE_MAPS_API = ""
    SERPER_API_KEY = os.environ.get(
        "SERPER_API_KEY", "1b077296f67499a12ee28ce232bb48221d29be14"
    )

    # Localization
    DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "uz")
    SUPPORTED_LANGUAGES = ["uz", "ru", "en", "tr", "ar"]
    DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY", "UZS")
    TIMEZONE = os.environ.get("TIMEZONE", "Asia/Tashkent")

    # Business logic
    AVG_PREP_MINUTES = int(os.environ.get("AVG_PREP_MINUTES", "7"))
    DELIVERY_BASE_PRICE = int(os.environ.get("DELIVERY_BASE_PRICE", "10000"))
    COURIER_BASE_RATE = int(os.environ.get("COURIER_BASE_RATE", "8000"))
    CASHBACK_PERCENTAGE = float(os.environ.get("CASHBACK_PERCENTAGE", "1.0"))
    MAX_DELIVERY_DISTANCE = float(os.environ.get("MAX_DELIVERY_DISTANCE", "50.0"))

    # Rate limiting
    RATE_LIMIT_DAILY = int(os.environ.get("RATE_LIMIT_DAILY", "1000"))
    RATE_LIMIT_HOURLY = int(os.environ.get("RATE_LIMIT_HOURLY", "200"))
    RATE_LIMIT_MINUTE = int(os.environ.get("RATE_LIMIT_MINUTE", "50"))

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE_MAX_SIZE = int(os.environ.get("LOG_FILE_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5"))

    # Performance
    THREAD_POOL_MAX_WORKERS = int(os.environ.get("THREAD_POOL_MAX_WORKERS", "10"))
    DB_POOL_MAX_CONNECTIONS = int(os.environ.get("DB_POOL_MAX_CONNECTIONS", "20"))

    # Admin credentials
    SUPER_ADMIN_USERNAME = os.environ.get("SUPER_ADMIN_USERNAME", "masteradmin")
    SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "sjtmsimram10")