import time
import string
import secrets as secrets_module
import secrets
import hashlib
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.profiler import ProfilerMiddleware
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import threading  # <-- added import for fallback threading
import sys  # Import sys to check sys.modules
import csv
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import pytz
from contextlib import contextmanager
from functools import wraps

import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    get_flashed_messages,
    jsonify,
    g,
    send_file,
    make_response,
)
from flask_cors import CORS
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from datetime import timedelta
import sqlite3
import json
import pandas as pd

try:
    import requests
except Exception:
    requests = None

try:
    import qrcode
except Exception:
    qrcode = None

try:
    import base64
except Exception:
    base64 = None

from io import BytesIO

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

try:
    from flask_sqlalchemy import SQLAlchemy
except Exception:
    SQLAlchemy = None

try:
    from werkzeug.utils import secure_filename
except Exception:

    def secure_filename(name):
        return os.path.basename(name)


import uuid as uuid_module

uuid = uuid_module

start_time = time.time()

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

load_dotenv()
print("DEBUG: load_dotenv done")

import time
from functools import wraps

MEMORY_CACHE = {}
CACHE_TIMEOUT = 300  # 5 минут


def simple_cache(timeout=300):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            current_time = time.time()

            if cache_key in MEMORY_CACHE:
                cached_time, cached_result = MEMORY_CACHE[cache_key]
                if current_time - cached_time < timeout:
                    return cached_result

            result = func(*args, **kwargs)
            MEMORY_CACHE[cache_key] = (current_time, result)

            if len(MEMORY_CACHE) % 100 == 0:
                cutoff = current_time - timeout * 2
                MEMORY_CACHE.clear()  # Простое очищение

            return result

        return wrapper

    return decorator


def export_orders_report(period="day"):
    """
    period: 'day', 'month', 'year'
    Buyurtmalar hisobotini Excel faylga eksport qiladi
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    now = datetime.datetime.now()
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("Period must be day, month, or year")
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")
    query = "SELECT * FROM orders WHERE created_at >= ? ORDER BY created_at DESC"
    cur.execute(query, (start_str,))
    rows = cur.fetchall()
    df = pd.DataFrame([dict(row) for row in rows])
    filename = f"orders_report_{period}_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    df.to_excel(filepath, index=False)
    conn.close()
    return filepath


app = Flask(__name__)

print("DEBUG: Flask app created")

try:
    from api.news_api import register_news_api

    register_news_api(app)
    print("DEBUG: News API registered")
except ImportError as e:
    print(f"WARNING: News API import failed: {e}")
except Exception as e:
    print(f"WARNING: News API registration failed: {e}")


class Config:
    "Universal dastur konfiguratsiyasi"

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

    # Rate limiting - ВЫСОКАЯ ПРОИЗВОДИТЕЛЬНОСТЬ
    RATE_LIMIT_DAILY = int(os.environ.get("RATE_LIMIT_DAILY", "100000"))  # 100k в день
    RATE_LIMIT_HOURLY = int(os.environ.get("RATE_LIMIT_HOURLY", "10000"))  # 10k в час
    RATE_LIMIT_MINUTE = int(os.environ.get("RATE_LIMIT_MINUTE", "1000"))  # 1k в минуту

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE_MAX_SIZE = int(os.environ.get("LOG_FILE_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5"))

    # Performance - ОПТИМИЗИРОВАНО ДЛЯ 100+ ПОЛЬЗОВАТЕЛЕЙ
    THREAD_POOL_MAX_WORKERS = int(
        os.environ.get("THREAD_POOL_MAX_WORKERS", "200")
    )  # Больше потоков
    DB_POOL_MAX_CONNECTIONS = int(
        os.environ.get("DB_POOL_MAX_CONNECTIONS", "100")
    )  # Больше соединений

    # Дополнительные оптимизации производительности
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "check_same_thread": False,
            "timeout": 120,  # Увеличенный timeout
            "isolation_level": None,  # autocommit mode для скорости
        },
        "pool_timeout": 60,
        "pool_recycle": 7200,  # 2 часа
        "pool_pre_ping": True,
        "pool_size": 50,  # Большой пул соединений
        "max_overflow": 100,  # Много overflow соединений
        "echo": False,  # Без SQL логирования для производительности
    }

    # Admin credentials
    SUPER_ADMIN_USERNAME = os.environ.get("SUPER_ADMIN_USERNAME", "masteradmin")
    SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "sjtmsimram10")


# Apply configuration
app.config.from_object(Config)
# Ensure client-side Yandex Maps key is available in app.config.
# Some deployments set YANDEX_MAPS_API in a separate config file or .env;
# make sure the key is always present in app.config for templates.
try:
    app.config["YANDEX_MAPS_API"] = os.environ.get(
        "YANDEX_MAPS_API", app.config.get("YANDEX_MAPS_API", "")
    )
except Exception:
    # Non-fatal: leave existing config value if environment lookup fails
    pass

# Ensure GOOGLE_MAPS_API is not populated from environment to avoid accidental
# client-side injection of the string 'None' or similar.
try:
    app.config["GOOGLE_MAPS_API"] = ""
except Exception:
    pass

# Also ensure Jinja templates never see a GOOGLE_MAPS_API global value.
# This is defensive: many templates read config values via globals; make sure
# GOOGLE_MAPS_API is always an empty string so no Google script tag is rendered.
try:
    app.jinja_env.globals["GOOGLE_MAPS_API"] = ""
except Exception:
    pass

# Ensure Flask secret key and session lifetime use the Config values explicitly
try:
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(
        seconds=getattr(Config, "PERMANENT_SESSION_LIFETIME", 7200)
    )
    # Make sure cookie flags are set on the Flask app config
    app.config["SESSION_COOKIE_SECURE"] = bool(
        getattr(Config, "SESSION_COOKIE_SECURE", False)
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = bool(
        getattr(Config, "SESSION_COOKIE_HTTPONLY", True)
    )
    app.config["SESSION_COOKIE_SAMESITE"] = getattr(
        Config, "SESSION_COOKIE_SAMESITE", "Lax"
    )
except Exception:
    pass

# Professional middleware stack
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# CORS support
CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Compression
Compress(app)

# Rate limiting with universal configuration
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[
        f"{Config.RATE_LIMIT_DAILY} per day",
        f"{Config.RATE_LIMIT_HOURLY} per hour",
        f"{Config.RATE_LIMIT_MINUTE} per minute",
    ],
    storage_uri=Config.REDIS_URL,
)

# Performance profiling (faqat debug rejimida)
if os.environ.get("FLASK_ENV") == "development":
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

# Upload papkasini yaratish
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Logs papkasini yaratish
os.makedirs("logs", exist_ok=True)


# Handle requests that exceed MAX_CONTENT_LENGTH (return JSON)
@app.errorhandler(413)
def request_entity_too_large(e):
    app.logger.warning("Request entity too large")
    return (
        jsonify(
            {"success": False, "message": "File too large or request payload too big"}
        ),
        413,
    )


# Advanced logging konfiguratsiyasi - funksiyani oldinroq e'lon qilish
def setup_logging():
    "Professional logging setup with structured logging"
    # Detailed formatter
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    )

    # Simple formatter
    simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    try:
        # Rotating file handler (maksimal 10MB, 5 ta backup)
        file_handler = RotatingFileHandler(
            "logs/restaurant.log", maxBytes=10485760, backupCount=5
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.INFO)

        # Error file handler
        error_handler = RotatingFileHandler(
            "logs/errors.log", maxBytes=10485760, backupCount=5
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)

        # Console handler - faqat development uchun
        console_handler = logging.StreamHandler()
        if Config.IS_DEVELOPMENT:
            console_handler.setFormatter(simple_formatter)
            console_handler.setLevel(logging.INFO)
        else:
            console_handler.setFormatter(
                logging.Formatter("%(levelname)s: %(message)s")
            )
            console_handler.setLevel(logging.ERROR)

        # Root logger konfiguratsiya
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO if Config.IS_DEVELOPMENT else logging.WARNING)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)

        # Flask app logger
        app.logger.setLevel(logging.INFO if Config.IS_DEVELOPMENT else logging.ERROR)
        app.logger.addHandler(error_handler)

        # Werkzeug loglarni sozlash
        werkzeug_logger = logging.getLogger("werkzeug")
        werkzeug_logger.setLevel(logging.WARNING)

        return logging.getLogger("restaurant_app")

    except Exception as e:
        # Fallback logging agar setupException bo'lsa
        print(f"Logging setup failed: {e}")
        # Agar app_logger hali yaratilmagan bo'lsa
        if "app_logger" not in globals():
            return logging.getLogger("restaurant_app")
        else:
            app_logger.error(f"Logging setup failed: {e}")
            return logging.getLogger("restaurant_app")


# Logging ni sozlash
app_logger = setup_logging()

# Location service instance - avoid network calls during SKIP_DB_INIT
try:
    if not os.environ.get("SKIP_DB_INIT"):
        from location_service import LocationService

        try:
            location_service = LocationService()
            app_logger.info("Location service muvaffaqiyatli yuklandi")
        except Exception as e:
            app_logger.warning(f"Location service init failed: {str(e)}")
            location_service = None
    else:
        location_service = None
except (ImportError, Exception) as e:
    app_logger.warning(f"Location service yuklanmadi: {str(e)}")
    location_service = None

if location_service is None:

    class FallbackLocationService:
        def search_places(self, query):
            return {"places": [], "error": "Location service not available"}

    location_service = FallbackLocationService()


# Cache tizimi
class CacheManager:
    def __init__(self):
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.cache_lock = threading.Lock()
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        "Redis connection (agar mavjud bo'lsa)"
        try:
            # If redis is not installed or REDIS_URL indicates memory backend, skip trying to connect.
            if not REDIS_AVAILABLE:
                return

            redis_url = os.environ.get("REDIS_URL", "memory://")
            if not redis_url or redis_url.startswith("memory"):
                # Explicitly configured to use in-memory cache
                return

            # Attempt to create a client with a short connect timeout. Do not treat a failure as an error
            # that needs frequent logging; use INFO level so it's less noisy in typical deployments.
            try:
                # short connect timeout to avoid hanging processes when Redis is unreachable
                self.redis_client = redis.from_url(redis_url, socket_connect_timeout=2)
                # Try a quick ping; failures are expected if Redis isn't present and are handled silently.
                self.redis_client.ping()
                app_logger.info("Redis cache connected")
            except Exception as conn_err:
                # Keep it quiet: informational message and fall back to memory cache.
                app_logger.info(
                    f"Redis not available, falling back to in-memory cache: {str(conn_err)}"
                )
                self.redis_client = None
        except Exception as e:
            # As a last resort, do not spam warnings for Redis problems during normal operation.
            try:
                app_logger.info(f"Redis initialization skipped or failed: {str(e)}")
            except Exception:
                pass
            self.redis_client = None

    def get(self, key, default=None):
        "Cache dan ma'lumot olish"
        try:
            if self.redis_client:
                value = self.redis_client.get(f"restaurant:{key}")
                if value:
                    return json.loads(value.decode())

            # Memory cache dan olish
            with self.cache_lock:
                if key in self.memory_cache:
                    timestamp = self.cache_timestamps.get(key, 0)
                    if time.time() - timestamp < 300:  # 5 daqiqa
                        return self.memory_cache[key]
                    else:
                        del self.memory_cache[key]
                        del self.cache_timestamps[key]
        except Exception as e:
            app_logger.error(f"Cache get error: {str(e)}")

        return default

    def set(self, key, value, ttl=300):
        "Cache ga ma'lumot saqlash"
        try:
            if self.redis_client:
                self.redis_client.setex(
                    f"restaurant:{key}", ttl, json.dumps(value, default=str)
                )

            # Memory cache ga ham saqlash
            with self.cache_lock:
                self.memory_cache[key] = value
                self.cache_timestamps[key] = time.time()

                # Memory cache ni tozalash (maksimal 1000 ta element)
                if len(self.memory_cache) > 1000:
                    oldest_key = min(
                        self.cache_timestamps.keys(),
                        key=lambda k: self.cache_timestamps[k],
                    )
                    del self.memory_cache[oldest_key]
                    del self.cache_timestamps[oldest_key]
        except Exception as e:
            app_logger.error(f"Cache set error: {str(e)}")

    def delete(self, key):
        "Cache dan o'chirish"
        try:
            if self.redis_client:
                self.redis_client.delete(f"restaurant:{key}")

            with self.cache_lock:
                self.memory_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
        except Exception as e:
            app_logger.error(f"Cache delete error: {str(e)}")


# Global cache manager (lazy-init to avoid blocking imports)
cache_manager = None


def get_cache_manager():
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
        try:
            print("DEBUG: CacheManager initialized")
        except Exception:
            pass
    return cache_manager


# Ensure a global cache_manager instance exists so code that references
# `cache_manager` directly (older decorators/routes) doesn't hit None.
try:
    cache_manager = get_cache_manager()
except Exception as e:
    try:
        app_logger.warning(f"Cache manager initialization failed: {e}")
    except Exception:
        pass
    cache_manager = None


# Role-based access decorators - centralize session checks
def role_required(role):
    """Return a decorator that checks the session for a specific role.

    role: 'staff' | 'courier' | 'super_admin' | 'user'
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                if role == "staff" and session.get("staff_id"):
                    return fn(*args, **kwargs)
                if role == "courier" and session.get("courier_id"):
                    return fn(*args, **kwargs)
                if role == "super_admin" and session.get("super_admin"):
                    return fn(*args, **kwargs)
                if role == "user" and session.get("user_id"):
                    return fn(*args, **kwargs)

                # Not authorized
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                # Fallback redirect to login page depending on role
                if role == "courier":
                    return redirect(url_for("courier_login"))
                if role == "staff":
                    return redirect(url_for("staff_login"))
                if role == "super_admin":
                    return redirect(url_for("super_admin_login"))
                return redirect(url_for("login_page"))
            except Exception as e:
                app_logger.warning(f"role_required wrapper error: {str(e)}")
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("login_page"))

        return wrapper

    return decorator


# Simple caching decorator for API endpoints (uses cache_manager)
def cached(ttl=30, key_func=None):
    """Cache API JSON responses for `ttl` seconds using CacheManager.

    key_func(request, *args, **kwargs) -> str optional
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                cm = get_cache_manager()
                if not cm:
                    return fn(*args, **kwargs)

                if key_func and callable(key_func):
                    cache_key = key_func(request, *args, **kwargs)
                else:
                    # Default key: function name + sorted query params
                    params = dict(request.args) if request.args else {}
                    cache_key = f"{fn.__name__}:{json.dumps(params, sort_keys=True)}"

                cached_val = cm.get(cache_key)
                if cached_val is not None:
                    # If the view normally returns a dict/json for API endpoints
                    if request.path.startswith("/api/"):
                        return jsonify(cached_val)
                    return cached_val

                result = fn(*args, **kwargs)

                # Only cache JSON-able dicts for API endpoints
                if request.path.startswith("/api/"):
                    try:
                        if isinstance(result, tuple):
                            data = result[0]
                        else:
                            data = result
                        # Only cache when response looks like a JSON-able dict
                        if isinstance(data, dict):
                            cm.set(cache_key, data, ttl=ttl)
                    except Exception:
                        pass

                return result
            except Exception as e:
                app_logger.warning(f"cached decorator error: {str(e)}")
                return fn(*args, **kwargs)

        return wrapper

    return decorator


# CSRF helpers - define early so decorators are available before use
def generate_csrf_token():
    """Generate or return existing CSRF token stored in session."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def clear_session_conflicts():
    """Clear conflicting session data to prevent account mixing."""
    try:
        # Store current session type before clearing
        session_types = {
            "user": bool(session.get("user_id")),
            "staff": bool(session.get("staff_id")),
            "courier": bool(session.get("courier_id")),
            "super_admin": bool(session.get("super_admin")),
        }

        # Count active sessions
        active_sessions = sum(session_types.values())

        # If more than one session type is active, clear authentication-related keys but
        # preserve general, non-auth session data (cart, preferences, csrf token, etc.).
        if active_sessions > 1:
            app_logger.warning(
                f"Multiple session types detected: {session_types}. Clearing auth conflicts while preserving non-auth data."
            )

            # Preserve non-auth keys and CSRF token
            try:
                csrf_token = session.get("csrf_token")
                # Keep any key that does not look like an auth key. Auth keys start with
                # prefixes like 'user_', 'staff_', 'courier_', or are 'super_admin'/'admin_name'.
                preserved = {
                    k: v
                    for k, v in dict(session).items()
                    if not (
                        k.startswith("user_")
                        or k.startswith("staff_")
                        or k.startswith("courier_")
                        or k.startswith("admin_")
                        or k in ("super_admin", "admin_name", "session_id")
                    )
                }

                # Clear the whole session then restore preserved keys (safer across session backends)
                session.clear()
                session.update(preserved)

                if csrf_token:
                    session["csrf_token"] = csrf_token

                # Regenerate session_id to reduce session fixation & cross-device linkage
                import uuid as _uuid

                new_sid = str(_uuid.uuid4())
                session["session_id"] = new_sid
                session.permanent = True
                app_logger.info(
                    f"Session conflicts cleared; new session_id={new_sid[:8]}..."
                )
                return True
            except Exception as exc:
                app_logger.error(
                    f"Error while preserving session during conflict clear: {exc}"
                )
                # Fall back to previous conservative approach: remove common auth keys
                keys_to_clear = [
                    "user_id",
                    "user_phone",
                    "user_address",
                    "user_first_name",
                    "user_last_name",
                    "user_address_latitude",
                    "user_address_longitude",
                    "staff_id",
                    "staff_name",
                    "staff_role",
                    "staff_role_display",
                    "courier_id",
                    "courier_name",
                    "courier_phone",
                    "super_admin",
                    "admin_name",
                ]
                for key in keys_to_clear:
                    session.pop(key, None)
                session.permanent = True
                return True

        return False

    except Exception as e:
        app_logger.error(f"Session conflict clearing error: {str(e)}")
        return False


def secure_session_login(session_type, session_data):
    """Securely set session data with conflict prevention.

    Args:
        session_type: 'user', 'staff', 'courier', or 'super_admin'
        session_data: dict with session data to set
    """
    try:
        # Preserve non-auth session data (cart, preferences, csrf token) before touching auth keys.
        try:
            csrf_token = session.get("csrf_token")
            preserved = {
                k: v
                for k, v in dict(session).items()
                if not (
                    k.startswith("user_")
                    or k.startswith("staff_")
                    or k.startswith("courier_")
                    or k.startswith("admin_")
                    or k in ("super_admin", "session_id")
                )
            }
        except Exception:
            csrf_token = None
            preserved = {}

        # Clear conflicts and restore preserved keys to avoid losing guest/cart info
        clear_session_conflicts()
        session.clear()
        session.update(preserved)
        if csrf_token:
            session["csrf_token"] = csrf_token

        # Regenerate session_id on successful login to avoid session fixation / cross-device reuse
        try:
            import uuid as _uuid

            session["session_id"] = str(_uuid.uuid4())
        except Exception:
            # If uuid generation fails for some reason keep existing session_id
            pass

        # Set new session data based on type
        if session_type == "user":
            # Core identifiers
            session["user_id"] = session_data.get("user_id")
            # Friendly display name used across templates
            first = session_data.get("first_name", "")
            last = session_data.get("last_name", "")
            full_name = (
                f"{first} {last}".strip()
                or session_data.get("username")
                or session_data.get("email")
            )
            session["user_first_name"] = first
            session["user_last_name"] = last
            session["user_name"] = full_name
            # Contact and profile
            session["user_email"] = session_data.get("email", "")
            session["user_phone"] = session_data.get("phone", "")
            session["user_avatar"] = session_data.get("avatar") or session.get(
                "user_avatar"
            )
            # Address / geo
            session["user_address"] = session_data.get("address", "")
            session["user_address_latitude"] = session_data.get("address_latitude")
            session["user_address_longitude"] = session_data.get("address_longitude")

        elif session_type == "staff":
            session["staff_id"] = session_data.get("staff_id")
            session["staff_name"] = session_data.get("staff_name", "")
            session["staff_role"] = session_data.get("staff_role", "staff")
            session["staff_role_display"] = session_data.get(
                "staff_role_display", "Xodim"
            )

        elif session_type == "courier":
            session["courier_id"] = session_data.get("courier_id")
            session["courier_name"] = session_data.get("courier_name", "")
            session["courier_phone"] = session_data.get("courier_phone", "")

        elif session_type == "super_admin":
            session["super_admin"] = True
            session["admin_name"] = session_data.get("admin_name", "Super Admin")

        # Set session as permanent with proper timeout
        session.permanent = True

        # Generate a fresh CSRF token for the new authenticated session (preserve if already present)
        generate_csrf_token()

        app_logger.info(
            f"Secure session login completed for {session_type}; session_id={session.get('session_id')[:8]}..."
        )
        return True

    except Exception as e:
        app_logger.error(f"Secure session login error: {str(e)}")
        return False


@app.context_processor
def inject_navbar_context():
    """Provide template variables to decide which navbar to render.

    Rules implemented:
    - super_admin, staff, courier are role-specific and must be logged in to use their menus.
    - If no special role is logged in, show the public/user navbar.
    - If a normal user is logged in, expose `user_profile` and `notifications_count` so templates
      can show profile info and unread notifications icon.
    """
    try:
        is_user = bool(session.get("user_id"))
        is_staff = bool(session.get("staff_id"))
        is_courier = bool(session.get("courier_id"))
        is_super_admin = bool(session.get("super_admin"))

        # If any elevated role is present, prefer that role's navbar (they must be logged in)
        elevated = is_staff or is_courier or is_super_admin

        user_profile = {}
        notifications_count = 0

        if is_user and not elevated:
            # Build a minimal profile object for templates
            user_profile = {
                "name": session.get("user_name")
                or session.get("user_first_name")
                or "",
                "avatar": session.get("user_avatar") or None,
                "email": session.get("user_email") or None,
            }

            # Try to get unread notifications count (best-effort, silent on error)
            try:
                if session.get("user_id"):
                    # notifications table stores recipient as (recipient_type, recipient_id)
                    # and the read flag column is named 'read_flag'. Use those columns.
                    res = execute_query(
                        "SELECT COUNT(1) FROM notifications WHERE recipient_type = 'user' AND recipient_id = ? AND read_flag = 0",
                        (session.get("user_id"),),
                        fetch_one=True,
                    )
                    if res:
                        try:
                            notifications_count = int(res[0])
                        except Exception:
                            notifications_count = 0
            except Exception:
                notifications_count = 0

        return {
            "is_user": is_user and not elevated,
            "is_staff": is_staff,
            "is_courier": is_courier,
            "is_super_admin": is_super_admin,
            "user_profile": user_profile,
            "notifications_count": notifications_count,
        }
    except Exception as e:
        try:
            app_logger.warning(f"inject_navbar_context error: {e}")
        except Exception:
            pass
        return {}


def is_international_delivery_enabled():
    """Check if international delivery is enabled."""
    try:
        result = execute_query(
            "SELECT value FROM settings WHERE key = 'international_delivery'",
            fetch_one=True,
        )
        return result and str(result[0]).lower() in ("1", "true", "yes")
    except Exception as e:
        app_logger.error(f"Error checking international delivery: {str(e)}")
        return True  # Default to enabled


def accepts_orders_from_country(country_name):
    """Check if orders are accepted from a specific country."""
    try:
        if not is_international_delivery_enabled():
            return False

        # Get the main branch's supported countries
        result = execute_query(
            "SELECT international_countries FROM branches WHERE accepts_international = 1 AND is_active = 1 LIMIT 1",
            fetch_one=True,
        )

        if not result or not result[0]:
            return True  # If no restrictions specified, accept all

        supported_countries = str(result[0]).lower().split(",")
        country_check = country_name.lower().strip()

        # Check if country is in the supported list
        for supported in supported_countries:
            if country_check in supported.strip() or supported.strip() in country_check:
                return True

        return False

    except Exception as e:
        app_logger.error(
            f"Error checking country acceptance for {country_name}: {str(e)}"
        )
        return True  # Default to accepting if error occurs


def get_main_branch():
    """Get the main branch information."""
    try:
        # Get main branch ID from settings
        main_branch_result = execute_query(
            "SELECT value FROM settings WHERE key = 'main_branch_id'", fetch_one=True
        )

        if main_branch_result:
            main_branch_id = int(main_branch_result[0])
            branch = execute_query(
                "SELECT * FROM branches WHERE id = ? AND is_active = 1",
                (main_branch_id,),
                fetch_one=True,
            )
            if branch:
                return dict(branch) if hasattr(branch, "keys") else branch

        # Fallback to first active branch
        branch = execute_query(
            "SELECT * FROM branches WHERE is_active = 1 ORDER BY id LIMIT 1",
            fetch_one=True,
        )
        return dict(branch) if branch and hasattr(branch, "keys") else branch

    except Exception as e:
        app_logger.error(f"Error getting main branch: {str(e)}")
        return None


def csrf_protect(fn):
    """Simple CSRF protection decorator for POST endpoints that checks token in form/json headers."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            # Check token in header first, then json body, then form
            header = request.headers.get("X-CSRF-Token")
            token = (
                header
                or (request.get_json(silent=True) or {}).get("csrf_token")
                or request.form.get("csrf_token")
            )
            if not token or token != session.get("csrf_token"):
                app_logger.warning("CSRF token mismatch or missing")
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "CSRF token missing or invalid"}), 403
                flash("CSRF token noto'g'ri yoki yo'q", "error")
                return redirect(request.referrer or url_for("index"))
        return fn(*args, **kwargs)

    return wrapper


# -------------------------
# Background task submission helper (safe fallback)
def safe_submit(fn, *args, **kwargs):
    """
    Submit background task to executor if available.
    Fallbacks:
      - try to lazily create ThreadPoolExecutor
      - if executor unavailable, use threading.Thread (daemon)
      - if even that fails, run synchronously (last resort)
    Returns: concurrent.futures.Future or threading.Thread or direct function result / None
    """
    global executor
    try:
        # Lazy create executor if possible
        if executor is None:
            try:
                executor = ThreadPoolExecutor(
                    max_workers=getattr(Config, "THREAD_POOL_MAX_WORKERS", 4)
                )
                app_logger.info("Lazy ThreadPoolExecutor created by safe_submit")
            except Exception as e:
                executor = None
                app_logger.debug(f"Could not create ThreadPoolExecutor lazily: {e}")

        if executor is not None and hasattr(executor, "submit"):
            return executor.submit(fn, *args, **kwargs)

        # Fallback to threading.Thread
        try:
            t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
            t.start()
            return t
        except Exception as thread_err:
            app_logger.warning(f"Thread fallback failed in safe_submit: {thread_err}")

        # Last resort: run synchronously
        try:
            return fn(*args, **kwargs)
        except Exception as sync_err:
            app_logger.error(f"Running task synchronously failed: {sync_err}")
            return None

    except Exception as e:
        try:
            app_logger.error(f"safe_submit unexpected error: {e}")
        except:
            print(f"safe_submit unexpected error: {e}")
        return None


# -------------------------


# Rate limiting
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, identifier, max_requests=100, window=3600):
        "Rate limiting tekshiruvi"
        current_time = time.time()

        with self.lock:
            # Eski so'rovlarni tozalash
            self.requests[identifier] = [
                req_time
                for req_time in self.requests[identifier]
                if current_time - req_time < window
            ]

            # Yangi so'rovni qo'shish
            if len(self.requests[identifier]) < max_requests:
                self.requests[identifier].append(current_time)
                return True

            return False


rate_limiter = RateLimiter()

# Thread pool for async operations with configurable workers
# ThreadPoolExecutor is expensive to create at import time; skip when running lightweight tests
executor = None
if not os.environ.get("SKIP_DB_INIT"):
    try:
        executor = ThreadPoolExecutor(max_workers=Config.THREAD_POOL_MAX_WORKERS)
        print("DEBUG: ThreadPoolExecutor created")
    except Exception:
        executor = None

# Database fayl yo'lini to'g'rilash
DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")

import logging
from logging.handlers import RotatingFileHandler, SMTPHandler


# Global error handlers
@app.errorhandler(404)
def not_found_error(error):
    app_logger.warning(f"404 Error: {request.url}")

    # Collect diagnostics to help identify why some clients receive JSON
    headers_snapshot = {
        "User-Agent": request.headers.get("User-Agent"),
        "Accept": request.headers.get("Accept"),
        "X-Requested-With": request.headers.get("X-Requested-With"),
        "Path": request.path,
        "is_json": request.is_json,
    }

    # Decision rule:
    # - If the path is an API call (starts with /api/) -> return JSON
    # - Else if the request method is GET (normal browser navigation) -> return HTML
    # - Otherwise (non-GET non-API), fall back to JSON for clients that expect it
    wants_json = request.path.startswith("/api/") or request.is_json

    app_logger.debug(
        f"404 diagnostics: {headers_snapshot} wants_json={wants_json} method={request.method}"
    )

    if wants_json and request.method != "GET":
        # For API endpoints and non-GET requests that indicate JSON usage, return JSON
        return jsonify({"error": "Not found", "code": 404}), 404

    # Otherwise serve an HTML page for GET navigations (safe for browsers/crawlers)
    try:
        return (
            render_template(
                "error.html", error_code=404, error_message="Sahifa topilmadi"
            ),
            404,
        )
    except Exception as e:
        app_logger.debug(f"Rendering error.html failed: {e}")
        return (
            """
        <!DOCTYPE html>
        <html>
        <head><title>404 Not Found</title></head>
        <body>
            <h1>404 - Sahifa topilmadi</h1>
            <p>So'ralgan sahifa mavjud emas.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        """,
            404,
        )


@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"500 Error: {str(error)} - URL: {request.url}")
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error", "code": 500}), 500

    try:
        return (
            render_template(
                "error.html", error_code=500, error_message="Server xatoligi"
            ),
            500,
        )
    except:
        return (
            """
        <!DOCTYPE html>
        <html>
        <head><title>500 Internal Server Error</title></head>
        <body>
            <h1>500 - Server xatoligi</h1>
            <p>Ichki server xatoligi yuz berdi.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        """,
            500,
        )


@app.errorhandler(429)
def rate_limit_error(error):
    app_logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({"error": "Rate limit exceeded", "code": 429}), 429

    try:
        return (
            render_template(
                "error.html", error_code=429, error_message="Juda ko'p so'rov"
            ),
            429,
        )
    except:
        return (
            """
        <!DOCTYPE html>
        <html>
        <head><title>429 Too Many Requests</title></head>
        <body>
            <h1>429 - Juda ko'p so'rov</h1>
            <p>Juda ko'p so'rov yuborildi. Biroz kuting.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        """,
            429,
        )


@app.errorhandler(Exception)
def handle_exception(e):
    "Global exception handler"
    # Log the exception message and full traceback to help locate the origin of errors
    try:
        app_logger.error(f"Unhandled exception: {str(e)} - URL: {request.url}")
        tb = traceback.format_exc()
        app_logger.error(f"Full traceback:\n{tb}")
        # Also print to stdout so test scripts can capture it easily
        try:
            print("DEBUG-TRACEBACK:")
            print(tb)
        except Exception:
            pass
    except Exception:
        # Best-effort logging
        try:
            app_logger.error(f"Unhandled exception (minimal): {str(e)}")
        except Exception:
            pass

    if request.is_json or request.path.startswith("/api/"):
        return (
            jsonify(
                {
                    "error": "Unexpected error occurred",
                    "code": 500,
                    "details": (
                        str(e) if Config.IS_DEVELOPMENT else "Internal server error"
                    ),
                }
            ),
            500,
        )

    try:
        return (
            render_template(
                "error.html",
                error_code=500,
                error_message="Kutilmagan xatolik yuz berdi",
            ),
            500,
        )
    except:
        return (
            """
        <!DOCTYPE html>
        <html>
        <head><title>Unexpected Error</title></head>
        <body>
            <h1>Kutilmagan xatolik</h1>
            <p>Dasturda kutilmagan xatolik yuz berdi.</p>
            <a href="/">Bosh sahifaga qaytish</a>
        </body>
        </html>
        """,
            500,
        )


# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times = []
        self.lock = threading.Lock()
        self.error_count = 0
        self.success_count = 0
        self.last_cleanup = time.time()

    def record_request(self, duration, endpoint, status_code=200):
        with self.lock:
            try:
                self.request_times.append(
                    {
                        "duration": duration,
                        "endpoint": endpoint,
                        "timestamp": time.time(),
                        "status_code": status_code,
                    }
                )

                # Status ni hisoblash
                if status_code >= 400:
                    self.error_count += 1
                else:
                    self.success_count += 1

                # Memory management - har 10 daqiqada eski ma'lumotlarni tozalash
                current_time = time.time()
                if current_time - self.last_cleanup > 600:  # 10 daqiqa
                    cutoff_time = current_time - 3600  # 1 soat
                    self.request_times = [
                        req
                        for req in self.request_times
                        if req["timestamp"] > cutoff_time
                    ]
                    self.last_cleanup = current_time

                # Faqat so'nggi 1000 ta so'rovni saqlash
                if len(self.request_times) > 1000:
                    self.request_times = self.request_times[-1000:]

            except Exception as e:
                app_logger.error(f"Performance monitoring xatoligi: {str(e)}")

    def get_stats(self):
        with self.lock:
            if not self.request_times:
                return {}

            durations = [req["duration"] for req in self.request_times]
            return {
                "avg_response_time": sum(durations) / len(durations),
                "max_response_time": max(durations),
                "min_response_time": min(durations),
                "total_requests": len(durations),
            }


# Performance monitor instance yaratish - to'g'ri e'lon qilish
try:
    performance_monitor = PerformanceMonitor()
    app_logger.info("Performance monitor muvaffaqiyatli yaratildi")
except Exception as e:
    app_logger.warning(f"Performance monitor yaratishda xatolik: {str(e)}")

    # Fallback performance monitor yaratish
    class DummyPerformanceMonitor:
        def record_request(self, duration, endpoint, status_code=200):
            pass

        def get_stats(self):
            return {}

    performance_monitor = DummyPerformanceMonitor()


@app.before_request
def before_request():
    "So'rov boshlanishida xavfsiz pre-processing"
    try:
        # Request time tracking - g obyektiga saqlash
        g.start_time = time.time()

        # Session ni tekshirish va tuzatish
        if not session.get("session_id") or session.get("session_id") == "None":
            session["session_id"] = get_session_id()

        # Database connection test
        if not hasattr(g, "db_test_done"):
            try:
                test_conn = get_db()
                test_conn.execute("SELECT 1")
                test_conn.close()  # Connectionni yopamiz
                g.db_test_done = True
            except Exception as db_error:
                app_logger.error(f"Database connection test failed: {str(db_error)}")

        # Record session presence to sessions table for active session tracking
        try:
            sid = session.get("session_id") or get_session_id()
            # IP and User-Agent
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            ua = request.headers.get("User-Agent", "")
            # If user is logged in, associate user_id
            uid = session.get("user_id")
            record_session_entry(sid, uid, ip, ua)
        except Exception:
            # Non-fatal
            pass

    except Exception as e:
        app_logger.error(f"Before request error: {str(e)}")
        # Error bo'lsa ham davom ettirish


@app.after_request
def after_request(response):
    "Request tugagandan keyin ishlaydigan function"
    try:
        end_time = time.time()
        start_time = getattr(g, "start_time", end_time)
        duration = end_time - start_time

        # Performance monitoring - fixed to use function call
        try:
            # Check if performance_monitor has the record_request method
            if hasattr(performance_monitor, "record_request") and callable(
                performance_monitor.record_request
            ):
                performance_monitor.record_request(
                    duration, request.endpoint or "unknown", response.status_code
                )
            else:
                # Log a warning if the method is missing or not callable
                app_logger.warning(
                    "performance_monitor object does not have a callable 'record_request' method."
                )
        except Exception as pm_error:
            app_logger.warning(f"Performance monitoring error: {str(pm_error)}")

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Cache headers faqat static files uchun emas
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        if Config.IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

    except Exception as e:
        # Silent pass - xavfsizlik uchun
        app_logger.warning(f"After request error (silent): {str(e)}")
        pass

    return response


AVG_PREP_MINUTES = int(os.environ.get("AVG_PREP_MINUTES", "7"))
# o'rtacha tayyorlanish vaqti (daqiqalarda)

# Initialize SQLAlchemy only if using PostgreSQL
if Config.DATABASE_URL.startswith("postgresql"):
    db = SQLAlchemy(app)
else:
    db = None  # Use custom SQLite connection pool instead

# O'zbekiston vaqt zonasi
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")


def get_current_time():
    return datetime.datetime.now(TASHKENT_TZ)


# Database connection pool
class DatabasePool:
    def __init__(self, db_path, max_connections=10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()
        self.connection_count = 0
        self._init_pool()

    def _init_pool(self):
        "Connection pool ni ishga tushirish"
        for _ in range(3):  # Boshlang'ich 3 ta connection (kamaytirildi)
            conn = self._create_connection()
            if conn:
                self.connections.append(conn)

    def _create_connection(self):
        "Yangi database connection yaratish - timeout fix bilan"
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Timeout ni oshirish va retry logic yaxshilash
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=60.0,  # 60 soniya timeout
                    isolation_level=None,
                )
                conn.row_factory = sqlite3.Row

                # SQLite optimallashtirish sozlamalari - timeout uchun
                try:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA cache_size=10000")
                    conn.execute("PRAGMA temp_store=MEMORY")
                    conn.execute("PRAGMA foreign_keys=ON")
                    conn.execute("PRAGMA busy_timeout=30000")  # 30 soniya busy timeout
                    conn.execute("PRAGMA wal_autocheckpoint=1000")
                    conn.execute("PRAGMA optimize")
                except Exception as pragma_error:
                    app_logger.warning(f"PRAGMA settings failed: {str(pragma_error)}")

                # Connection test with timeout
                conn.execute("SELECT 1").fetchone()
                return conn

            except sqlite3.OperationalError as e:
                if (
                    "database is locked" in str(e).lower()
                    or "timeout" in str(e).lower()
                ):
                    wait_time = min(5.0, 0.5 * (2**attempt))  # Exponential backoff
                    app_logger.warning(
                        f"Database locked/timeout, retrying in {wait_time}s (attempt {attempt + 1})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    app_logger.error(f"Database connection error: {str(e)}")
                    if attempt == max_retries - 1:
                        return None
            except Exception as e:
                app_logger.error(
                    f"Database connection attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt == max_retries - 1:
                    app_logger.critical(
                        f"Database connection yaratishda XATOLIK: {str(e)}"
                    )
                    return None
                time.sleep(0.5 * (attempt + 1))

        return None

    @contextmanager
    def get_connection(self):
        "Context manager orqali connection olish - improved error handling"
        conn = None
        start_time = time.time()

        try:
            # Connection olish - timeout bilan
            timeout_duration = 30  # 30 soniya timeout

            while time.time() - start_time < timeout_duration:
                with self.lock:
                    if self.connections:
                        conn = self.connections.pop()
                        break
                    elif self.connection_count < self.max_connections:
                        self.connection_count += 1
                        break

                # Agar connection mavjud bo'lmasa, biroz kutish
                time.sleep(0.1)

            if not conn:
                # Yangi connection yaratish
                conn = self._create_connection()
                if not conn:
                    raise Exception(
                        "Database connection timeout - yangi connection yaratib bo'lmadi"
                    )

            # Connection ni test qilish - safe method
            try:
                test_result = conn.execute("SELECT 1").fetchone()
                if test_result is None:
                    raise Exception("Connection test returned None")
            except Exception as test_error:
                app_logger.warning(
                    f"Connection test failed, creating new one: {str(test_error)}"
                )
                try:
                    conn.close()
                except:
                    pass
                conn = self._create_connection()
                if not conn:
                    raise Exception("Database connection timeout")

            yield conn

        except sqlite3.OperationalError as e:
            if "timeout" in str(e).lower() or "locked" in str(e).lower():
                app_logger.error(f"Database timeout error: {str(e)}")
                raise Exception("Database connection timeout")
            else:
                raise e
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            app_logger.error(f"Database pool error: {str(e)}")
            raise e
        finally:
            if conn:
                try:
                    with self.lock:
                        if len(self.connections) < self.max_connections:
                            self.connections.append(conn)
                        else:
                            try:
                                conn.close()
                            except:
                                pass
                        if self.connection_count > 0:
                            self.connection_count -= 1
                except Exception as cleanup_error:
                    app_logger.warning(
                        f"Connection cleanup error: {str(cleanup_error)}"
                    )
                    try:
                        if conn:
                            conn.close()
                    except:
                        pass


# Global database pool with configurable max connections (lazy-init)
db_pool = None


def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = DatabasePool(DB_PATH, Config.DB_POOL_MAX_CONNECTIONS)
        try:
            print("DEBUG: DatabasePool created")
        except Exception:
            pass
    return db_pool


def get_db():
    "Legacy support uchun - timeout fix bilan"
    try:
        conn = sqlite3.connect(
            DB_PATH, check_same_thread=False, timeout=60.0  # 60 soniya timeout
        )
        conn.row_factory = sqlite3.Row

        # Ensure foreign keys are enforced for legacy connections and set sensible pragmas
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception as pragma_err:
            app_logger.warning(f"get_db PRAGMA setup failed: {str(pragma_err)}")

        # Basic connection test
        conn.execute("SELECT 1").fetchone()
        return conn
    except Exception as e:
        app_logger.error(f"get_db connection error: {str(e)}")
        raise Exception("Database connection timeout")


def _now_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def record_session_entry(session_id, user_id=None, ip=None, user_agent=None):
    """Create or update a sessions table entry for the given session_id."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cur = conn.cursor()
        now = _now_iso()
        try:
            cur.execute("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
        except sqlite3.OperationalError as oe:
            # Table probably doesn't exist yet; create it and retry once
            if "no such table" in str(oe).lower():
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        user_id INTEGER,
                        ip TEXT,
                        user_agent TEXT,
                        created_at TEXT NOT NULL,
                        last_seen TEXT NOT NULL
                    );
                    """
                )
                conn.commit()
                # retry select
                cur.execute(
                    "SELECT id FROM sessions WHERE session_id = ?", (session_id,)
                )
            else:
                raise

        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE sessions SET user_id = ?, ip = ?, user_agent = ?, last_seen = ? WHERE session_id = ?",
                (user_id, ip, user_agent, now, session_id),
            )
        else:
            cur.execute(
                "INSERT INTO sessions (session_id, user_id, ip, user_agent, created_at, last_seen) VALUES (?,?,?,?,?,?)",
                (session_id, user_id, ip, user_agent, now, now),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        try:
            app_logger.error(f"record_session_entry error: {e}")
        except:
            pass


def get_user_sessions(user_id):
    """Return list of active sessions for a user ordered by last_seen desc."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT session_id, ip, user_agent, created_at, last_seen FROM sessions WHERE user_id = ? ORDER BY last_seen DESC",
                (user_id,),
            )
        except sqlite3.OperationalError as oe:
            if "no such table" in str(oe).lower():
                return []
            raise
        rows = cur.fetchall() or []
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try:
            app_logger.error(f"get_user_sessions error: {e}")
        except:
            pass
        return []


def terminate_session(session_id_to_kill, current_session_id=None):
    """Remove a session record and clear flask session if it's the current session."""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id_to_kill,)
            )
            conn.commit()
        except sqlite3.OperationalError as oe:
            if "no such table" in str(oe).lower():
                # nothing to delete
                conn.close()
                if current_session_id and session_id_to_kill == current_session_id:
                    session.clear()
                return True
            raise
        conn.close()
        if current_session_id and session_id_to_kill == current_session_id:
            session.clear()
        return True
    except Exception as e:
        try:
            app_logger.error(f"terminate_session error: {e}")
        except:
            pass
        return False


# Ensure database schema exists before first request (safe registration)
def ensure_db_schema():
    try:
        init_db()
        app_logger.info("Database initialized/check complete")
    except Exception as e:
        try:
            app_logger.warning(f"init_db warning: {str(e)}")
        except:
            pass


# Try to register using Flask API if available, else call immediately
try:
    if hasattr(app, "before_first_request") and callable(
        getattr(app, "before_first_request")
    ):
        app.before_first_request(ensure_db_schema)
    else:
        # Fallback: run once now only if not explicitly skipping DB init
        if not os.environ.get("SKIP_DB_INIT"):
            ensure_db_schema()
except Exception:
    try:
        if not os.environ.get("SKIP_DB_INIT"):
            ensure_db_schema()
    except Exception:
        pass


def check_database_health():
    "Database connection holatini tekshirish"
    try:
        result = execute_query("SELECT 1", fetch_one=True)
        return result is not None
    except Exception as e:
        app_logger.error(f"Database health check failed: {str(e)}")
        return False


def safe_count(query, params=None):
    """Run COUNT(*) queries safely and return integer 0 on error."""
    try:
        result = execute_query(query, params, fetch_one=True)
        if not result:
            return 0
        # result may be tuple or dict-like
        try:
            return int(result[0])
        except Exception:
            # dict-like
            try:
                return int(list(result.values())[0])
            except Exception:
                return 0
    except Exception as e:
        app_logger.warning(f"safe_count error for query: {query} -> {str(e)}")
        return 0


@app.route("/api/set-settings", methods=["POST"])
@csrf_protect
def api_set_settings():
    """Minimal API to accept settings and avoid 404s from frontend. It stores settings in a simple config table."""
    data = request.get_json() or {}

    # If super_admin is setting system-wide config, persist to file
    if session.get("super_admin"):
        try:
            with open("superadmin_settings.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"success": True, "message": "System settings saved"})
        except Exception as e:
            app_logger.error(f"Failed to save system settings: {str(e)}")
            return (
                jsonify({"success": False, "message": "Failed to save settings"}),
                500,
            )

    # Allow logged-in users (any role) to save personal UI settings (theme, font, language)
    try:
        # Normalize common frontend keys and save to session
        # Accept: theme ('dark'/'light' or bool), dark_theme (bool), font_size or fontSize, language
        if "theme" in data:
            val = data.get("theme")
            if isinstance(val, str):
                session["dark_theme"] = val.lower() == "dark"
            else:
                session["dark_theme"] = bool(val)

        if "dark_theme" in data:
            session["dark_theme"] = bool(data.get("dark_theme"))

        if "font_size" in data:
            session["font_size"] = data.get("font_size") or "medium"
        if "fontSize" in data:
            session["font_size"] = data.get("fontSize") or session.get(
                "font_size", "medium"
            )

        if "language" in data:
            session["interface_language"] = data.get("language") or "uz"

        # If a user is logged in, persist to users table
        user_id = session.get("user_id")
        if user_id:
            try:
                execute_query(
                    "UPDATE users SET dark_theme = ?, font_size = ?, interface_language = ? WHERE id = ?",
                    (
                        1 if session.get("dark_theme") else 0,
                        session.get("font_size", "medium"),
                        session.get("interface_language", "uz"),
                        user_id,
                    ),
                )
            except Exception as db_err:
                app_logger.warning(
                    f"Failed to persist user settings to DB: {str(db_err)}"
                )

        return jsonify({"success": True, "message": "Settings saved to session"})
    except Exception as e:
        app_logger.error(f"api_set_settings error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to save settings"}), 500


# Optimized database operations with timeout handling
def execute_query(query, params=None, fetch_one=False, fetch_all=False, max_retries=3):
    "Optimizatsiya qilingan database so'rovi - improved None handling"
    last_error = None

    for attempt in range(max_retries):
        try:
            pool = get_db_pool()
            with pool.get_connection() as conn:
                if conn is None:
                    raise Exception("Connection is None")

                cur = conn.cursor()

                # Query ni timeout bilan bajarish
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)

                if fetch_one:
                    result = cur.fetchone()
                    if result is None:
                        return None

                    # Build a small proxy that supports both dict-like access (.get('col'))
                    # and integer indexing (result[0]) because callers expect both.
                    cols = [c[0] for c in (cur.description or [])]

                    class RowProxy(dict):
                        def __init__(self, columns, values):
                            # Map column name -> value
                            super().__init__(zip(columns, values) if columns else {})
                            self._values = tuple(values)
                            self._columns = list(columns)

                        def __getitem__(self, key):
                            if isinstance(key, int):
                                return self._values[key]
                            return super().__getitem__(key)

                        def get(self, key, default=None):
                            return super().get(key, default)

                        def keys(self):
                            return super().keys()

                    return RowProxy(cols, result)

                elif fetch_all:
                    all_results = cur.fetchall() or []
                    if not all_results:
                        return []

                    cols = [c[0] for c in (cur.description or [])]

                    class RowProxy(dict):
                        def __init__(self, columns, values):
                            super().__init__(zip(columns, values) if columns else {})
                            self._values = tuple(values)
                            self._columns = list(columns)

                        def __getitem__(self, key):
                            if isinstance(key, int):
                                return self._values[key]
                            return super().__getitem__(key)

                        def get(self, key, default=None):
                            return super().get(key, default)

                        def keys(self):
                            return super().keys()

                    proxy_rows = []
                    for r in all_results:
                        try:
                            proxy_rows.append(RowProxy(cols, r))
                        except Exception:
                            # Fallback to raw row if proxy creation fails
                            proxy_rows.append(r)
                    return proxy_rows
                else:
                    conn.commit()
                    # Safe lastrowid return
                    try:
                        return cur.lastrowid
                    except (AttributeError, TypeError):
                        return None

        except sqlite3.OperationalError as e:
            last_error = e
            if "timeout" in str(e).lower() or "locked" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (2**attempt)  # Exponential backoff
                    app_logger.warning(
                        f"Database timeout, retrying in {wait_time}s (attempt {attempt + 1})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    app_logger.error(
                        f"Database timeout after {max_retries} attempts: {str(e)}"
                    )
                    raise Exception("Database connection timeout")
            else:
                app_logger.error(f"Database operational error: {str(e)}")
                raise e
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                app_logger.warning(
                    f"Query execution failed, retrying (attempt {attempt + 1}): {str(e)}"
                )
                time.sleep(0.5)
                continue
            else:
                app_logger.error(
                    f"execute_query error after {max_retries} attempts: {str(e)} - Query: {query[:100]}..."
                )
                raise e

    # Agar barcha attempts muvaffaqiyatsiz bo'lsa
    if last_error:
        raise last_error
    else:
        raise Exception("Unknown database error")


def execute_many(query, params_list):
    "Bulk operations uchun optimizatsiya"
    with db_pool.get_connection() as conn:
        try:
            cur = conn.cursor()
            cur.executemany(query, params_list)
            conn.commit()
            return cur.rowcount
        except Exception as e:
            conn.rollback()
            app_logger.error(f"execute_many error: {str(e)} - Query: {query[:100]}...")
            raise e


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Product Media table - mahsulot rasmlari va videolarini saqlash
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS product_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item_id INTEGER NOT NULL,
            media_type TEXT NOT NULL DEFAULT 'image',  -- 'image' yoki 'video'
            media_url TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            is_main BOOLEAN DEFAULT 0,  -- asosiy rasm
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE
        );
    """
    )

    # Payment cards table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT NOT NULL,
            card_holder_name TEXT NOT NULL,
            card_type TEXT DEFAULT 'visa',
            is_active BOOLEAN DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
    """
    )

    # Card Payment Settings table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS card_payment_settings (
            id INTEGER PRIMARY KEY,
            card_number TEXT NOT NULL,
            card_name TEXT NOT NULL,
            click_qr_url TEXT,
            payme_qr_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
    """
    )

    # 360 Photos table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS photos_360 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image_url TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            created_by INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (created_by) REFERENCES staff (id)
        );
    """
    )

    # Foydalanuvchilar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            address TEXT,
            card_number TEXT,
            card_expiry TEXT,
            created_at TEXT NOT NULL,
            address_latitude REAL,
            address_longitude REAL,
            interface_language TEXT DEFAULT 'uz',
            font_size TEXT DEFAULT 'medium',
            dark_theme BOOLEAN DEFAULT 1
        );
    """
    )

    # Xodimlar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            phone TEXT NOT NULL,
            passport_series TEXT NOT NULL,
            passport_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            total_hours REAL DEFAULT 0,
            orders_handled INTEGER DEFAULT 0,
            last_activity TEXT,
            created_at TEXT NOT NULL
        );
    """
    )

    # Kuryerlar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS couriers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            phone TEXT NOT NULL,
            passport_series TEXT NOT NULL,
            passport_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            total_hours REAL DEFAULT 0,
            deliveries_completed INTEGER DEFAULT 0,
            last_activity TEXT,
            created_at TEXT NOT NULL
        );
    """
    )

    # Buyurtmalar jadvali (yangilangan)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            ticket_no INTEGER NOT NULL,
            order_type TEXT NOT NULL, -- 'dine_in' yoki 'delivery'
            status TEXT NOT NULL,
            delivery_address TEXT,
            delivery_distance REAL DEFAULT 0, -- masofa km da
            delivery_price REAL DEFAULT 0, -- yetkazish narxi
            delivery_latitude REAL,
            delivery_longitude REAL,
            delivery_map_url TEXT,
            customer_note TEXT,
            customer_phone TEXT,
            card_number TEXT,
            courier_id INTEGER,
            courier_price REAL DEFAULT 0,
            courier_delivery_minutes INTEGER DEFAULT 0,
            branch_id INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            eta_time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (courier_id) REFERENCES couriers (id)
        );
    """
    )

    # Tikketlar hisoblagich
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        );
    """
    )
    cur.execute(
        "INSERT OR IGNORE INTO counters (name, value) VALUES ('ticket', 10000);"
    )

    # Menyu mahsulotlari (yangilangan)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            available BOOLEAN DEFAULT 1,
            stock_quantity INTEGER DEFAULT 0,
            orders_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 0.0,
            discount_percentage REAL DEFAULT 0.0,
            sizes TEXT DEFAULT NULL,    -- JSON or comma-separated sizes (e.g. "38,39,40")
            colors TEXT DEFAULT NULL,   -- JSON or comma-separated colors (e.g. "black,brown")
            created_at TEXT NOT NULL
        );
    """
    )

    # Sevimlilar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id),
            UNIQUE(user_id, menu_item_id)
        );
    """
    )

    # Savatcha jadvali (yangilangan)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT NOT NULL DEFAULT 'default_session',
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    """
    )

    # Buyurtma tafsilotlari jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    """
    )

    # Baholar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id),
            UNIQUE(user_id, menu_item_id)
        );
    """
    )

    # Savollar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
    """
    )

    # Cheklar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            receipt_number TEXT NOT NULL UNIQUE,
            total_amount REAL NOT NULL,
            cashback_amount REAL NOT NULL,
            cashback_percentage REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        );
    """
    )

    # Filiallar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            phone TEXT,
            working_hours TEXT DEFAULT '09:00-22:00',
            is_active BOOLEAN DEFAULT 1,
            delivery_radius REAL DEFAULT 15.0,
            created_at TEXT NOT NULL
        );
    """
    )

    # Boshlang'ich taomlar qo'shish
    cur.execute("SELECT COUNT(*) FROM menu_items")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        # Seed sample products for a footwear/shop catalogue with different categories.
        sample_items = [
            # Tufli kategoriyasi
            (
                "Klassik Tufli - Qora",
                850000,
                "tufli",
                "Yuqori sifatli teri tufli, rasmiy kiyinish uchun",
                "/static/images/formal-shoes-black.jpg",
                1,
                25,
                5,
                4.7,
                0.0,
                "39,40,41,42,43,44",
                "qora,jigarrang",
                now,
            ),
            (
                "Biznes Tufli - Jigarrang",
                950000,
                "tufli",
                "Premium teri biznes tufli, har kunlik kiyish uchun",
                "/static/images/business-shoes.jpg",
                1,
                30,
                8,
                4.8,
                5.0,
                "40,41,42,43,44",
                "jigarrang,qora",
                now,
            ),
            # Etik kategoriyasi
            (
                "Qishki Etik",
                1200000,
                "etik",
                "Issiq va chidamli qishki etik, barcha ob-havo uchun",
                "/static/images/winter-boots.jpg",
                1,
                20,
                12,
                4.9,
                10.0,
                "39,40,41,42,43",
                "qora,jigarrang,kulrang",
                now,
            ),
            (
                "Ishchi Etigi",
                980000,
                "etik",
                "Mustahkam ishchi etigi, xavfsizlik uchun",
                "/static/images/work-boots.jpg",
                1,
                18,
                3,
                4.6,
                0.0,
                "40,41,42,43,44,45",
                "qora,jigarrang",
                now,
            ),
            # Krosovka kategoriyasi
            (
                "Sport Krosovka",
                750000,
                "krosovka",
                "Qulay sport krosovka, yugurish va fitnes uchun",
                "/static/images/sport-sneakers.jpg",
                1,
                50,
                25,
                4.5,
                15.0,
                "36,37,38,39,40,41,42",
                "oq,qora,ko'k,qizil",
                now,
            ),
            (
                "Kungslik Krosovka",
                650000,
                "krosovka",
                "Har kunlik kiyish uchun moslashgan zamonaviy krosovka",
                "/static/images/casual-sneakers.jpg",
                1,
                40,
                18,
                4.4,
                0.0,
                "37,38,39,40,41,42",
                "oq,kulrang,qora",
                now,
            ),
            # Mokasima kategoriyasi
            (
                "Teri Mokasima",
                550000,
                "mokasima",
                "Yumshoq va qulay teri mokasima, ofis va dam olish uchun",
                "/static/images/leather-loafers.jpg",
                1,
                35,
                7,
                4.6,
                0.0,
                "38,39,40,41,42",
                "jigarrang,qora,to'q ko'k",
                now,
            ),
            # Botik kategoriyasi
            (
                "Ayollar Botiki",
                480000,
                "botik",
                "Zamonaviy va qulay ayollar botiki, har kuni uchun",
                "/static/images/womens-flats.jpg",
                1,
                45,
                22,
                4.3,
                20.0,
                "35,36,37,38,39,40",
                "qora,jigarrang,oq,qizil",
                now,
            ),
            # Tapochka kategoriyasi
            (
                "Uy Tapochkasi",
                120000,
                "tapochka",
                "Yumshoq va issiq uy tapochkasi, dam olish uchun",
                "/static/images/house-slippers.jpg",
                1,
                60,
                35,
                4.2,
                0.0,
                "36,37,38,39,40,41,42,43",
                "kulrang,jigarrang,qora,ko'k",
                now,
            ),
            (
                "Hammom Tapochkasi",
                85000,
                "tapochka",
                "Suv o'tkazmaydigan hammom tapochkasi",
                "/static/images/bathroom-slippers.jpg",
                1,
                80,
                42,
                4.0,
                0.0,
                "36,37,38,39,40,41,42",
                "oq,ko'k,qizil,yashil",
                now,
            ),
        ]

        cur.executemany(
            "INSERT INTO menu_items (name, price, category, description, image_url, available, stock_quantity, orders_count, rating, discount_percentage, sizes, colors, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_items,
        )

    # Yangiliklar jadvali
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            type TEXT NOT NULL DEFAULT 'news',  -- 'news' yoki 'advertisement'
            image_url TEXT,
            video_url TEXT,
            is_active BOOLEAN DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_by INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (created_by) REFERENCES staff (id)
        );
    """
    )

    # Boshlang'ich yangiliklarni qo'shish
    cur.execute("SELECT COUNT(*) FROM news")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        sample_news = [
            (
                "🎉 Yangi kolleksiya!",
                "Bahorgi yangi oyoq kiyimlar kolleksiyasi do'konimizga keldi! 50% gacha chegirmalar.",
                "advertisement",
                "/static/images/default-men.jpg",
                None,
                1,
                1,
                1,
                now,
                now,
            ),
            (
                "🚚 Bepul yetkazib berish",
                "Endi 300,000 so'mdan yuqori xaridlar uchun bepul yetkazib berish xizmati!",
                "news",
                None,
                None,
                1,
                2,
                1,
                now,
                now,
            ),
            (
                "⭐ Mijozlar bahosi",
                "Do'konimiz 4.8/5 bahoga ega bo'ldi. Rahmat barcha mijozlarimizga!",
                "news",
                None,
                None,
                1,
                3,
                1,
                now,
                now,
            ),
            (
                "💳 Click va Payme orqali to'lov",
                "Endi sizlar uchun yanada qulay - Click va Payme orqali to'lov imkoni!",
                "advertisement",
                "/static/images/default-product.jpg",
                None,
                1,
                4,
                1,
                now,
                now,
            ),
        ]
        cur.executemany(
            "INSERT INTO news (title, content, type, image_url, video_url, is_active, display_order, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_news,
        )

    # Create branches table with international delivery support
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            phone TEXT,
            working_hours TEXT,
            is_active BOOLEAN DEFAULT 1,
            delivery_radius REAL DEFAULT 0,
            accepts_international BOOLEAN DEFAULT 0,
            international_countries TEXT,
            created_at TEXT NOT NULL
        );
        """
    )

    # Boshlang'ich filiallarni qo'shish - bitta asosiy filial bilan
    cur.execute("SELECT COUNT(*) FROM branches")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        # Single main branch that accepts international orders including Russia
        main_branch = (
            "Pro-Obuv Markaziy Filial",
            "Markaziy filial - Butun dunyo bo'ylab yetkazib berish",
            41.236832,  # Updated coordinates
            69.203578,
            "+998712345678",
            "9:00 - 18:00",  # Updated working hours
            1,  # is_active
            999999.0,  # unlimited delivery radius
            1,  # accepts_international
            "Rossiya,Qozog'iston,Qirg'iziston,Tojikiston,Turkmaniston,Ozarbayjon,Belorussiya,Ukraina,Gruziya,Armaniston,Moldaviya,Latviya,Estoniya,Litva",  # international countries
            now,
        )

        cur.execute(
            "INSERT INTO branches (name, address, latitude, longitude, phone, working_hours, is_active, delivery_radius, accepts_international, international_countries, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            main_branch,
        )

        # Set as the main branch in settings
        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)",
            ("main_branch_id", "1", "Asosiy filial ID raqami"),
        )

        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)",
            ("international_delivery", "1", "Xalqaro yetkazib berish yoqilgan"),
        )

        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)",
            ("accepts_russia_orders", "1", "Rossiyadan buyurtma qabul qilish"),
        )

        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)",
            ("working_hours", "9:00 - 18:00", "Ish vaqti"),
        )

        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value, description) VALUES (?, ?, ?)",
            ("address_coordinates", "41.236832,69.203578", "Manzil koordinatalari"),
        )

    # Payment Cards jadvali - superadmin tomonidan boshqariladigan to'lov kartalari
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT NOT NULL,
            card_number TEXT NOT NULL,
            card_holder_name TEXT NOT NULL,
            bank_name TEXT,
            card_type TEXT DEFAULT 'visa',  -- visa, mastercard, uzcard, humo
            is_active BOOLEAN DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_by INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (created_by) REFERENCES staff (id)
        );
    """
    )

    # Boshlang'ich to'lov kartalarini qo'shish
    cur.execute("SELECT COUNT(*) FROM payment_cards")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        sample_cards = [
            (
                "Asosiy UzCard",
                "8600 **** **** 1234",
                "JOHN DOE",
                "Milliy bank",
                "uzcard",
                1,
                1,
                1,
                now,
                now,
            ),
            (
                "Humo karta",
                "9860 **** **** 5678",
                "JANE SMITH",
                "Xalq banki",
                "humo",
                1,
                2,
                1,
                now,
                now,
            ),
            (
                "Visa karta",
                "4111 **** **** 9876",
                "ALICE JOHNSON",
                "Toshkent shahar banki",
                "visa",
                1,
                3,
                1,
                now,
                now,
            ),
        ]
        cur.executemany(
            "INSERT INTO payment_cards (card_name, card_number, card_holder_name, bank_name, card_type, is_active, display_order, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sample_cards,
        )

    conn.commit()
    conn.close()

    # Card payment settings table - for superadmin management
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS card_payment_settings (
            id INTEGER PRIMARY KEY,
            card_number TEXT NOT NULL,
            card_name TEXT NOT NULL,
            click_qr_url TEXT,
            payme_qr_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """
    )
    conn.commit()
    conn.close()

    # 360 degree photos table
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS photos_360 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            image_url TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """
    )
    conn.commit()
    conn.close()

    # Sessions table for active session tracking
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            ip TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()

    # Chats and notifications tables
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            is_group BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            member_type TEXT NOT NULL, -- 'user'|'staff'|'courier'|'super'
            member_id INTEGER, -- NULL for system or broadcast
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender_type TEXT NOT NULL,
            sender_id INTEGER,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        );
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_type TEXT NOT NULL,
            recipient_id INTEGER,
            sender_type TEXT DEFAULT 'system',
            sender_id INTEGER,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            read_flag INTEGER DEFAULT 0,
            notification_type TEXT DEFAULT 'general'
        );
    """
    )

    # Add missing columns if they don't exist
    try:
        cur.execute("PRAGMA table_info(notifications);")
        cols = [r[1] for r in cur.fetchall() or []]
        if "sender_type" not in cols:
            cur.execute(
                "ALTER TABLE notifications ADD COLUMN sender_type TEXT DEFAULT 'system'"
            )
        if "sender_id" not in cols:
            cur.execute("ALTER TABLE notifications ADD COLUMN sender_id INTEGER")
        if "notification_type" not in cols:
            cur.execute(
                "ALTER TABLE notifications ADD COLUMN notification_type TEXT DEFAULT 'general'"
            )
    except Exception:
        # If anything goes wrong here, continue — other code paths also ensure schema.
        pass
    conn.commit()
    conn.close()


def ensure_orders_columns():
    "Orders jadvaliga kerakli ustunlarni qo'shadi (migration)."
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(orders);")
        cols = [r[1] for r in cur.fetchall()]

        if "status" not in cols:
            cur.execute(
                "ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'waiting';"
            )
            conn.commit()

        if "user_id" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER;")
            conn.commit()

        if "delivery_address" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_address TEXT;")
            conn.commit()

        if "delivery_distance" not in cols:
            cur.execute(
                "ALTER TABLE orders ADD COLUMN delivery_distance REAL DEFAULT 0;"
            )
            conn.commit()

        if "delivery_price" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_price REAL DEFAULT 0;")
            conn.commit()

        if "customer_phone" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT;")
            conn.commit()

        if "card_number" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN card_number TEXT;")
            conn.commit()

        if "courier_id" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_id INTEGER;")
            conn.commit()

        if "order_type" not in cols:
            cur.execute(
                "ALTER TABLE orders ADD COLUMN order_type TEXT NOT NULL DEFAULT 'dine_in';"
            )
            conn.commit()

        if "delivery_latitude" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_latitude REAL;")
            conn.commit()

        if "delivery_longitude" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_longitude REAL;")
            conn.commit()

        if "courier_delivery_time" not in cols:
            cur.execute(
                "ALTER TABLE orders ADD COLUMN courier_delivery_time INTEGER DEFAULT 30;"
            )
            conn.commit()

        if "delivery_map_url" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_map_url TEXT;")
            conn.commit()

        if "customer_note" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_note TEXT;")
            conn.commit()

        if "courier_price" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_price REAL DEFAULT 0;")
            conn.commit()

        if "courier_delivery_minutes" not in cols:
            cur.execute(
                "ALTER TABLE orders ADD COLUMN courier_delivery_minutes INTEGER DEFAULT 0;"
            )
            conn.commit()

        if "branch_id" not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN branch_id INTEGER DEFAULT 1;")
            conn.commit()

    except Exception as e:
        app_logger.error(f"Orders jadval migration xatoligi: {str(e)}")
        logging.error(f"Orders jadval migration xatoligi: {str(e)}")
    finally:
        conn.close()


def ensure_users_columns():
    "Users jadvaliga kerakli ustunlarni qo'shadi (migration)."
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(users);")
        cols = [r[1] for r in cur.fetchall()]

        if "address_latitude" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN address_latitude REAL;")
            conn.commit()

        if "address_longitude" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN address_longitude REAL;")
            conn.commit()

        if "interface_language" not in cols:
            cur.execute(
                "ALTER TABLE users ADD COLUMN interface_language TEXT DEFAULT 'uz';"
            )
            conn.commit()

        if "font_size" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN font_size TEXT DEFAULT 'medium';")
            conn.commit()

        if "dark_theme" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN dark_theme BOOLEAN DEFAULT 1;")
            conn.commit()

    except Exception as e:
        app_logger.warning(f"Users jadval migratsiyasi xatoligi: {str(e)}")
    finally:
        conn.close()


def ensure_receipts_columns():
    """Ensure receipts table has expected columns (migration helper)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(receipts);")
        cols = [r[1] for r in cur.fetchall()]
        if "total_amount" not in cols:
            # Add the column with default 0.0 to avoid queries failing
            cur.execute(
                "ALTER TABLE receipts ADD COLUMN total_amount REAL DEFAULT 0.0;"
            )
            conn.commit()
            app_logger.info("Added missing total_amount column to receipts table")
    except Exception as e:
        app_logger.warning(f"Receipts migration warning: {str(e)}")
    finally:
        conn.close()


def ensure_cart_items_columns():
    "Cart_items jadvaliga user_id ustunini qo'shadi va session_id ni optional qiladi (migration)."
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(cart_items);")
        cols = [r[1] for r in cur.fetchall()]
        if "user_id" not in cols:
            cur.execute("ALTER TABLE cart_items ADD COLUMN user_id INTEGER;")
            conn.commit()

        # Add size and color columns if missing so selected options are persisted
        if "size" not in cols:
            try:
                cur.execute("ALTER TABLE cart_items ADD COLUMN size TEXT;")
                conn.commit()
            except Exception:
                pass

        if "color" not in cols:
            try:
                cur.execute("ALTER TABLE cart_items ADD COLUMN color TEXT;")
                conn.commit()
            except Exception:
                pass

        # Eski jadval strukturasini yangilash - session_id ni NULL qilib qo'yish
        cur.execute(
            "UPDATE cart_items SET session_id = 'temp_session' WHERE session_id IS NULL OR session_id = ''"
        )
        conn.commit()
    except Exception as e:
        app_logger.warning(f"Cart items jadval migratsiyasi xatoligi: {str(e)}")
    finally:
        conn.close()


def ensure_staff_columns():
    "Staff jadvaliga kerakli ustunlarni qo'shadi (migration)."
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(staff);")
        cols = [r[1] for r in cur.fetchall()]

        if "passport_series" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN passport_series TEXT;")
            conn.commit()

        if "passport_number" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN passport_number TEXT;")
            conn.commit()

        if "total_hours" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN total_hours REAL DEFAULT 0;")
            conn.commit()

        if "orders_handled" not in cols:
            cur.execute(
                "ALTER TABLE staff ADD COLUMN orders_handled INTEGER DEFAULT 0;"
            )
            conn.commit()

        if "last_activity" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN last_activity TEXT;")
            conn.commit()

        app_logger.info("Staff table migration completed successfully")

    except Exception as e:
        app_logger.warning(f"Staff jadval migratsiyasi xatoligi: {str(e)}")
    finally:
        conn.close()


def ensure_courier_columns():
    "Courier jadvaliga kerakli ustunlarni qo'shadi (migration)."
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(couriers);")
        cols = [r[1] for r in cur.fetchall()]

        if "passport_series" not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN passport_series TEXT;")
            conn.commit()

        if "passport_number" not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN passport_number TEXT;")
            conn.commit()

        if "total_hours" not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN total_hours REAL DEFAULT 0;")
            conn.commit()

        if "deliveries_completed" not in cols:
            cur.execute(
                "ALTER TABLE couriers ADD COLUMN deliveries_completed INTEGER DEFAULT 0;"
            )
            conn.commit()

        if "last_activity" not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN last_activity TEXT;")
            conn.commit()

    except Exception as e:
        app_logger.warning(f"Courier jadval migratsiyasi xatoligi: {str(e)}")
    finally:
        conn.close()


def ensure_menu_items_columns():
    "Menu_items jadvaliga kerakli ustunlarni qo'shadi (migration)."
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(menu_items);")
        cols = [r[1] for r in cur.fetchall()]

        # Kerakli ustunlarni qo'shish
        columns_to_add = [
            ("description", "TEXT"),
            ("image_url", "TEXT"),
            ("available", "BOOLEAN DEFAULT 1"),
            ("stock_quantity", "INTEGER DEFAULT 0"),
            ("orders_count", "INTEGER DEFAULT 0"),
            ("rating", "REAL DEFAULT 0.0"),
            ("discount_percentage", "REAL DEFAULT 0.0"),
            ("sizes", "TEXT"),
            ("colors", "TEXT"),
            ("created_at", "TEXT"),
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in cols:
                try:
                    cur.execute(
                        f"ALTER TABLE menu_items ADD COLUMN {col_name} {col_type};"
                    )
                    conn.commit()
                    app_logger.info(f"Menu_items jadvaliga {col_name} ustuni qo'shildi")
                except Exception as col_error:
                    app_logger.warning(
                        f"Menu_items jadvaliga {col_name} ustunini qo'shishda xatolik: {str(col_error)}"
                    )

        # Ensure order_details has size/color columns when order_details table exists
        try:
            cur.execute("PRAGMA table_info(order_details);")
            od_cols = [r[1] for r in cur.fetchall()]
            if "size" not in od_cols:
                try:
                    cur.execute("ALTER TABLE order_details ADD COLUMN size TEXT;")
                    conn.commit()
                except Exception:
                    pass
            if "color" not in od_cols:
                try:
                    cur.execute("ALTER TABLE order_details ADD COLUMN color TEXT;")
                    conn.commit()
                except Exception:
                    pass
        except Exception:
            # If order_details doesn't exist yet, ignore
            pass

    except Exception as e:
        app_logger.error(f"Menu items migration xatoligi: {str(e)}")
    finally:
        if conn:
            conn.close()


def ensure_ratings_columns():
    """Ensure ratings table has branch_id column and a schema that supports branch ratings.

    If the existing ratings table lacks branch_id or has menu_item_id NOT NULL, perform a safe
    table rebuild: create a new table with menu_item_id nullable and branch_id column, copy data,
    then replace the old table.
    """
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(ratings);")
        cols_info = cur.fetchall() or []
        cols = [r[1] for r in cols_info]

        need_rebuild = False
        if "branch_id" not in cols:
            need_rebuild = True
        else:
            # If menu_item_id currently has NOT NULL constraint, rebuild to allow NULL
            for r in cols_info:
                if r[1] == "menu_item_id":
                    # PRAGMA table_info fields: cid, name, type, notnull, dflt_value, pk
                    if r[3] == 1:
                        need_rebuild = True
                    break

        if not need_rebuild:
            return

        app_logger.info(
            "Rebuilding ratings table to add branch_id and allow NULL menu_item_id"
        )

        # Read existing rows
        cur.execute(
            "SELECT id, user_id, menu_item_id, rating, comment, created_at FROM ratings"
        )
        existing = cur.fetchall() or []

        # Start migration in a transaction
        cur.execute("BEGIN TRANSACTION;")

        # Create new table with desired schema
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                menu_item_id INTEGER,
                branch_id INTEGER,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id),
                UNIQUE(user_id, menu_item_id, branch_id)
            );
            """
        )

        # Copy existing rows into new table (branch_id NULL)
        for row in existing:
            rid = row[0]
            uid = row[1]
            mid = row[2]
            rating_val = row[3]
            comment = row[4]
            created_at = row[5]
            cur.execute(
                "INSERT INTO ratings_new (id, user_id, menu_item_id, branch_id, rating, comment, created_at) VALUES (?, ?, ?, NULL, ?, ?, ?)",
                (rid, uid, mid, rating_val, comment, created_at),
            )

        # Drop old table and rename new one
        cur.execute("DROP TABLE IF EXISTS ratings;")
        cur.execute("ALTER TABLE ratings_new RENAME TO ratings;")

        conn.commit()
        app_logger.info("Ratings table migration completed")

    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except:
            pass
        app_logger.error(f"Ratings table migration failed: {str(e)}")
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def cleanup_expired_orders():
    "Waiting holatidagi, 30 daqiqadan oshgan buyurtmalarni cancelled ga o'tkazadi."
    try:
        # Connection pool dan connection olish
        with db_pool.get_connection() as conn:
            cur = conn.cursor()
            cutoff = (get_current_time() - datetime.timedelta(minutes=30)).isoformat()
            cur.execute(
                "UPDATE orders SET status='cancelled' WHERE status='waiting' AND created_at < ?",
                (cutoff,),
            )
            conn.commit()
    except Exception as e:
        app_logger.error(f"Expired orders cleanup failed: {str(e)}")


def send_birthday_notifications(run_date=None):
    """Find users, staff, couriers with birthday on run_date and send them a notification.

    This function is safe to run multiple times; it will not duplicate notifications for the same recipient on the same day.
    """
    try:
        run_date = run_date or get_current_time().date()
        month_day = run_date.strftime("-%m-%d")

        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # users
            cur.execute(
                "SELECT id, first_name, last_name, email FROM users WHERE substr(birth_date,6) = ?",
                (month_day,),
            )
            users = cur.fetchall() or []

            # staff
            cur.execute(
                "SELECT id, first_name, last_name FROM staff WHERE substr(birth_date,6) = ?",
                (month_day,),
            )
            staffers = cur.fetchall() or []

            # couriers
            cur.execute(
                "SELECT id, first_name, last_name FROM couriers WHERE substr(birth_date,6) = ?",
                (month_day,),
            )
            couriers = cur.fetchall() or []

            # helper to insert targeted notification if not already sent today
            def _insert_if_not_sent(recipient_type, recipient_id, title, body):
                try:
                    today_iso = run_date.isoformat()
                    # Check duplicates: same recipient, same title, same day
                    q = "SELECT id FROM notifications WHERE recipient_type=? AND recipient_id=? AND DATE(created_at)=? AND title=?"
                    cur.execute(q, (recipient_type, recipient_id, today_iso, title))
                    if cur.fetchone():
                        return
                    cur.execute(
                        "INSERT INTO notifications (recipient_type, recipient_id, sender_id, title, body, created_at, read_flag) VALUES (?, ?, ?, ?, ?, ?, 0)",
                        (
                            recipient_type,
                            recipient_id,
                            None,
                            title,
                            body,
                            datetime.datetime.now().isoformat(),
                        ),
                    )
                except Exception as ie:
                    app_logger.warning(
                        f"Failed to insert birthday notification: {str(ie)}"
                    )

            for u in users:
                uid = u[0] if isinstance(u, (list, tuple)) else u.get("id")
                name = (
                    (u[1] + " " + u[2])
                    if len(u) > 2
                    else (u.get("first_name") + " " + u.get("last_name", ""))
                )
                title = "Tug'ilgan kun muborak!"
                body = f"{name}, Sizni tug'ilgan kuningiz bilan tabriklaymiz!"
                _insert_if_not_sent("users", uid, title, body)

            for s in staffers:
                sid = s[0] if isinstance(s, (list, tuple)) else s.get("id")
                name = (
                    (s[1] + " " + s[2])
                    if len(s) > 2
                    else (s.get("first_name") + " " + s.get("last_name", ""))
                )
                title = "Tug'ilgan kun muborak!"
                body = f"{name}, Sizni tug'ilgan kuningiz bilan tabriklaymiz!"
                _insert_if_not_sent("staff", sid, title, body)

            for c in couriers:
                cid = c[0] if isinstance(c, (list, tuple)) else c.get("id")
                name = (
                    (c[1] + " " + c[2])
                    if len(c) > 2
                    else (c.get("first_name") + " " + c.get("last_name", ""))
                )
                title = "Tug'ilgan kun muborak!"
                body = f"{name}, Sizni tug'ilgan kuningiz bilan tabriklaymiz!"
                _insert_if_not_sent("couriers", cid, title, body)

            conn.commit()
    except Exception as e:
        app_logger.error(f"send_birthday_notifications error: {str(e)}")


# ---------- Routes ----------
# Manual fix for missing staff total_hours column
def fix_staff_table():
    "Manual fix for staff table missing columns"
    try:
        conn = get_db()
        cur = conn.cursor()

        # Check if total_hours exists
        cur.execute("PRAGMA table_info(staff);")
        cols = [r[1] for r in cur.fetchall()]

        if "total_hours" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN total_hours REAL DEFAULT 0.0;")
            conn.commit()
            app_logger.info("Added missing total_hours column to staff table")

        conn.close()
    except Exception as e:
        app_logger.error(f"Failed to fix staff table: {str(e)}")


# Manual fix for staff table - add role column
def fix_staff_role_table():
    "Add role column to staff table and create super admin"
    try:
        conn = get_db()
        cur = conn.cursor()

        # Check if role column exists
        cur.execute("PRAGMA table_info(staff);")
        cols = [r[1] for r in cur.fetchall()]

        if "role" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN role TEXT DEFAULT 'staff';")
            conn.commit()
            app_logger.info("Added role column to staff table")

        # Check if login column exists
        if "login" not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN login TEXT;")
            conn.commit()
            app_logger.info("Added login column to staff table")

        # Create super admin if doesn't exist
        cur.execute("SELECT COUNT(*) FROM staff WHERE role = 'super_admin'")
        if cur.fetchone()[0] == 0:
            now = get_current_time().isoformat()
            password_hash = generate_password_hash("admin123")
            cur.execute(
                "INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, role, login, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "Super",
                    "Admin",
                    "1990-01-01",
                    "+998901234567",
                    "AA",
                    "1234567",
                    password_hash,
                    "super_admin",
                    "admin",
                    now,
                ),
            )
            conn.commit()
            app_logger.info("Created super admin user: login=admin, password=admin123")
            print("Super admin yaratildi: login=admin, password=admin123")

        conn.close()
    except Exception as e:
        app_logger.error(f"Failed to fix staff role table: {str(e)}")


# Manual fix for news table
def fix_news_table():
    "Create news table if not exists and reset sample data with correct images"
    try:
        conn = get_db()
        cur = conn.cursor()

        # Create news table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT NOT NULL DEFAULT 'news',
                image_url TEXT,
                video_url TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # Check and fix sample data with wrong image paths
        cur.execute(
            "SELECT COUNT(*) FROM news WHERE image_url LIKE '%spring-collection.jpg%' OR image_url LIKE '%payment-methods.jpg%'"
        )
        wrong_images_count = cur.fetchone()[0]

        if wrong_images_count > 0:
            # Update wrong image paths
            cur.execute(
                "UPDATE news SET image_url = '/static/images/default-men.jpg' WHERE image_url = '/static/images/spring-collection.jpg'"
            )
            cur.execute(
                "UPDATE news SET image_url = '/static/images/default-product.jpg' WHERE image_url = '/static/images/payment-methods.jpg'"
            )
            conn.commit()
            app_logger.info(
                f"Fixed {wrong_images_count} news items with wrong image paths"
            )
            print(f"{wrong_images_count} ta yangilik rasmiy yo'llari tuzatildi")

        # Add sample news if table is empty
        cur.execute("SELECT COUNT(*) FROM news")
        if cur.fetchone()[0] == 0:
            now = get_current_time().isoformat()
            sample_news = [
                (
                    "🎉 Yangi kolleksiya!",
                    "Bahorgi yangi oyoq kiyimlar kolleksiyasi do'konimizga keldi! 50% gacha chegirmalar.",
                    "advertisement",
                    "/static/images/default-men.jpg",
                    None,
                    1,
                    1,
                    1,
                    now,
                    now,
                ),
                (
                    "🚚 Bepul yetkazib berish",
                    "Endi 300,000 so'mdan yuqori xaridlar uchun bepul yetkazib berish xizmati!",
                    "news",
                    None,
                    None,
                    1,
                    2,
                    1,
                    now,
                    now,
                ),
                (
                    "⭐ Mijozlar bahosi",
                    "Do'konimiz 4.8/5 bahoga ega bo'ldi. Rahmat barcha mijozlarimizga!",
                    "news",
                    None,
                    None,
                    1,
                    3,
                    1,
                    now,
                    now,
                ),
                (
                    "💳 Click va Payme orqali to'lov",
                    "Endi sizlar uchun yanada qulay - Click va Payme orqali to'lov imkoni!",
                    "advertisement",
                    "/static/images/default-product.jpg",
                    None,
                    1,
                    4,
                    1,
                    now,
                    now,
                ),
            ]
            cur.executemany(
                "INSERT INTO news (title, content, type, image_url, video_url, is_active, display_order, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                sample_news,
            )
            conn.commit()
            app_logger.info("Added sample news data")
            print("Namuna yangiliklar qo'shildi")

        conn.close()
    except Exception as e:
        app_logger.error(f"Failed to fix news table: {str(e)}")


# Manual fix for courier table
def fix_courier_table():
    "Manual fix for courier table missing columns"
    try:
        conn = get_db()
        cur = conn.cursor()

        # Check courier table columns
        cur.execute("PRAGMA table_info(couriers);")
        cols = [r[1] for r in cur.fetchall()]

        if "total_hours" not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN total_hours REAL DEFAULT 0.0;")
            conn.commit()
            app_logger.info("Added missing total_hours column to couriers table")

        if "deliveries_completed" not in cols:
            cur.execute(
                "ALTER TABLE couriers ADD COLUMN deliveries_completed INTEGER DEFAULT 0;"
            )
            conn.commit()
            app_logger.info(
                "Added missing deliveries_completed column to couriers table"
            )

        conn.close()
    except Exception as e:
        app_logger.error(f"Failed to fix courier table: {str(e)}")


def safe_init_database():
    """Safe DB initialization helper used during startup.

    Tries to run init_db(); on failure, attempts a minimal fallback to ensure the app
    can start and surface a clearer error.
    """
    try:
        app_logger.info("Ma'lumotlar bazasini ishga tushirish boshlandi...")
        init_db()
        app_logger.info("Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")
        return True
    except Exception as e:
        app_logger.error(f"Ma'lumotlar bazasini ishga tushirishda xatolik: {str(e)}")
        try:
            # Fallback - ensure DB file exists with a minimal table so the app can run
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _app_health_check (id INTEGER PRIMARY KEY)"
            )
            conn.commit()
            conn.close()
            app_logger.warning("Ma'lumotlar bazasi qisman ishga tushirildi")
            return False
        except Exception as fallback_error:
            app_logger.critical(
                f"Ma'lumotlar bazasi fallback ham ishlamadi: {str(fallback_error)}"
            )
            return False


if not os.environ.get("SKIP_DB_INIT"):
    # Ensure columns exist on startup
    ensure_orders_columns()
    ensure_cart_items_columns()
    ensure_staff_columns()
    ensure_courier_columns()
    ensure_menu_items_columns()
    ensure_ratings_columns()
    ensure_users_columns()

    # Apply manual fixes
    fix_staff_table()
    fix_courier_table()
    fix_news_table()
    ensure_receipts_columns()

    # Database ni xavfsiz ishga tushirish
    with app.app_context():
        try:
            safe_init_database()
        except Exception as init_error:
            app_logger.error(
                f"App context da database initialization xatoligi: {str(init_error)}"
            )


# --- Inject role-based nav and show_nav flag for templates ---
@app.context_processor
def inject_role_nav():
    """
    Provide role_nav and show_nav for templates.
    show_nav = False for login/register routes so auth pages can hide global navbar.
    """
    try:
        endpoint = (request.endpoint or "").split(".")[-1]
        auth_endpoints = {
            "login",
            "login_page",
            "register",
            "staff_login",
            "courier_login",
            "super_admin_login",
            "staff_register",
            "courier_register",
        }
        show_nav = endpoint not in auth_endpoints and not request.path.startswith(
            "/static/"
        )

        # base context values available in all templates
        base_ctx = {
            "csrf_token": generate_csrf_token(),
            "session_dark_theme": bool(session.get("dark_theme", True)),
            "session_font_size": session.get("font_size", "medium"),
            "session_language": session.get("interface_language", "uz"),
            "show_nav": show_nav,
        }

        is_courier = bool(session.get("courier_id"))
        is_staff = bool(session.get("staff_id"))
        is_super = bool(session.get("super_admin"))
        is_user = bool(session.get("user_id"))

        # Prefer super admin role if present even when other session flags exist
        if is_super:
            base_ctx.update(
                {
                    "role_nav": [
                        {"label": "Dashboard", "endpoint": "super_admin_dashboard"},
                        {"label": "Analytics", "endpoint": "super_admin_analytics"},
                        {"label": "Reports", "endpoint": "super_admin_reports"},
                        {"label": "System", "endpoint": "super_admin_system"},
                        {"label": "Profil", "endpoint": "super_admin_logout"},
                    ],
                    "role_name": "super_admin",
                    "is_courier": False,
                    "is_staff": False,
                    "is_super_admin": True,
                    "is_user": False,
                }
            )
            return base_ctx

        if is_courier:
            base_ctx.update(
                {
                    "role_nav": [
                        {"label": "Dashboard", "endpoint": "courier_dashboard"},
                        {
                            "label": "Hisobot",
                            "endpoint": "super_admin_get_performance_stats",
                        },
                        {"label": "Xarita", "endpoint": "courier_dashboard"},
                        {"label": "Info", "endpoint": "contact"},
                        {"label": "Contact", "endpoint": "contact"},
                        {"label": "Profil", "endpoint": "courier_logout"},
                    ],
                    "role_name": "courier",
                    "is_courier": True,
                    "is_staff": False,
                    "is_super_admin": False,
                    "is_user": False,
                }
            )
            return base_ctx

        if is_staff:
            base_ctx.update(
                {
                    "role_nav": [
                        {"label": "Dashboard", "endpoint": "staff_dashboard"},
                        {"label": "Buyurtmalar", "endpoint": "staff_dashboard"},
                        {"label": "Hisobot", "endpoint": "api_super_admin_reports"},
                        {"label": "Profil", "endpoint": "staff_logout"},
                        {"label": "Contact", "endpoint": "contact"},
                    ],
                    "role_name": "staff",
                    "is_courier": False,
                    "is_staff": True,
                    "is_super_admin": False,
                    "is_user": False,
                }
            )
            return base_ctx

        # default user nav (visible on non-auth pages)
        base_ctx.update(
            {
                "role_nav": [
                    {"label": "Menyu", "endpoint": "menu"},
                    {"label": "Buyurtmalar", "endpoint": "user_page"},
                    {"label": "Kontakt", "endpoint": "contact"},
                    {"label": "Profil", "endpoint": "profile"},
                ],
                "role_name": "user",
                "is_courier": False,
                "is_staff": False,
                "is_super_admin": False,
                "is_user": is_user,
            }
        )
        return base_ctx
    except Exception:
        return {
            "role_nav": [],
            "role_name": None,
            "is_courier": False,
            "is_staff": False,
            "is_super_admin": False,
            "is_user": False,
            "show_nav": True,
            "csrf_token": generate_csrf_token(),
            "session_dark_theme": True,
            "session_font_size": "medium",
            "session_language": "uz",
        }


# ---- Simple i18n loader -------------------------------------------------
# Loads JSON files from static/locales/<lang>.json and provides a Jinja helper
SUPPORTED_LANGUAGES = ["uz", "ru", "en", "kk", "zh"]
LOCALES = {}


def load_locales():
    """Load locale JSON files into LOCALES dict. Missing files produce empty dicts."""
    global LOCALES
    base = os.path.join(app.root_path, "static", "locales")
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join(base, f"{lang}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                LOCALES[lang] = json.load(f)
        except Exception:
            LOCALES[lang] = {}


# load once at startup (safe if files missing)
try:
    load_locales()
except Exception:
    LOCALES = {ln: {} for ln in SUPPORTED_LANGUAGES}


def translate(key, **kwargs):
    """Translate a key using session['interface_language'] with graceful fallbacks.

    Usage in templates: {{ _('settings.title') }}
    """
    lang = session.get("interface_language", "uz")
    # prefer requested lang -> uz -> en -> raw key
    candidates = [lang, "uz", "en"]
    for c in candidates:
        bucket = LOCALES.get(c, {})
        if key in bucket:
            val = bucket.get(key)
            try:
                return val.format(**kwargs) if isinstance(val, str) else val
            except Exception:
                return val
    # fallback to key if nothing found
    return key


# Load optional message->key mapping for existing flash strings so we can
# automatically translate legacy literal messages without changing every
# flash(...) callsite.
MSG_KEY_MAP = {}
try:
    msg_map_path = os.path.join(app.root_path, "static", "locales", "msg_key_map.json")
    if os.path.exists(msg_map_path):
        with open(msg_map_path, "r", encoding="utf-8") as f:
            MSG_KEY_MAP = json.load(f)
except Exception:
    MSG_KEY_MAP = {}


@app.before_request
def localize_flashes():
    """Remap any flashed literal messages into translated strings using
    MSG_KEY_MAP and translate(). This lets us keep existing flash(...) calls
    and have their text localized automatically.
    """
    try:
        # get current flashed messages (consumes them)
        messages = get_flashed_messages(with_categories=True)
        if not messages:
            return
        # re-flash localized versions
        for category, msg in messages:
            # If mapping exists, use translation key; else try to find key by value
            key = MSG_KEY_MAP.get(msg)
            if key:
                localized = translate(key) if isinstance(key, str) else translate(msg)
            else:
                # As a fallback, try to treat the msg itself as a translation key
                localized = translate(msg)
            # re-flash localized message in same category
            flash(localized, category)
    except Exception:
        # don't break the request flow on localization errors
        pass


@app.context_processor
def inject_translations():
    """Expose translation helper and current language to templates."""
    return {
        "_": translate,
        "supported_languages": SUPPORTED_LANGUAGES,
        "current_language": session.get("interface_language", "uz"),
    }


# ---------- Helpers ----------


def next_ticket_no(conn):
    try:
        cur = conn.cursor()
        cur.execute("UPDATE counters SET value = value + 1 WHERE name = 'ticket';")
        cur.execute("SELECT value FROM counters WHERE name = 'ticket';")
        result = cur.fetchone()
        return result[0] if result else 10001  # Default value if something goes wrong
    except Exception as e:
        app_logger.error(f"Failed to get next ticket number: {str(e)}")
        return 10001  # Default value in case of error


def waiting_position(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting';")
        result = cur.fetchone()
        return result[0] if result else 0
    except Exception as e:
        app_logger.error(f"Failed to get waiting position: {str(e)}")
        return 0


def calc_eta_minutes(conn):
    # navbatdagi pozitsiya bo'yicha ETA ni hisoblash
    position = waiting_position(conn)  # sizdan oldingi kutayotganlar soni
    eta_minutes = (position + 1) * AVG_PREP_MINUTES
    return eta_minutes


def get_user_queue_position(conn, ticket_no):
    # Foydalanuvchining navbatdagi o'rni
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM orders
            WHERE status='waiting' AND created_at < (
                SELECT created_at FROM orders WHERE ticket_no=? AND status='waiting'
            )
        """,
            (ticket_no,),
        )
        result = cur.fetchone()
        return result[0] + 1 if result else 0
    except Exception as e:
        app_logger.error(
            f"Failed to get user queue position for ticket {ticket_no}: {str(e)}"
        )
        return 0


def fmt_time(dt):
    return dt.strftime("%H:%M")


def search_location_with_serper(query, gl="uz", hl="uz"):
    "Serper API orqali joylashuvlarni qidirish"
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": Config.SERPER_API_KEY,  # Config dan API kalitini olish
            "Content-Type": "application/json",
        }
        data = {"q": query, "gl": gl, "hl": hl}

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            app_logger.error(
                f"Serper API search error: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        app_logger.error(f"Serper API xatoligi: {e}")
        return None


def get_places_with_serper(query, gl="uz", hl="uz"):
    "Serper API orqali Google Places ma'lumotlarini olish"
    try:
        url = "https://google.serper.dev/places"
        headers = {
            "X-API-KEY": Config.SERPER_API_KEY,  # Config dan API kalitini olish
            "Content-Type": "application/json",
        }
        data = {"q": query, "gl": gl, "hl": hl}

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            app_logger.error(
                f"Serper API places error: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        app_logger.error(f"Serper Places API xatoligi: {e}")
        return None


def validate_delivery_address(address):
    "Yetkazib berish manzilini tekshirish Yandex API orqali"
    if not address:
        return False, "Manzil kiritilmagan"

    # Yandex API kaliti mavjudligini tekshirish
    if not app.config["YANDEX_GEOCODER_API"]:
        app_logger.warning(
            "Yandex Geocoding API kaliti belgilanmagan. Manzil tekshiruvi cheklangan."
        )
        # Agar API kaliti bo'lmasa, oddiy tekshiruv
        if len(address) > 5 and any(
            word in address.lower()
            for word in ["ko'cha", "mahalla", "tuman", "shoh", "yo'l"]
        ):
            return True, "Manzil qabul qilindi (API kaliti yo'q)"
        else:
            return False, "Manzilni to'liqroq kiriting (API kaliti yo'q)"

    try:
        # Yandex Geocoding API orqali manzilni tekshirish
        geocoding_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": app.config["YANDEX_GEOCODER_API"],
            "geocode": f"{address}, Toshkent, O'zbekiston",
            "format": "json",
            "results": 1,
        }

        response = requests.get(geocoding_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Natijalarni tekshirish
            geo_objects = (
                data.get("response", {})
                .get("GeoObjectCollection", {})
                .get("featureMember", [])
            )

            if geo_objects:
                return True, "Manzil topildi"
            else:
                return False, "Manzil topilmadi"
        else:
            app_logger.error(
                f"Yandex Geocoding API error: {response.status_code} - {response.text}"
            )
            # API ishlamasa, oddiy tekshirish
            if len(address) > 5 and any(
                word in address.lower()
                for word in ["ko'cha", "mahalla", "tuman", "shoh", "yo'l"]
            ):
                return True, "Manzil qabul qilindi (API xatosi)"
            else:
                return False, "Manzilni to'liqroq kiriting (API xatosi)"

    except Exception as e:
        # Xatolik bo'lsa, oddiy tekshirish
        app_logger.error(f"Manzil tekshirishda umumiy xatolik: {str(e)}")
        if len(address) > 5:
            return True, "Manzil qabul qilindi (Xatolik)"
        else:
            return False, "Manzilni to'liqroq kiriting (Xatolik)"


def calculate_delivery_distance(address):
    "Yetkazib berish masofasini hisoblash Yandex API orqali"
    # Yandex API kaliti mavjudligini tekshirish
    if not app.config["YANDEX_GEOCODER_API"]:
        app_logger.warning(
            "Yandex Geocoding API kaliti belgilanmagan. Masofa hisoblash cheklangan."
        )
        # Agar API kaliti bo'lmasa, taxminiy masofa
        return calculate_distance_fallback(address)

    try:
        # Restoran koordinatalari (Toshkent markazi)
        restaurant_coords = [41.2995, 69.2401]

        # Yandex Geocoding API orqali manzilni manzilga o'tkazish
        geocoding_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": app.config["YANDEX_GEOCODER_API"],
            "geocode": f"{address}, Toshkent, O'zbekiston",
            "format": "json",
            "results": 1,
        }

        response = requests.get(geocoding_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            geo_objects = (
                data.get("response", {})
                .get("GeoObjectCollection", {})
                .get("featureMember", [])
            )

            if geo_objects:
                # Koordinatalarni olish
                point = geo_objects[0]["GeoObject"]["Point"]["pos"].split()
                dest_coords = [float(point[1]), float(point[0])]  # lat, lng formatida

                # To'g'ri chiziq bo'yicha masofa hisoblash (Haversine formula)
                import math

                lat1, lng1 = math.radians(restaurant_coords[0]), math.radians(
                    restaurant_coords[1]
                )
                lat2, lng2 = math.radians(dest_coords[0]), math.radians(dest_coords[1])

                dlat = lat2 - lat1
                dlng = lng2 - lng1

                a = (
                    math.sin(dlat / 2) ** 2
                    + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
                )
                c = 2 * math.asin(math.sqrt(a))
                distance_km = 6371 * c  # Yer radiusi 6371 km

                return round(min(50, max(0.5, distance_km)), 1)
            else:
                # Agar Yandex API manzilni topa olmasa, fallback
                return calculate_distance_fallback(address)

        else:
            app_logger.error(
                f"Yandex Geocoding API distance error: {response.status_code} - {response.text}"
            )
            return calculate_distance_fallback(address)  # Agar API xato bersa, fallback

    except Exception as e:
        app_logger.error(f"Masofa hisoblashda umumiy xatolik: {str(e)}")
        return calculate_distance_fallback(address)  # Umumiy xatolikda fallback


def calculate_distance_fallback(address):
    "Masofa hisoblash uchun fallback funksiyasi"
    address_lower = address.lower()
    if (
        "toshkent" in address_lower
        or "алмазар" in address_lower
        or "olmazor" in address_lower
    ):
        if any(
            word in address_lower for word in ["chilonzor", "olmazor", "shayxontohur"]
        ):
            return 8.0
        elif any(word in address_lower for word in ["yunusobod", "yashnobod"]):
            return 12.0
        elif any(word in address_lower for word in ["sergeli", "bektemir"]):
            return 15.0
        else:
            return 5.0
    elif "sirdaryo" in address_lower or "jizzax" in address_lower:
        return 20.0
    elif "samarqand" in address_lower:
        return 30.0
    else:
        return 7.0  # Umumiy taxminiy qiymat


def find_nearest_branch(user_latitude, user_longitude):
    "Foydalanuvchiga eng yaqin filialni topish"
    import math

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM branches WHERE is_active = 1")
    branches_raw = cur.fetchall() or []  # Ensure branches_raw is a list
    conn.close()

    if not branches_raw:
        app_logger.warning("Hech qanday faol filial topilmadi")
        return None

    nearest_branch = None
    min_distance = float("inf")

    for branch_row in branches_raw:
        try:
            # Safe access to branch data, assuming branch_row is a dictionary-like object from fetchall
            branch = dict(branch_row)

            # Ensure coordinates and radius are valid numbers
            branch_lat = (
                float(branch.get("latitude", 0))
                if branch.get("latitude") is not None
                else 0
            )
            branch_lng = (
                float(branch.get("longitude", 0))
                if branch.get("longitude") is not None
                else 0
            )
            delivery_radius = (
                float(branch.get("delivery_radius", 15.0))
                if branch.get("delivery_radius") is not None
                else 15.0
            )

            if not branch_lat or not branch_lng:
                app_logger.warning(
                    f"Filial {branch.get('id', 'N/A')} uchun koordinatalar mavjud emas"
                )
                continue  # Skip if coordinates are missing or invalid

            # Haversine formula bilan masofa hisoblash
            lat1, lng1 = math.radians(user_latitude), math.radians(user_longitude)
            lat2, lng2 = math.radians(branch_lat), math.radians(branch_lng)

            dlat = lat2 - lat1
            dlng = lng2 - lng1

            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
            )
            c = 2 * math.asin(math.sqrt(a))
            distance = 6371 * c  # Yer radiusi 6371 km

            app_logger.info(
                f"Filial {branch.get('name', 'N/A')} masofa: {distance:.2f} km, radius: {delivery_radius} km"
            )

            # Eng yaqin filialni topish (radius ichida)
            if distance < min_distance and distance <= delivery_radius:
                min_distance = distance
                nearest_branch = {"branch": branch, "distance": round(distance, 2)}
        except (ValueError, TypeError, KeyError, IndexError) as e:
            app_logger.warning(
                f"Filial ma'lumotlarini qayta ishlashda xatolik (ID: {branch_row.get('id', 'N/A')}): {str(e)}"
            )
            continue  # Skip this branch if error occurs

    if nearest_branch:
        app_logger.info(
            f"Eng yaqin filial topildi: {nearest_branch['branch']['name']} - {nearest_branch['distance']} km"
        )
    else:
        app_logger.warning(
            f"Foydalanuvchi joylashuvi ({user_latitude}, {user_longitude}) uchun yetkazish radiusida filial topilmadi"
        )

    return nearest_branch


def calculate_delivery_cost_and_time(distance_km):
    "Masofa bo'yicha yetkazib berish narxi va vaqtini hisoblash"
    # 1 km uchun 10000 so'm, 2 km uchun 20000 so'm
    base_price = 10000
    price = distance_km * base_price

    # 1 km taxminan 10 daqiqada
    delivery_time_minutes = max(10, int(distance_km * 10))

    return round(price), delivery_time_minutes


def auto_calculate_courier_delivery_price(distance_km):
    "Kuryer uchun avtomatik yetkazish narxini hisoblash"
    # Asosiy narx: 1 km uchun 8000 so'm
    base_rate = 8000

    # Masofa bo'yicha narx hisoblash
    distance_price = distance_km * base_rate

    # Minimum narx 15000 so'm
    minimum_price = 15000

    # Maksimum narx 50000 so'm (juda uzoq masofalar uchun)
    maximum_price = 50000

    # Yakuniy narx
    final_price = max(minimum_price, min(distance_price, maximum_price))

    # Yetkazish vaqti: 1 km = 8 daqiqa (shahar trafigi hisobga olingan)
    delivery_time = max(15, int(distance_km * 8))

    return round(final_price), delivery_time


def get_branch_average_rating(branch_id):
    "Filial uchun o'rtacha bahoni hisoblash"
    try:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Filial uchun berilgan baholarni olish (menu_item_id = -branch_id)
            cur.execute(
                """
                SELECT AVG(CAST(rating AS REAL)) as avg_rating, COUNT(*) as total_ratings
                FROM ratings
                WHERE menu_item_id = ?
            """,
                (-branch_id,),
            )

            result = cur.fetchone()

            if result and result[0] is not None:
                # Xavfsiz type conversion
                try:
                    avg_rating = float(str(result[0])) if result[0] is not None else 0.0
                    total_ratings = int(str(result[1])) if result[1] is not None else 0
                except (ValueError, TypeError):
                    avg_rating = 0.0
                    total_ratings = 0

                return {
                    "average_rating": round(avg_rating, 1),
                    "total_ratings": total_ratings,
                }

        return {"average_rating": 0.0, "total_ratings": 0}

    except Exception as e:
        app_logger.error(f"Filial bahosini hisoblashda xatolik: {str(e)}")
        return {"average_rating": 0.0, "total_ratings": 0}


def generate_qr_code(receipt_data):
    "Chek uchun QR kod yaratish"
    # Improved QR generator: supports soliq.uz style payload and multiple return formats
    # Usage: generate_qr_code(receipt_data, return_type='base64'|'data_uri'|'bytes'|'file', filename=None)
    return_type = receipt_data.pop("_return_type", None) or "base64"
    filename = receipt_data.pop("_filename", None)

    # Minimal required fields for fiscal QR (best-effort): adjust as needed for soliq.uz
    required = ["receipt_number", "total_amount", "receipt_created"]
    for f in required:
        if f not in receipt_data or not receipt_data.get(f):
            raise ValueError(f"Missing required receipt field: {f}")

    qr_data = {
        "receipt_number": str(receipt_data.get("receipt_number")),
        "total_amount": float(receipt_data.get("total_amount") or 0.0),
        "cashback_amount": float(receipt_data.get("cashback_amount") or 0.0),
        "date": str(receipt_data.get("receipt_created", ""))[:10],
        "time": str(receipt_data.get("receipt_created", ""))[11:19],
        "restaurant": receipt_data.get("restaurant", "O'zbek Milliy Taomlar Restorani"),
        "inn": receipt_data.get("inn", "123456789"),
        "cashback_percent": float(receipt_data.get("cashback_percentage", 1.0)),
    }

    # Serialize payload as compact UTF-8 JSON (Soliq format may differ; adjust if you have a spec)
    try:
        qr_text_bytes = json.dumps(qr_data, ensure_ascii=False).encode("utf-8")
    except Exception:
        # Fallback to ascii-safe serialization
        qr_text_bytes = json.dumps(qr_data, ensure_ascii=True).encode("utf-8")

    # Ensure optional libs available
    if qrcode is None:
        raise RuntimeError("qrcode library is not available")
    if base64 is None:
        raise RuntimeError("base64 module is not available")

    # Build QR image
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=getattr(qrcode.constants, "ERROR_CORRECT_L", 1),
            box_size=6,
            border=2,
        )
        qr.add_data(qr_text_bytes)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        # Ensure RGB mode for consistent PNG output
        try:
            img = img.convert("RGB")
        except Exception:
            pass

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        png_bytes = buffered.getvalue()
        b64 = base64.b64encode(png_bytes).decode("ascii")

        if return_type == "base64":
            return b64
        if return_type == "data_uri":
            return f"data:image/png;base64,{b64}"
        if return_type == "bytes":
            return png_bytes
        if return_type == "file":
            if not filename:
                filename = f"qr_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as fh:
                fh.write(png_bytes)
            return filename

        # Unknown return type: default to base64
        return b64

    except Exception as e:
        app_logger.error(f"QR generation error: {str(e)}")
        raise


def get_session_id():
    "Session ID yaratish yoki olish - yaxshilangan versiya"
    try:
        # Session mavjudligini tekshirish
        if (
            not session
            or "session_id" not in session
            or not session["session_id"]
            or session["session_id"] == "None"
        ):
            import uuid as uuid_module

            session_id = str(uuid_module.uuid4())
            session["session_id"] = session_id
            session.permanent = True  # Session ni permanent qilish

            # Session timeout belgilash
            session.permanent_session_lifetime = datetime.timedelta(days=30)

            app_logger.info(f"Yangi session yaratildi: {session_id[:8]}...")
            return session_id

        # Mavjud session ID ni validatsiya qilish
        session_id = session["session_id"]
        if len(session_id) < 10:  # UUID minimal uzunlik tekshiruvi
            import uuid as uuid_module

            new_session_id = str(uuid_module.uuid4())
            session["session_id"] = new_session_id
            app_logger.warning(
                f"Noto'g'ri session ID tuzatildi: {session_id} -> {new_session_id[:8]}..."
            )
            return new_session_id

        return session_id

    except Exception as e:
        app_logger.error(f"Session ID yaratishda xatolik: {str(e)}")
        # Fallback - oddiy UUID
        import uuid as uuid_module

        fallback_id = str(uuid_module.uuid4())
        try:
            session["session_id"] = fallback_id
            session.permanent = True
        except:
            pass  # Agar session ishlamasa ham davom etish
        return fallback_id


def get_cart_items(conn, session_id, user_id=None):
    """Savatchadagi mahsulotlarni olish - xavfsiz va size/color ni qaytaradi"""
    # If no connection passed, create new one
    if conn is None:
        conn = get_db()
        close_conn = True
    else:
        close_conn = False

    # Make rows accessible by column name
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # Validate parameters
        if not session_id and not user_id:
            app_logger.warning(
                "Neither session_id nor user_id provided to get_cart_items"
            )
            return []

        # Prepare and run the query (include ci.size and ci.color)
        query = """
            SELECT ci.id, ci.menu_item_id, mi.name, mi.price, ci.quantity,
                   ci.size, ci.color,
                   COALESCE(mi.discount_percentage, 0) as discount_percentage,
                   CASE
                       WHEN COALESCE(mi.discount_percentage, 0) > 0
                       THEN (mi.price * (100 - COALESCE(mi.discount_percentage, 0)) / 100) * ci.quantity
                       ELSE mi.price * ci.quantity
                   END as total
            FROM cart_items ci
            JOIN menu_items mi ON ci.menu_item_id = mi.id
            WHERE {where_clause} AND mi.available = 1
            ORDER BY ci.created_at DESC
        """

        if user_id:
            cur.execute(query.format(where_clause="ci.user_id = ?"), (user_id,))
        else:
            cur.execute(query.format(where_clause="ci.session_id = ?"), (session_id,))

        results = cur.fetchall()

        if not results:
            return []

        cart_items = []
        for row in results:
            try:
                item_dict = {
                    "id": row["id"],
                    "menu_item_id": row["menu_item_id"],
                    "name": row["name"],
                    "price": row["price"],
                    "quantity": row["quantity"],
                    "discount_percentage": (
                        row["discount_percentage"]
                        if row["discount_percentage"] is not None
                        else 0
                    ),
                    "size": row["size"] if "size" in row.keys() else None,
                    "color": row["color"] if "color" in row.keys() else None,
                    "total": (
                        row["total"]
                        if row["total"] is not None
                        else (row["price"] * row["quantity"])
                    ),
                }
                cart_items.append(item_dict)
            except Exception as row_error:
                app_logger.error(f"Savatcha element o'qishda xatolik: {str(row_error)}")
                # Fallback: try tuple access with conservative indices
                try:
                    item_dict = {
                        "id": row[0] if len(row) > 0 else 0,
                        "menu_item_id": row[1] if len(row) > 1 else 0,
                        "name": row[2] if len(row) > 2 else "",
                        "price": row[3] if len(row) > 3 else 0,
                        "quantity": row[4] if len(row) > 4 else 1,
                        "size": row[5] if len(row) > 5 else None,
                        "color": row[6] if len(row) > 6 else None,
                        "discount_percentage": (
                            row[7] if len(row) > 7 and row[7] is not None else 0
                        ),
                        "total": (
                            row[8]
                            if len(row) > 8 and row[8] is not None
                            else (row[3] * row[4])
                        ),
                    }
                    cart_items.append(item_dict)
                except Exception:
                    continue

        return cart_items

    except Exception as e:
        app_logger.error(f"Savatcha ma'lumotlarini olishda xatolik: {str(e)}")
        return []
    finally:
        if close_conn and conn:
            conn.close()


def get_cart_total(conn, session_id, user_id=None):
    "Savatchaning umumiy summasini hisoblash"
    # If no connection passed, create new one
    if conn is None:
        conn = get_db()
        close_conn = True
    else:
        close_conn = False

    try:
        cur = conn.cursor()
        if user_id:
            cur.execute(
                """
                SELECT SUM(
                    CASE
                        WHEN COALESCE(mi.discount_percentage, 0) > 0
                        THEN (mi.price * (100 - COALESCE(mi.discount_percentage, 0)) / 100) * ci.quantity
                        ELSE mi.price * ci.quantity
                    END
                )
                FROM cart_items ci
                JOIN menu_items mi ON ci.menu_item_id = mi.id
                WHERE ci.user_id = ?
            """,
                (user_id,),
            )
        else:
            cur.execute(
                """
                SELECT SUM(
                    CASE
                        WHEN COALESCE(mi.discount_percentage, 0) > 0
                        THEN (mi.price * (100 - COALESCE(mi.discount_percentage, 0)) / 100) * ci.quantity
                        ELSE mi.price * ci.quantity
                    END
                )
                FROM cart_items ci
                JOIN menu_items mi ON ci.menu_item_id = mi.id
                WHERE ci.session_id = ?
            """,
                (session_id,),
            )
        result = cur.fetchone()
        return result[0] if result and result[0] is not None else 0
    except Exception as e:
        app_logger.error(f"Get cart total error: {str(e)}")
        return 0
    finally:
        if close_conn and conn:
            conn.close()


def clear_cart(conn, session_id, user_id=None):
    "Savatchani tozalash"
    try:
        cur = conn.cursor()
        if user_id:
            cur.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        else:
            cur.execute("DELETE FROM cart_items WHERE session_id = ?", (session_id,))
        conn.commit()
    except Exception as e:
        app_logger.error(f"Clear cart error: {str(e)}")


def save_user_to_json(name, ticket_no, order_time, order_items):
    "Foydalanuvchi ma'lumotlarini users.json fayliga saqlash"
    users_file = "users.json"

    # Yangi foydalanuvchi ma'lumotlari
    user_data = {
        "ism": name,
        "buyurtma_raqami": ticket_no,
        "buyurtma_vaqti": order_time.strftime("%Y-%m-%d %H:%M:%S"),
        "buyurtma_mahsulotlari": order_items,
    }

    # Mavjud ma'lumotlarni o'qish
    users_list = []
    if os.path.exists(users_file):
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            users_list = []

    # Yangi ma'lumotni qo'shish
    users_list.append(user_data)

    # Faylga saqlash
    try:
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(users_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app_logger.error(f"Failed to save user data to JSON: {str(e)}")


def save_staff_to_json(
    first_name, last_name, birth_date, phone, staff_id, register_time
):
    "Xodim ma'lumotlarini employees.json fayliga saqlash"
    employees_file = "employees.json"

    # Yangi xodim ma'lumotlari
    employee_data = {
        "id": staff_id,
        "ism": first_name,
        "familiya": last_name,
        "tugulgan_sana": birth_date,
        "telefon": phone,
        "royxatdan_otgan_vaqti": register_time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Mavjud ma'lumotlarni o'qish
    employees_list = []
    if os.path.exists(employees_file):
        try:
            with open(employees_file, "r", encoding="utf-8") as f:
                employees_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            employees_list = []

    # Yangi ma'lumotni qo'shish
    employees_list.append(employee_data)

    # Faylga saqlash
    try:
        with open(employees_file, "w", encoding="utf-8") as f:
            json.dump(employees_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app_logger.error(f"Failed to save staff data to JSON: {str(e)}")


# ---------- Chat & Notification helpers and APIs (appended) ----------
def _now_iso_short():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _current_user_context():
    """Return a simple dict describing current session user type and id."""
    if session.get("super_admin"):
        return {"type": "super", "id": None}
    if session.get("staff_id"):
        return {"type": "staff", "id": session.get("staff_id")}
    if session.get("courier_id"):
        return {"type": "courier", "id": session.get("courier_id")}
    if session.get("user_id"):
        return {"type": "user", "id": session.get("user_id")}
    return {"type": "guest", "id": None}


def create_or_get_group_chat(name="Xodimlar va Kuryerlar va SuperAdmin"):
    """Ensure a single staff/courier/super group exists and return chat id."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM chats WHERE is_group=1 AND name=?", (name,))
        r = cur.fetchone()
        if r:
            cid = r[0]
        else:
            created = _now_iso_short()
            cur.execute(
                "INSERT INTO chats (name,is_group,created_at) VALUES (?,?,?)",
                (name, 1, created),
            )
            cid = cur.lastrowid
            # add a placeholder super member so super admin can always access
            cur.execute(
                "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?,?,?)",
                (cid, "super_admin", None),
            )
            conn.commit()
        conn.close()
        return cid
    except Exception as e:
        app_logger.error(f"create_or_get_group_chat error: {e}")
        return None


def add_private_chat_between(member_type, member_id):
    """Create or return private chat for a member. Only that member and super are members."""
    try:
        conn = get_db()
        cur = conn.cursor()
        # find existing private chat for this member
        cur.execute(
            "SELECT c.id FROM chats c JOIN chat_members m ON c.id=m.chat_id WHERE c.is_group=0 AND m.member_type=? AND m.member_id=?",
            (member_type, member_id),
        )
        r = cur.fetchone()
        if r:
            cid = r[0]
        else:
            created = _now_iso_short()
            cur.execute(
                "INSERT INTO chats (name,is_group,created_at) VALUES (?,?,?)",
                (f"private-{member_type}-{member_id}", 0, created),
            )
            cid = cur.lastrowid
            cur.execute(
                "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?,?,?)",
                (cid, member_type, member_id),
            )
            # add super_admin as a member so admins can always see/support this private chat
            cur.execute(
                "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?,?,?)",
                (cid, "super_admin", None),
            )
            conn.commit()
        conn.close()
        return cid
    except Exception as e:
        app_logger.error(f"add_private_chat_between error: {e}")
        return None


def post_chat_message(chat_id, sender_type, sender_id, text):
    try:
        # Input validation
        if not chat_id or not sender_type or not text or not text.strip():
            app_logger.error(f"post_chat_message: Invalid input parameters")
            return False

        conn = get_db()
        cur = conn.cursor()
        created = _now_iso_short()

        # Ensure chat_messages table exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                sender_id INTEGER,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )

        cur.execute(
            "INSERT INTO chat_messages (chat_id,sender_type,sender_id,text,created_at) VALUES (?,?,?,?,?)",
            (chat_id, sender_type, sender_id, text.strip(), created),
        )
        conn.commit()
        conn.close()
        app_logger.info(
            f"Chat message posted successfully: chat_id={chat_id}, sender={sender_type}"
        )
        return True
    except Exception as e:
        app_logger.error(f"post_chat_message error: {e}")
        try:
            conn.close()
        except:
            pass
        return False


def get_chat_messages(chat_id, limit=200):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, sender_type, sender_id, text, created_at FROM chat_messages WHERE chat_id=? ORDER BY id ASC LIMIT ?",
            (chat_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
        msgs = []
        for r in rows:
            msgs.append(
                {
                    "id": r[0],
                    "sender_type": r[1],
                    "sender_id": r[2],
                    "text": r[3],
                    "created_at": r[4],
                }
            )
        return msgs
    except Exception as e:
        app_logger.error(f"get_chat_messages error: {e}")
        return []


def get_user_chats_for_ui(current_user):
    """Return chats visible to current_user with preview."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT c.id, c.name, c.is_group FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE m.member_type=? AND (m.member_id=? OR m.member_id IS NULL)",
            (current_user["type"], current_user.get("id")),
        )
        rows = cur.fetchall()
        chats = []
        for r in rows:
            cid, name, is_group = r[0], r[1], r[2]
            cur.execute(
                "SELECT text FROM chat_messages WHERE chat_id=? ORDER BY id DESC LIMIT 1",
                (cid,),
            )
            lr = cur.fetchone()
            preview = lr[0] if lr else ""
            chats.append(
                {
                    "id": cid,
                    "name": name or f"Chat {cid}",
                    "is_group": bool(is_group),
                    "preview": preview,
                }
            )
        conn.close()
        return chats
    except Exception as e:
        app_logger.error(f"get_user_chats_for_ui error: {e}")
        return []


def get_unread_chat_count_for_user(current_user):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(cm.id) FROM chat_messages cm JOIN chat_members m ON cm.chat_id = m.chat_id WHERE m.member_type=? AND (m.member_id=? OR m.member_id IS NULL)",
            (current_user["type"], current_user.get("id")),
        )
        r = cur.fetchone()
        conn.close()
        return int(r[0]) if r and r[0] else 0
    except Exception as e:
        app_logger.error(f"get_unread_chat_count_for_user error: {e}")
        return 0


def send_notification(
    recipient_type, recipient_id, title, body, sender_type="system", sender_id=None
):
    """Send notification to specific user or broadcast to all users of a type."""
    try:
        # Input validation
        if not recipient_type or not title or not body:
            app_logger.error(f"send_notification: Invalid input parameters")
            return False

        # Normalize recipient_type aliases to canonical values used throughout the app
        rt = (recipient_type or "").lower()
        if rt in ("user", "users", "customer", "customers"):
            recipient_type = "users"
        elif rt in ("staff", "staff_member", "staff_members"):
            recipient_type = "staff"
        elif rt in ("courier", "couriers"):
            recipient_type = "couriers"
        elif rt in ("all", "broadcast"):
            recipient_type = "all"
        else:
            # Fallback: keep original lowercased token to avoid unexpected NULLs
            recipient_type = rt

        # Ensure recipient_id is an integer or None
        try:
            recipient_id = (
                int(recipient_id)
                if recipient_id is not None and str(recipient_id) != ""
                else None
            )
        except Exception:
            recipient_id = None

        conn = get_db()
        cur = conn.cursor()
        created = _now_iso_short()

        # Ensure notifications table exists with all required columns
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_type TEXT NOT NULL,
                recipient_id INTEGER,
                sender_type TEXT DEFAULT 'system',
                sender_id INTEGER,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL,
                read_flag INTEGER DEFAULT 0,
                notification_type TEXT DEFAULT 'general'
            )
        """
        )

        # Add missing columns if they don't exist (guarded by PRAGMA)
        cur.execute("PRAGMA table_info(notifications)")
        cols = [r[1] for r in cur.fetchall() or []]
        if "sender_type" not in cols:
            cur.execute(
                "ALTER TABLE notifications ADD COLUMN sender_type TEXT DEFAULT 'system'"
            )
        if "sender_id" not in cols:
            cur.execute("ALTER TABLE notifications ADD COLUMN sender_id INTEGER")
        if "notification_type" not in cols:
            cur.execute(
                "ALTER TABLE notifications ADD COLUMN notification_type TEXT DEFAULT 'general'"
            )

        cur.execute(
            "INSERT INTO notifications (recipient_type, recipient_id, sender_type, sender_id, title, body, created_at, read_flag) VALUES (?,?,?,?,?,?,?,0)",
            (
                recipient_type,
                recipient_id,
                sender_type,
                sender_id,
                title,
                body,
                created,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        app_logger.error(f"send_notification error: {e}")
        return False


def send_automatic_notification(
    notification_type, recipient_type, recipient_id, title, body, **kwargs
):
    """Send automatic system notifications for various events."""
    try:
        # Add notification type to body for better categorization
        enhanced_body = f"[{notification_type.upper()}] {body}"

        # Send notification
        success = send_notification(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            title=title,
            body=enhanced_body,
            sender_type="system",
            sender_id=None,
        )

        if success:
            app_logger.info(
                f"Automatic notification sent: {notification_type} to {recipient_type}:{recipient_id}"
            )

        return success
    except Exception as e:
        app_logger.error(f"send_automatic_notification error: {e}")
        return False


def send_order_notifications(order_id, order_status, customer_name, total_amount):
    """Send notifications for order status changes."""
    try:
        # Get order details
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            return False

        # Notify staff about new orders
        if order_status == "pending":
            staff_members = execute_query("SELECT id FROM staff", fetch_all=True)
            if staff_members:
                for staff in staff_members:
                    staff_id = staff["id"] if isinstance(staff, dict) else staff[0]
                    send_automatic_notification(
                        notification_type="new_order",
                        recipient_type="staff",
                        recipient_id=staff_id,
                        title="🆕 Yangi buyurtma",
                        body=f"Yangi buyurtma: {customer_name} - {total_amount:,} so'm",
                    )

        # Notify couriers about ready orders
        elif order_status == "ready":
            couriers = execute_query("SELECT id FROM couriers", fetch_all=True)
            if couriers:
                for courier in couriers:
                    courier_id = (
                        courier["id"] if isinstance(courier, dict) else courier[0]
                    )
                    send_automatic_notification(
                        notification_type="order_ready",
                        recipient_type="courier",
                        recipient_id=courier_id,
                        title="📦 Buyurtma tayyor",
                        body=f"Buyurtma tayyor: {customer_name} - {total_amount:,} so'm",
                    )

        # Notify customer about order status
        customer_id = order.get("user_id")
        if customer_id:
            status_messages = {
                "confirmed": "✅ Buyurtmangiz tasdiqlandi",
                "preparing": "👨‍🍳 Buyurtmangiz tayyorlanmoqda",
                "ready": "📦 Buyurtmangiz tayyor",
                "delivered": "🚚 Buyurtmangiz yetkazib berildi",
                "cancelled": "❌ Buyurtmangiz bekor qilindi",
            }

            if order_status in status_messages:
                send_automatic_notification(
                    notification_type="order_update",
                    recipient_type="users",
                    recipient_id=customer_id,
                    title=status_messages[order_status],
                    body=f"Buyurtma #{order_id} holati yangilandi: {order_status}",
                )

        return True
    except Exception as e:
        app_logger.error(f"send_order_notifications error: {e}")
        return False


def send_system_notifications():
    """Send various system notifications."""
    try:
        # Check for low inventory
        low_inventory_items = execute_query(
            "SELECT name, quantity FROM menu WHERE quantity < 10 AND quantity > 0",
            fetch_all=True,
        )
        if low_inventory_items:
            for item in low_inventory_items:
                item_name = item.get("name") if isinstance(item, dict) else item[0]
                quantity = item.get("quantity") if isinstance(item, dict) else item[1]

                # Notify staff
                staff_members = execute_query("SELECT id FROM staff", fetch_all=True)
                if staff_members:
                    for staff in staff_members:
                        staff_id = staff["id"] if isinstance(staff, dict) else staff[0]
                        send_automatic_notification(
                            notification_type="low_inventory",
                            recipient_type="staff",
                            recipient_id=staff_id,
                            title="⚠️ Mahsulot kam qoldi",
                            body=f"{item_name} - {quantity} dona qoldi",
                        )

        # Check for pending orders older than 30 minutes
        old_pending_orders = execute_query(
            "SELECT id, customer_name, total_amount FROM orders WHERE status = 'pending' AND created_at < datetime('now', '-30 minutes')",
            fetch_all=True,
        )
        if old_pending_orders:
            for order in old_pending_orders:
                order_id = order.get("id") if isinstance(order, dict) else order[0]
                customer_name = (
                    order.get("customer_name") if isinstance(order, dict) else order[1]
                )
                total_amount = (
                    order.get("total_amount") if isinstance(order, dict) else order[2]
                )

                # Notify staff about old pending orders
                staff_members = execute_query("SELECT id FROM staff", fetch_all=True)
                if staff_members:
                    for staff in staff_members:
                        staff_id = staff["id"] if isinstance(staff, dict) else staff[0]
                        send_automatic_notification(
                            notification_type="old_order",
                            recipient_type="staff",
                            recipient_id=staff_id,
                            title="⏰ Eski buyurtma",
                            body=f"Buyurtma #{order_id} 30 daqiqadan ko'p vaqt kutilmoqda",
                        )

        return True
    except Exception as e:
        app_logger.error(f"send_system_notifications error: {e}")
        return False


def get_notifications_for_user(current_user):
    try:
        conn = get_db()
        cur = conn.cursor()

        # Enhanced query with sender information
        cur.execute(
            """
            SELECT n.id, n.title, n.body, n.read_flag, n.created_at, n.sender_type, n.sender_id
            FROM notifications n
            WHERE n.recipient_type=? AND (n.recipient_id=? OR n.recipient_id IS NULL)
            ORDER BY n.created_at DESC LIMIT 100
        """,
            (current_user["type"], current_user.get("id")),
        )

        rows = cur.fetchall()
        conn.close()

        notes = []
        for r in rows:
            notification = {
                "id": r[0],
                "title": r[1],
                "body": r[2],
                "read_flag": r[3],
                "created_at": r[4],
                "sender_type": r[5],
                "sender_id": r[6],
                "is_read": bool(r[3]),
                "time_ago": get_time_ago(r[4]),
            }

            # Add sender name if available
            if r[5] and r[6]:
                sender_name = get_sender_name(r[5], r[6])
                notification["sender_name"] = sender_name

            notes.append(notification)

        return notes
    except Exception as e:
        app_logger.error(f"get_notifications_for_user error: {e}")
        return []


def get_sender_name(sender_type, sender_id):
    """Get sender name for notification display."""
    try:
        if sender_type == "super_admin":
            return "Super Admin"
        elif sender_type == "staff":
            staff = execute_query(
                "SELECT first_name, last_name FROM staff WHERE id = ?",
                (sender_id,),
                fetch_one=True,
            )
            if staff:
                name = f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip()
                return name or f"Staff #{sender_id}"
        elif sender_type == "courier":
            courier = execute_query(
                "SELECT first_name, last_name FROM couriers WHERE id = ?",
                (sender_id,),
                fetch_one=True,
            )
            if courier:
                name = f"{courier.get('first_name', '')} {courier.get('last_name', '')}".strip()
                return name or f"Courier #{sender_id}"
        elif sender_type == "users":
            user = execute_query(
                "SELECT first_name, last_name FROM users WHERE id = ?",
                (sender_id,),
                fetch_one=True,
            )
            if user:
                name = (
                    f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                )
                return name or f"User #{sender_id}"
        elif sender_type == "system":
            return "Tizim"

        return "Noma'lum"
    except Exception as e:
        app_logger.error(f"get_sender_name error: {e}")
        return "Noma'lum"


def get_time_ago(timestamp):
    """Convert timestamp to human readable time ago format."""
    try:
        from datetime import datetime, timezone

        # Always compare aware datetimes
        now = datetime.now(timezone.utc)

        if isinstance(timestamp, str):
            # Try parse ISO; if naive, assume UTC
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = timestamp
            if isinstance(dt, datetime) and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

        diff = now - (dt if isinstance(dt, datetime) else now)

        if diff.days > 0:
            return f"{diff.days} kun oldin"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} soat oldin"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} daqiqa oldin"
        else:
            return "Hozir"
    except Exception as e:
        app_logger.error(f"get_time_ago error: {e}")
        return "Noma'lum vaqt"


def get_recipient_info_from_session():
    """Return canonical recipient_type, list of possible aliases, and recipient_id from current session."""
    try:
        if session.get("super_admin"):
            return ("super_admin", ["super_admin"], None)

        if session.get("user_id"):
            # canonical 'users' but accept legacy variants
            return (
                "users",
                ["users", "user", "customer", "customers"],
                session.get("user_id"),
            )
        if session.get("staff_id"):
            return (
                "staff",
                ["staff", "staff_member", "staffs", "staff_members"],
                session.get("staff_id"),
            )
        if session.get("courier_id"):
            return ("couriers", ["couriers", "courier"], session.get("courier_id"))

        return (None, [], None)
    except Exception as e:
        app_logger.error(f"get_recipient_info_from_session error: {e}")
        return (None, [], None)


# ---------- Routes ----------


@app.route("/")
def index():
    "Bosh sahifa - menu sahifasiga yo'naltirish"
    return redirect("/menu")


@app.route("/system-management-panel-x8k2m")
def admin_index():
    # Super admin yoki staff kirgan bo'lishi kerak
    if not session.get("super_admin") and not session.get("staff_id"):
        flash("Bu sahifaga kirish uchun admin huquqi kerak.", "error")
        return redirect(url_for("index"))
    return render_template("admin_index.html")


@app.route("/system-management-panel-master-z8x9k")
def system_management_panel():
    "System management panel"
    if not session.get("super_admin"):
        flash("Super admin huquqi kerak.", "error")
        return redirect(url_for("super_admin_login"))
    return redirect(url_for("super_admin_dashboard"))


# Monitor routes
@app.route("/monitor")
def monitor():
    "Monitor sahifasi - TV uchun"
    return redirect(url_for("admin_monitor"))


@app.route("/admin/monitor")
def admin_monitor_alt():
    "Alternative monitor route"
    return redirect(url_for("admin_monitor"))


# Staff dashboard routes
@app.route("/admin")
def admin_redirect():
    "Admin redirects"
    if session.get("super_admin"):
        return redirect(url_for("super_admin_dashboard"))
    elif session.get("staff_id"):
        return redirect(url_for("staff_dashboard"))
    elif session.get("courier_id"):
        return redirect(url_for("courier_dashboard"))
    else:
        return redirect(url_for("staff_login"))


@app.route("/admin/dashboard")
def admin_dashboard_redirect():
    "Admin dashboard redirect"
    if session.get("staff_id"):
        return redirect(url_for("staff_dashboard"))
    elif session.get("super_admin"):
        return redirect(url_for("super_admin_dashboard"))
    else:
        return redirect(url_for("staff_login"))


# Staff routes
@app.route("/staff")
def staff_redirect():
    "Staff redirect"
    if session.get("staff_id"):
        return redirect(url_for("staff_dashboard"))
    else:
        return redirect(url_for("staff_login"))


@app.route("/staff/login")
def staff_login_redirect():
    "Staff login redirect"
    return redirect(url_for("staff_login"))


# Courier routes
@app.route("/courier")
def courier_redirect():
    "Courier redirect"
    if session.get("courier_id"):
        return redirect(url_for("courier_dashboard"))
    else:
        return redirect(url_for("courier_login"))


@app.route("/courier/login")
def courier_login_redirect():
    "Courier login redirect"
    return redirect(url_for("courier_login"))


# Super admin routes
@app.route("/superadmin")
@app.route("/super-admin")
@app.route("/admin/super")
def superadmin_redirect():
    "Super admin redirect"
    if session.get("super_admin"):
        return redirect(url_for("super_admin_dashboard"))
    else:
        return redirect(url_for("super_admin_login"))


@app.route("/api/super-admin/reports")
def api_super_admin_reports():
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        report_type = (request.args.get("type") or "").lower()

        # Agar start/end kiritilmagan bo'lsa, type bo'yicha yoki default 30 kunlik oraliqni tanlash
        if not start_date or not end_date:
            import datetime

            today = datetime.date.today()

            if report_type in ("daily", "today"):
                start_date = today.strftime("%Y-%m-%d")
                end_date = start_date
            elif report_type in ("weekly", "week"):
                start_date = (today - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
            elif report_type in ("monthly", "month"):
                # oxirgi 30 kun
                start_date = (today - datetime.timedelta(days=29)).strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")
            else:
                # default: oxirgi 30 kun
                start_date = (today - datetime.timedelta(days=29)).strftime("%Y-%m-%d")
                end_date = today.strftime("%Y-%m-%d")

        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Buyurtmalar va daromad (use receipts.total_amount)
            cur.execute(
                "SELECT COUNT(*), COALESCE(SUM(r.total_amount), 0) FROM orders o LEFT JOIN receipts r ON o.id = r.order_id WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) <= ?",
                (start_date, end_date),
            )
            result = cur.fetchone() or (0, 0)
            total_orders = int(result[0]) if result[0] is not None else 0
            total_revenue = float(result[1]) if result[1] is not None else 0.0
            avg_check = int(total_revenue / total_orders) if total_orders > 0 else 0

            # Yangi mijozlar (ro'yxatdan o'tganlar)
            cur.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?",
                (start_date, end_date),
            )
            nc_res = cur.fetchone()
            new_customers = int(nc_res[0]) if nc_res and nc_res[0] is not None else 0

            # Oldingi davr uchun buyurtmalar (growth rate)
            import datetime

            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                delta = (end_dt - start_dt).days + 1
                prev_start = (start_dt - datetime.timedelta(days=delta)).strftime(
                    "%Y-%m-%d"
                )
                prev_end = (end_dt - datetime.timedelta(days=delta)).strftime(
                    "%Y-%m-%d"
                )
                cur.execute(
                    "SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?",
                    (prev_start, prev_end),
                )
                po = cur.fetchone()
                prev_orders = int(po[0]) if po and po[0] is not None else 0
            except Exception:
                prev_orders = 0

            growth_rate = 0
            if prev_orders:
                try:
                    growth_rate = round(
                        ((total_orders - prev_orders) / prev_orders) * 100, 1
                    )
                except Exception:
                    growth_rate = 0

            # Sotuvlar (kunlik)
            cur.execute(
                "SELECT DATE(o.created_at) as date, COUNT(*) as orders_count, COALESCE(SUM(r.total_amount),0) as revenue FROM orders o LEFT JOIN receipts r ON o.id = r.order_id WHERE DATE(o.created_at) >= ? AND DATE(o.created_at) <= ? GROUP BY DATE(o.created_at) ORDER BY date ASC",
                (start_date, end_date),
            )
            sales = []
            rows = cur.fetchall() or []
            for row in rows:
                # row can be tuple or sqlite Row
                try:
                    date_val = row[0]
                    orders_count = int(row[1]) if row[1] is not None else 0
                    revenue = float(row[2]) if row[2] is not None else 0.0
                except Exception:
                    # Fallback in case of unexpected row shape
                    row_list = list(row)
                    date_val = row_list[0] if len(row_list) > 0 else ""
                    orders_count = (
                        int(row_list[1])
                        if len(row_list) > 1 and row_list[1] is not None
                        else 0
                    )
                    revenue = (
                        float(row_list[2])
                        if len(row_list) > 2 and row_list[2] is not None
                        else 0.0
                    )

                avg_order = int(revenue / orders_count) if orders_count > 0 else 0
                sales.append(
                    {
                        "date": date_val,
                        "orders_count": orders_count,
                        "revenue": revenue,
                        "avg_order": avg_order,
                        "cashback": 0,
                    }
                )

            products = []
            customers = []
            staff = []
            branches = []

        return jsonify(
            {
                "summary": {
                    "total_orders": total_orders,
                    "total_revenue": total_revenue,
                    "avg_check": avg_check,
                    "new_customers": new_customers,
                    "growth_rate": growth_rate,
                },
                "sales": sales,
                "products": products,
                "customers": customers,
                "staff": staff,
                "branches": branches,
            }
        )
    except Exception as e:
        app_logger.error(
            f"api_super_admin_reports error: {str(e)} - params: {request.args}"
        )
        return (
            jsonify(
                {"error": "Hisobot yaratishda xatolik yuz berdi", "details": str(e)}
            ),
            500,
        )


@app.route("/api/super-admin/export-report", methods=["POST"])
def api_super_admin_export_report():
    """Accepts JSON report data from frontend (summary, sales, products, customers, etc.)
    and returns an in-memory XLSX file for download.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "JSON body required"}), 400

        data = request.get_json()
        # Expecting keys: summary, sales, products, customers, staff, branches
        summary = data.get("summary", {})
        sales = data.get("sales", []) or []
        products = data.get("products", []) or []
        customers = data.get("customers", []) or []
        staff = data.get("staff", []) or []
        branches = data.get("branches", []) or []

        # If pandas/openpyxl not available, fall back to CSV downloads for each sheet
        if pd is None or Workbook is None:
            app_logger.warning(
                "Pandas/openpyxl not available — falling back to CSV export"
            )
            # Create a zip or single CSV for the summary+sales combined
            try:
                output = BytesIO()
                # Create a simple CSV with sections separated
                w = output
                # We'll write UTF-8 BOM for Excel compatibility
                w.write(b"\ufeff")
                text = []
                text.append("# Summary")
                if summary:
                    for k, v in summary.items():
                        text.append(f"{k},{v}")
                else:
                    text.append("no_summary,")
                text.append("")
                text.append("# Sales")
                if sales:
                    # extract headers
                    headers = set()
                    for row in sales:
                        headers.update(row.keys() if isinstance(row, dict) else [])
                    headers = list(headers)
                    text.append(",".join(headers))
                    for row in sales:
                        row_vals = [
                            str(row.get(h, "")) if isinstance(row, dict) else ""
                            for h in headers
                        ]
                        text.append(",".join(row_vals))
                else:
                    text.append("no_sales,")

                # Append other sections minimally
                text.append("")
                text.append("# Products")
                text.append(str(products or []))
                text.append("")
                text.append("# Customers")
                text.append(str(customers or []))

                csv_bytes = "\n".join(text).encode("utf-8")
                output.write(csv_bytes)
                output.seek(0)
                filename = (
                    f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="text/csv",
                )
            except Exception as e:
                app_logger.error(f"CSV fallback export failed: {e}")
                return jsonify({"error": "Export failed", "details": str(e)}), 500

        # Build DataFrames for each section
        sheets = {}
        sheets["summary"] = pd.DataFrame([summary]) if summary else pd.DataFrame()
        sheets["sales"] = pd.DataFrame(sales)
        sheets["products"] = pd.DataFrame(products)
        sheets["customers"] = pd.DataFrame(customers)
        sheets["staff"] = pd.DataFrame(staff)
        sheets["branches"] = pd.DataFrame(branches)

        # Create Excel in-memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                # Ensure we write an empty sheet with header if df empty
                if df is None or df.empty:
                    # create empty DF with a placeholder column to avoid openpyxl errors
                    pd.DataFrame({"info": []}).to_excel(
                        writer, sheet_name=sheet_name, index=False
                    )
                else:
                    # sanitize column names to strings
                    df.columns = [str(c) for c in df.columns]
                    # Convert nested dicts/lists to JSON strings to keep excel readable
                    for col in df.columns:
                        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                            df[col] = df[col].apply(
                                lambda x: (
                                    json.dumps(x, ensure_ascii=False)
                                    if x is not None
                                    else ""
                                )
                            )
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        try:
            body_preview = (request.get_data() or b"")[:1024]
        except Exception:
            body_preview = b"<unavailable>"
        app_logger.error(
            f"export-report error: {str(e)} - body_preview: {body_preview}"
        )
        return jsonify({"error": "Export failed", "details": str(e)}), 500


@app.route("/api/super-admin/export-staff", methods=["GET"])
def api_super_admin_export_staff():
    """Return an XLSX file with the staff list. Restricted to super_admin session."""
    try:
        if not session.get("super_admin"):
            return jsonify({"error": "Unauthorized"}), 401

        staff_rows = (
            execute_query("SELECT * FROM staff ORDER BY id ASC", fetch_all=True) or []
        )

        # Normalize into list of dicts
        if pd is None or Workbook is None:
            app_logger.warning(
                "Pandas/openpyxl not available — falling back to CSV export for staff"
            )
            try:
                output = BytesIO()
                output.write(b"\ufeff")
                # csv writer needs text mode; create text and encode later
                rows = staff_rows or []
                if rows:
                    # convert sqlite Row to dicts
                    headers = []
                    rows_list = []
                    for r in rows:
                        d = dict(r) if hasattr(r, "keys") else r
                        rows_list.append(d)
                        for k in d.keys():
                            if k not in headers:
                                headers.append(k)
                    text_lines = [",".join(headers)]
                    for d in rows_list:
                        text_lines.append(
                            ",".join([str(d.get(h, "")) for h in headers])
                        )
                else:
                    text_lines = ["info", "no_staff"]
                output.write("\n".join(text_lines).encode("utf-8"))
                output.seek(0)
                filename = f"staff_list_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="text/csv",
                )
            except Exception as e:
                app_logger.error(f"CSV fallback staff export failed: {e}")
                return jsonify({"error": "Export failed", "details": str(e)}), 500

        try:
            staff_list = [dict(r) if hasattr(r, "keys") else r for r in staff_rows]
            df = pd.DataFrame(staff_list)
        except Exception:
            # Fallback: create an empty dataframe with minimal columns
            df = pd.DataFrame(staff_rows) if staff_rows else pd.DataFrame()

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if df is None or df.empty:
                pd.DataFrame({"info": []}).to_excel(
                    writer, sheet_name="staff", index=False
                )
            else:
                df.columns = [str(c) for c in df.columns]
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                        df[col] = df[col].apply(
                            lambda x: (
                                json.dumps(x, ensure_ascii=False)
                                if x is not None
                                else ""
                            )
                        )
                df.to_excel(writer, sheet_name="staff", index=False)

        output.seek(0)
        filename = (
            f"staff_list_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        app_logger.error(f"export-staff error: {str(e)}")
        return jsonify({"error": "Export failed", "details": str(e)}), 500


@app.route("/api/super-admin/export-couriers", methods=["GET"])
def api_super_admin_export_couriers():
    """Return an XLSX file with the courier list. Restricted to super_admin session."""
    try:
        if not session.get("super_admin"):
            return jsonify({"error": "Unauthorized"}), 401

        courier_rows = (
            execute_query("SELECT * FROM couriers ORDER BY id ASC", fetch_all=True)
            or []
        )

        if pd is None or Workbook is None:
            app_logger.warning(
                "Pandas/openpyxl not available — falling back to CSV export for couriers"
            )
            try:
                output = BytesIO()
                output.write(b"\ufeff")
                rows = courier_rows or []
                if rows:
                    headers = []
                    rows_list = []
                    for r in rows:
                        d = dict(r) if hasattr(r, "keys") else r
                        rows_list.append(d)
                        for k in d.keys():
                            if k not in headers:
                                headers.append(k)
                    text_lines = [",".join(headers)]
                    for d in rows_list:
                        text_lines.append(
                            ",".join([str(d.get(h, "")) for h in headers])
                        )
                else:
                    text_lines = ["info", "no_couriers"]
                output.write("\n".join(text_lines).encode("utf-8"))
                output.seek(0)
                filename = f"couriers_list_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="text/csv",
                )
            except Exception as e:
                app_logger.error(f"CSV fallback couriers export failed: {e}")
                return jsonify({"error": "Export failed", "details": str(e)}), 500

        try:
            courier_list = [dict(r) if hasattr(r, "keys") else r for r in courier_rows]
            df = pd.DataFrame(courier_list)
        except Exception:
            df = pd.DataFrame(courier_rows) if courier_rows else pd.DataFrame()

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if df is None or df.empty:
                pd.DataFrame({"info": []}).to_excel(
                    writer, sheet_name="couriers", index=False
                )
            else:
                df.columns = [str(c) for c in df.columns]
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                        df[col] = df[col].apply(
                            lambda x: (
                                json.dumps(x, ensure_ascii=False)
                                if x is not None
                                else ""
                            )
                        )
                df.to_excel(writer, sheet_name="couriers", index=False)

        output.seek(0)
        filename = (
            f"couriers_list_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        app_logger.error(f"export-couriers error: {str(e)}")
        return jsonify({"error": "Export failed", "details": str(e)}), 500


@app.route("/admin/login")
def admin_login_redirect():
    "Admin login redirect"
    return redirect(url_for("super_admin_login"))


# Dashboard routes
@app.route("/dashboard")
def dashboard_redirect():
    "General dashboard redirect"
    return redirect(url_for("admin_redirect"))


@app.route("/display-monitor-tv-screen-z9p4n")
def admin_monitor():
    "TV Monitor - autentifikatsiyasiz kirish mumkin"
    cleanup_expired_orders()

    try:
        conn = get_db()
        cur = conn.cursor()

        # Waiting orders - kutayotgan buyurtmalar
        cur.execute(
            """SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE o.status='waiting'
            GROUP BY o.id
            ORDER BY o.eta_time ASC
        """
        )
        waiting = cur.fetchall() or []

        # Ready orders - tayyor buyurtmalar
        cur.execute(
            """SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE o.status='ready'
            GROUP BY o.id
            ORDER BY o.eta_time ASC
        """
        )
        ready = cur.fetchall() or []

        # Served orders in last 5 minutes - so'nggi 5 daqiqada berilgan buyurtmalar
        five_min_ago = (get_current_time() - datetime.timedelta(minutes=5)).isoformat()
        cur.execute(
            """SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE o.status='served' AND o.created_at >= ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """,
            (five_min_ago,),
        )
        served_recent = cur.fetchall() or []

        conn.close()

        # Safely convert rows to dictionaries
        waiting_dicts = [dict(row) for row in waiting]
        ready_dicts = [dict(row) for row in ready]
        served_recent_dicts = [dict(row) for row in served_recent]

        return render_template(
            "admin_monitor.html",
            waiting=waiting_dicts,
            ready=ready_dicts,
            served_recent=served_recent_dicts,
        )

    except Exception as e:
        app_logger.error(f"Monitor sahifasida xatolik: {str(e)}")
        return render_template(
            "admin_monitor.html", waiting=[], ready=[], served_recent=[]
        )


# Advanced decorators
def login_required(f):
    "Enhanced login decorator"

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("super_admin") and not session.get("staff_id"):
            if request.is_json:
                return jsonify({"error": "Authorization required"}), 401
            return redirect(url_for("staff_login"))
        return f(*args, **kwargs)

    return wrapper


def rate_limit(max_requests=100, window=3600):
    "Rate limiting decorator"

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            identifier = request.remote_addr
            if not rate_limiter.is_allowed(identifier, max_requests, window):
                if request.is_json:
                    return jsonify({"error": "Rate limit exceeded"}), 429
                flash("Juda ko'p so'rov yuborildi. Biroz kuting.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)

        return wrapper

    return decorator


def cache_result(ttl=300):
    "Result caching decorator"

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Cache key yaratish
            cache_key = f"{f.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"

            # Cache dan olishga harakat qilish (lazy-get to avoid None)
            try:
                cm = cache_manager or get_cache_manager()
            except Exception:
                cm = None

            if cm:
                try:
                    cached_result = cm.get(cache_key)
                    if cached_result is not None:
                        return cached_result
                except Exception:
                    # Fallthrough to compute result
                    pass

            # Yangi natija hisoblash va cache ga saqlash
            result = f(*args, **kwargs)

            if cm:
                try:
                    cm.set(cache_key, result, ttl)
                except Exception:
                    pass

            return result

        return wrapper

    return decorator


def async_task(f):
    "Asynchronous task decorator"

    @wraps(f)
    def wrapper(*args, **kwargs):
        # Use safe_submit to avoid None executor issues
        return safe_submit(f, *args, **kwargs)

    return wrapper


def validate_json(required_fields=None):
    "JSON validation decorator"

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "JSON format required"}), 400

            data = request.get_json()
            if not data:
                return jsonify({"error": "Empty JSON"}), 400

            if required_fields:
                missing_fields = [
                    field for field in required_fields if field not in data
                ]
                if missing_fields:
                    return jsonify({"error": f"Missing fields: {missing_fields}"}), 400

            return f(*args, **kwargs)

        return wrapper

    return decorator


# ---- MENU ----
@app.route("/menu")
@rate_limit(max_requests=10000, window=60)  # Очень высокий лимит для меню
@cache_result(ttl=120)
def menu():
    "Optimized menu endpoint"
    try:
        # Cache dan menu ma'lumotlarini olish (lazy-get)
        try:
            cm = cache_manager or get_cache_manager()
        except Exception:
            cm = None

        cached_menu = None
        if cm:
            try:
                cached_menu = cm.get("menu_items_active")
            except Exception:
                cached_menu = None

        if not cached_menu:
            menu_items_raw = execute_query(
                """SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.rating) as rating_count
                   FROM menu_items m
                   LEFT JOIN ratings r ON m.id = r.menu_item_id
                   WHERE m.available = 1
                   GROUP BY m.id
                   ORDER BY m.category, m.orders_count DESC, m.name""",
                fetch_all=True,
            )
            # Convert rows to dictionaries safely
            menu_items = []
            for row in menu_items_raw:
                try:
                    menu_items.append(dict(row))
                except Exception as e:
                    app_logger.warning(f"Menu item row processing error: {str(e)}")
                    continue  # Skip problematic row

            # Cache ga saqlash (safe)
            if cm:
                try:
                    cm.set("menu_items_active", menu_items, 120)
                except Exception:
                    pass
        else:
            menu_items = cached_menu

        # Treat menu_items as product catalogue (shoe shop) - men only.
        # All products are now categorized as men's shoes.
        men = menu_items  # All items are for men
        women = []  # No women's items

        # Foydalanuvchi sevimlilarini olish
        favorites = []
        user_id = session.get("user_id")
        if user_id:
            try:
                favorites_raw = execute_query(
                    "SELECT menu_item_id FROM favorites WHERE user_id = ?",
                    (user_id,),
                    fetch_all=True,
                )
                if not favorites_raw:
                    favorites = []
                else:
                    try:
                        favorites = [
                            fav["menu_item_id"] for fav in favorites_raw if fav
                        ]
                    except Exception:
                        # fallback for tuple rows
                        favs = []
                        for fav in favorites_raw:
                            try:
                                if isinstance(fav, (list, tuple)) and len(fav) > 0:
                                    favs.append(fav[0])
                            except Exception:
                                continue
                        favorites = favs
            except Exception as fav_error:
                app_logger.error(f"Favorites fetching error: {str(fav_error)}")
                favorites = []

        # Load basic user profile into session so templates can display profile info
        # (menu is a commonly visited page and templates expect session.* fields)
        try:
            if (
                user_id
                and not session.get("staff_id")
                and not session.get("courier_id")
                and not session.get("super_admin")
            ):
                user_profile = execute_query(
                    "SELECT phone, address, address_latitude, address_longitude, first_name, last_name, email, card_number FROM users WHERE id = ?",
                    (user_id,),
                    fetch_one=True,
                )
                if user_profile:
                    # user_profile may be None or a tuple; handle both safely
                    try:
                        session["user_phone"] = user_profile.get("phone", "") or ""
                        session["user_address"] = user_profile.get("address", "") or ""
                        session["user_address_latitude"] = user_profile.get(
                            "address_latitude"
                        )
                        session["user_address_longitude"] = user_profile.get(
                            "address_longitude"
                        )
                        session["user_first_name"] = (
                            user_profile.get("first_name", "") or ""
                        )
                        session["user_last_name"] = (
                            user_profile.get("last_name", "") or ""
                        )
                    except Exception:
                        # tuple-style access fallback
                        try:
                            session["user_phone"] = user_profile[0] or ""
                        except Exception:
                            session["user_phone"] = ""
                        try:
                            session["user_address"] = user_profile[1] or ""
                        except Exception:
                            session["user_address"] = ""
                        # best-effort for remaining fields
                        session.setdefault("user_address_latitude", None)
                        session.setdefault("user_address_longitude", None)
                        session.setdefault("user_first_name", "")
                        session.setdefault("user_last_name", "")
                    # Expose combined display name for templates
                    try:
                        fn = session.get("user_first_name", "") or ""
                        ln = session.get("user_last_name", "") or ""
                        session["user_name"] = (
                            (fn + " " + ln).strip()
                            if (fn or ln)
                            else session.get("user_name", "")
                        )
                    except Exception:
                        session["user_name"] = session.get("user_name", "")
                    session["user_email"] = user_profile.get("email", "") or ""
                    session["user_card_number"] = (
                        user_profile.get("card_number", "") or ""
                    )
        except Exception as profile_load_err:
            app_logger.warning(
                f"Failed to load user profile into session for menu: {str(profile_load_err)}"
            )

        # Render menu using clothing store categories (women/men)
        return render_template(
            "menu.html",
            women=women,
            men=men,
            favorites=favorites,
            current_page="menu",
        )

    except Exception as e:
        app_logger.error(f"Menu endpoint error: {str(e)}")
        # Fallback - oddiy menu
        try:
            menu_items_raw = execute_query(
                "SELECT * FROM menu_items WHERE available = 1 ORDER BY category, name",
                fetch_all=True,
            )
            menu_items = [dict(row) for row in menu_items_raw] if menu_items_raw else []
            # All items are for men only - no women's category
            women = []  # No women's items
            men = menu_items  # All items are for men
            return render_template(
                "menu.html", women=women, men=men, current_page="menu"
            )
        except Exception as fallback_error:
            app_logger.error(f"Menu fallback error: {str(fallback_error)}")
            flash("Menu yuklashda xatolik yuz berdi.", "error")
            return redirect(url_for("index"))


@app.route("/api/menu-search", methods=["GET"])
@rate_limit(max_requests=5000, window=60)  # Высокий лимит для API
@cached(
    ttl=30,
    key_func=lambda req, *a, **k: f"menu_search:{json.dumps(dict(req.args), sort_keys=True)}",
)
def api_menu_search():
    """API: Search and filter menu items.

    Query params supported:
      - q: full-text search on name and description
      - category: exact match (e.g., 'product', 'food', 'drink')
      - min_price, max_price: numeric bounds
      - size, color: comma-separated single values to match inside sizes/colors fields
      - sort: 'price_asc', 'price_desc', 'popularity', 'rating'
    Returns JSON: { success: True, items: [...] }
    """
    try:
        q = (request.args.get("q") or "").strip()
        category = (request.args.get("category") or "").strip()
        min_price = request.args.get("min_price")
        max_price = request.args.get("max_price")
        size = (request.args.get("size") or "").strip()
        color = (request.args.get("color") or "").strip()
        sort = (request.args.get("sort") or "").strip()

        where_clauses = ["available = 1"]
        params = []

        if q:
            # simple LIKE search on name and description
            where_clauses.append("(name LIKE ? OR description LIKE ?)")
            like_q = f"%{q}%"
            params.extend([like_q, like_q])

        if category:
            where_clauses.append("category = ?")
            params.append(category)

        if min_price:
            try:
                mp = float(min_price)
                where_clauses.append("price >= ?")
                params.append(mp)
            except Exception:
                pass

        if max_price:
            try:
                mp = float(max_price)
                where_clauses.append("price <= ?")
                params.append(mp)
            except Exception:
                pass

        # Size and color are stored as CSV or JSON in sizes/colors columns
        if size:
            # Use LIKE to match value inside CSV (e.g., '36,37,38')
            where_clauses.append(
                "(sizes LIKE ? OR sizes LIKE ? OR sizes LIKE ? OR sizes = ?)"
            )
            params.extend([f"%,{size},%", f"{size},%", f"%,{size}", size])

        if color:
            where_clauses.append(
                "(colors LIKE ? OR colors LIKE ? OR colors LIKE ? OR colors = ?)"
            )
            params.extend([f"%,{color},%", f"{color},%", f"%,{color}", color])

        order_by = "ORDER BY category, name"
        if sort == "price_asc":
            order_by = "ORDER BY price ASC"
        elif sort == "price_desc":
            order_by = "ORDER BY price DESC"
        elif sort == "popularity":
            order_by = "ORDER BY orders_count DESC"
        elif sort == "rating":
            order_by = "ORDER BY rating DESC"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1"
        sql = f"SELECT * FROM menu_items WHERE {where_sql} {order_by} LIMIT 200"

        items_raw = execute_query(sql, params, fetch_all=True)
        items = []
        if items_raw:
            for r in items_raw:
                try:
                    items.append(dict(r))
                except Exception:
                    # fallback if row proxy not dict-like
                    items.append(r)

        return jsonify({"success": True, "items": items})
    except Exception as e:
        app_logger.error(f"api_menu_search error: {str(e)}")
        return jsonify({"success": False, "message": "Search failed"}), 500


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    try:
        # Check if request is JSON or form data
        size = None
        color = None
        if request.is_json:
            data = request.get_json()
            menu_item_id = data.get("menu_item_id") or data.get("item_id")
            quantity = int(data.get("quantity", 1)) if data.get("quantity") else 1
            size = (data.get("size") or "").strip() if data.get("size") else None
            color = (data.get("color") or "").strip() if data.get("color") else None
        else:
            menu_item_id = request.form.get("menu_item_id")
            quantity = (
                int(request.form.get("quantity", 1))
                if request.form.get("quantity")
                else 1
            )
            size = (
                (request.form.get("size") or "").strip()
                if request.form.get("size")
                else None
            )
            color = (
                (request.form.get("color") or "").strip()
                if request.form.get("color")
                else None
            )

        if not menu_item_id:
            if request.is_json:
                return jsonify({"success": False, "message": "Mahsulot tanlanmadi"})
            flash("Mahsulot tanlanmadi.", "error")
            return redirect(url_for("menu"))

        # Convert menu_item_id to int safely
        try:
            menu_item_id = int(menu_item_id)
        except (ValueError, TypeError):
            if request.is_json:
                return jsonify({"success": False, "message": "Noto'g'ri mahsulot ID"})
            flash("Noto'g'ri mahsulot ID.", "error")
            return redirect(url_for("menu"))

        # Implement quantity limits - maximum 10,000 items per order
        MAX_QUANTITY_PER_ITEM = 10000
        if quantity <= 0:
            if request.is_json:
                return jsonify(
                    {"success": False, "message": "Miqdor 0 dan katta bo'lishi kerak"}
                )
            flash("Miqdor 0 dan katta bo'lishi kerak.", "error")
            return redirect(url_for("menu"))

        if quantity > MAX_QUANTITY_PER_ITEM:
            if request.is_json:
                return jsonify(
                    {
                        "success": False,
                        "message": f"Bir vaqtda maksimal {MAX_QUANTITY_PER_ITEM:,} ta buyurtma berish mumkin",
                    }
                )
            flash(
                f"Bir vaqtda maksimal {MAX_QUANTITY_PER_ITEM:,} ta buyurtma berish mumkin.",
                "error",
            )
            return redirect(url_for("menu"))

        # Validate menu item exists
        menu_item_data = execute_query(
            "SELECT id, sizes, colors FROM menu_items WHERE id = ? AND available = 1",
            (menu_item_id,),
            fetch_one=True,
        )

        if not menu_item_data:
            if request.is_json:
                return jsonify({"success": False, "message": "Mahsulot mavjud emas"})
            flash("Mahsulot mavjud emas.", "error")
            return redirect(url_for("menu"))

        # Optionally validate that provided size/color belong to the product (best-effort)
        try:
            # Normalize menu_item_data into accessible local variables to avoid
            # tuple/dict/RowProxy shape differences causing string-index errors.
            if menu_item_data is None:
                prod_sizes = ""
                prod_colors = ""
            elif hasattr(menu_item_data, "get"):
                prod_sizes = menu_item_data.get("sizes") or ""
                prod_colors = menu_item_data.get("colors") or ""
            else:
                # Assume positional tuple: SELECT id, sizes, colors
                try:
                    prod_sizes = menu_item_data[1] or ""
                except Exception:
                    prod_sizes = ""
                try:
                    prod_colors = menu_item_data[2] or ""
                except Exception:
                    prod_colors = ""

            # More tolerant matching: compare trimmed, case-insensitive values and
            # attempt numeric matches so that client-side formatting differences
            # (extra spaces, case differences, numeric strings) don't cause
            # required-option validations to fail.
            def _matches_option(value, options_str):
                if not value:
                    return False
                try:
                    opts = [s.strip() for s in str(options_str).split(",") if s.strip()]
                    if not opts:
                        return False
                    val_norm = str(value).strip().lower()
                    opts_norm = [o.lower() for o in opts]
                    if val_norm in opts_norm:
                        return True
                    # Try numeric equality if both look like integers
                    try:
                        val_int = int(val_norm)
                        for o in opts:
                            try:
                                if int(o) == val_int:
                                    return True
                            except Exception:
                                continue
                    except Exception:
                        pass
                    return False
                except Exception:
                    return False

            if size and prod_sizes:
                if not _matches_option(size, prod_sizes):
                    app_logger.info(
                        f"Add_to_cart: provided size='{size}' does not match allowed sizes='{prod_sizes}' for item_id={menu_item_id}"
                    )
                    size = None
            if color and prod_colors:
                if not _matches_option(color, prod_colors):
                    app_logger.info(
                        f"Add_to_cart: provided color='{color}' does not match allowed colors='{prod_colors}' for item_id={menu_item_id}"
                    )
                    color = None
        except Exception:
            # Be conservative: if anything fails during validation, just ignore
            # the provided size/color rather than erroring out.
            size = None
            color = None

        # Enforce required selection: if product defines sizes or colors, require user to select them
        try:
            prod_has_sizes = bool(prod_sizes and str(prod_sizes).strip())
            prod_has_colors = bool(prod_colors and str(prod_colors).strip())
            if prod_has_sizes and not size:
                if request.is_json:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": "Iltimos, mahsulot uchun o'lchamni tanlang",
                            }
                        ),
                        400,
                    )
                flash("Iltimos, mahsulot uchun o'lchamni tanlang.", "error")
                return redirect(url_for("menu"))
            if prod_has_colors and not color:
                if request.is_json:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "message": "Iltimos, mahsulot uchun rangni tanlang",
                            }
                        ),
                        400,
                    )
                flash("Iltimos, mahsulot uchun rangni tanlang.", "error")
                return redirect(url_for("menu"))
        except Exception:
            # If anything goes wrong determining requirements, fall back to permissive behavior
            pass

        session_id = get_session_id()
        user_id = session.get("user_id")

        # Check if item already exists in cart - treat same size/color as same line
        if user_id:
            existing_item = execute_query(
                "SELECT id, quantity FROM cart_items WHERE user_id = ? AND menu_item_id = ? AND COALESCE(size,'') = COALESCE(?, '') AND COALESCE(color,'') = COALESCE(?, '')",
                (user_id, menu_item_id, size or "", color or ""),
                fetch_one=True,
            )
        else:
            existing_item = execute_query(
                "SELECT id, quantity FROM cart_items WHERE session_id = ? AND menu_item_id = ? AND COALESCE(size,'') = COALESCE(?, '') AND COALESCE(color,'') = COALESCE(?, '')",
                (session_id, menu_item_id, size or "", color or ""),
                fetch_one=True,
            )

        now = get_current_time().isoformat()

        if existing_item:
            # Update existing item
            existing_id = (
                existing_item.get("id")
                if isinstance(existing_item, dict)
                else existing_item[0]
            )
            if existing_id:
                execute_query(
                    "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
                    (quantity, existing_id),
                )
        else:
            # Add new item (persist chosen size/color)
            if user_id:
                execute_query(
                    "INSERT INTO cart_items (user_id, session_id, menu_item_id, quantity, size, color, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        session_id,
                        menu_item_id,
                        quantity,
                        size or None,
                        color or None,
                        now,
                    ),
                )
            else:
                execute_query(
                    "INSERT INTO cart_items (session_id, menu_item_id, quantity, size, color, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        session_id,
                        menu_item_id,
                        quantity,
                        size or None,
                        color or None,
                        now,
                    ),
                )

        # Get updated cart count - safe handling
        try:
            if user_id:
                cart_count_result = execute_query(
                    "SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_id = ?",
                    (user_id,),
                    fetch_one=True,
                )
            else:
                cart_count_result = execute_query(
                    "SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE session_id = ?",
                    (session_id,),
                    fetch_one=True,
                )

            cart_count = (
                int(cart_count_result[0])
                if cart_count_result and cart_count_result[0] is not None
                else 0
            )
        except Exception as count_error:
            app_logger.warning(f"Cart count error: {str(count_error)}")
            cart_count = 0

        # Clear cache for cart count (safe)
        try:
            cm2 = cache_manager or get_cache_manager()
        except Exception:
            cm2 = None
        if cm2:
            try:
                if user_id:
                    cm2.delete(f"cart_count_{user_id}")
                else:
                    cm2.delete(f"cart_count_{session_id}")
            except Exception:
                pass

        if request.is_json:
            return jsonify(
                {
                    "success": True,
                    "message": "Mahsulot savatchaga qo'shildi",
                    "cart_count": cart_count,
                }
            )

        flash("Mahsulot savatchaga qo'shildi!", "success")
        return redirect(url_for("menu"))

    except Exception as e:
        app_logger.error(f"Add to cart error: {str(e)}")
        if request.is_json:
            return jsonify({"success": False, "message": "Xatolik yuz berdi"})
        flash("Savatchaga qo'shishda xatolik yuz berdi.", "error")
        return redirect(url_for("menu"))


@app.route("/cart")
def cart():
    session_id = get_session_id()
    user_id = session.get("user_id")

    try:
        # Agar xodim, kuryer yoki admin cart sahifasiga kirishga harakat qilsa
        if (
            session.get("staff_id")
            or session.get("courier_id")
            or session.get("super_admin")
        ):
            flash("Savatcha faqat foydalanuvchilar uchun mo'ljallangan.", "warning")
            return redirect(url_for("menu"))

        # Foydalanuvchi ma'lumotlarini olish va session ga yuklash
        if (
            user_id
            and not session.get("staff_id")
            and not session.get("courier_id")
            and not session.get("super_admin")
        ):
            user_profile = execute_query(
                "SELECT phone, address, address_latitude, address_longitude, first_name, last_name FROM users WHERE id = ?",
                (user_id,),
                fetch_one=True,
            )

            if user_profile:
                session["user_phone"] = user_profile.get("phone", "") or ""
                session["user_address"] = user_profile.get("address", "") or ""
                session["user_address_latitude"] = user_profile.get("address_latitude")
                session["user_address_longitude"] = user_profile.get(
                    "address_longitude"
                )
                session["user_first_name"] = user_profile.get("first_name", "") or ""
                session["user_last_name"] = user_profile.get("last_name", "") or ""

        # Savatcha ma'lumotlarini olish
        cart_items = get_cart_items(
            None, session_id, user_id
        )  # Pass None for conn, as get_cart_items handles connection
        total = get_cart_total(None, session_id, user_id)  # Pass None for conn

        return render_template(
            "cart.html", cart_items=cart_items or [], total=total or 0
        )

    except Exception as e:
        app_logger.error(f"Cart sahifasida xatolik: {str(e)}")
        return render_template("cart.html", cart_items=[], total=0)


# Backwards-compatible alias: some templates/code call url_for('view_cart')
# Keep a lightweight redirect so existing links don't break.
@app.route("/view_cart")
def view_cart():
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:cart_item_id>", methods=["POST"])
def remove_from_cart(cart_item_id):
    session_id = get_session_id()
    user_id = session.get("user_id")

    try:
        if user_id:
            execute_query(
                "DELETE FROM cart_items WHERE id = ? AND user_id = ?",
                (cart_item_id, user_id),
            )
        else:
            execute_query(
                "DELETE FROM cart_items WHERE id = ? AND session_id = ?",
                (cart_item_id, session_id),
            )

        # Clear cache for cart count
        if user_id:
            cache_manager.delete(f"cart_count_{user_id}")
        else:
            cache_manager.delete(f"cart_count_{session_id}")

        flash("Mahsulot savatchadan olib tashlandi.", "success")
    except Exception as e:
        app_logger.error(f"Remove from cart error: {str(e)}")
        flash("Mahsulotni olib tashlashda xatolik.", "error")

    return redirect(url_for("cart"))


@app.route("/favorites")
def favorites():
    "Foydalanuvchi sevimli mahsulotlari - faqat foydalanuvchilar uchun"
    # Faqat oddiy foydalanuvchilar kirishi mumkin
    if not session.get("user_id"):
        flash(
            "Sevimlilar ro'yxatini ko'rish uchun foydalanuvchi sifatida tizimga kiring.",
            "warning",
        )
        return redirect(url_for("login_page"))

    # Xodim, kuryer yoki super admin kirishini bloklash
    if (
        session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        flash("Sevimlilar faqat foydalanuvchilar uchun mo'ljallangan.", "error")
        return redirect(url_for("index"))

    try:
        user_id = session.get("user_id")

        # Sevimli mahsulotlarni olish
        favorite_items_raw = execute_query(
            """
            SELECT m.*, f.created_at as favorite_added
            FROM menu_items m
            JOIN favorites f ON m.id = f.menu_item_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            """,
            (user_id,),
            fetch_all=True,
        )
        favorite_items = (
            [dict(row) for row in favorite_items_raw] if favorite_items_raw else []
        )

        return render_template(
            "favorites.html", favorites=favorite_items, current_page="favorites"
        )

    except Exception as e:
        app_logger.error(f"Favorites sahifasida xatolik: {str(e)}")
        flash("Sevimlilar ro'yxatini yuklashda xatolik yuz berdi.", "error")
        return redirect(url_for("index"))


@app.route("/add-to-favorites/<int:menu_item_id>", methods=["POST"])
def add_to_favorites(menu_item_id):
    "Mahsulotni sevimlilarga qo'shish - faqat foydalanuvchilar uchun"
    # Faqat oddiy foydalanuvchilar sevimli qo'sha oladi
    if not session.get("user_id"):
        return jsonify(
            {"success": False, "message": "Foydalanuvchi sifatida tizimga kiring"}
        )

    # Xodim, kuryer yoki admin kirishini bloklash
    if (
        session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify(
            {"success": False, "message": "Sevimlilar faqat foydalanuvchilar uchun"}
        )

    try:
        user_id = session.get("user_id")

        # Allaqachon sevimli emasligini tekshirish
        existing_favorite = execute_query(
            "SELECT id FROM favorites WHERE user_id = ? AND menu_item_id = ?",
            (user_id, menu_item_id),
            fetch_one=True,
        )
        if existing_favorite:
            return jsonify(
                {"success": False, "message": "Bu mahsulot allaqachon sevimlilarda"}
            )

        # Sevimlilarga qo'shish
        now = get_current_time().isoformat()
        try:
            execute_query(
                "INSERT INTO favorites (user_id, menu_item_id, created_at) VALUES (?, ?, ?)",
                (user_id, menu_item_id, now),
            )
        except Exception as e:
            # If FK constraint fails in test/dev (no matching user/menu item), return friendly error
            if "FOREIGN KEY constraint failed" in str(e):
                app_logger.warning(f"Favorites insert FK failed: {e}")
                return jsonify(
                    {
                        "success": False,
                        "message": "Could not add favorite: invalid user or item",
                    }
                )
            raise

        return jsonify({"success": True, "message": "Sevimlilar ro'yxatiga qo'shildi"})

    except Exception as e:
        app_logger.error(f"Add to favorites error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})


@app.route("/remove-from-favorites/<int:menu_item_id>", methods=["POST"])
def remove_from_favorites(menu_item_id):
    "Mahsulotni sevimlilardan olib tashlash - faqat foydalanuvchilar uchun"
    # Faqat oddiy foydalanuvchilar sevimli olib tashlashi mumkin
    if not session.get("user_id"):
        return jsonify(
            {"success": False, "message": "Foydalanuvchi sifatida tizimga kiring"}
        )

    # Xodim, kuryer yoki admin kirishini bloklash
    if (
        session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify(
            {"success": False, "message": "Sevimlilar faqat foydalanuvchilar uchun"}
        )

    try:
        user_id = session.get("user_id")

        execute_query(
            "DELETE FROM favorites WHERE user_id = ? AND menu_item_id = ?",
            (user_id, menu_item_id),
        )

        return jsonify({"success": True, "message": "Sevimlilardan olib tashlandi"})

    except Exception as e:
        app_logger.error(f"Remove from favorites error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})


# ---- USER LOGIN & REGISTER ----


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([first_name, last_name, email, password, confirm_password]):
            flash("Majburiy maydonlarni to'ldiring.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Parollar mos kelmaydi.", "error")
            return redirect(url_for("register"))

        # Email mavjudligini tekshirish
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = ?", (email,), fetch_one=True
        )
        if existing_user:
            flash("Bu email allaqachon ro'yxatdan o'tgan.", "error")
            return redirect(url_for("register"))

        # Xarita koordinatalari
        address_latitude = request.form.get("address_latitude", "")
        address_longitude = request.form.get("address_longitude", "")

        # Yangi foydalanuvchi yaratish
        password_hash = generate_password_hash(password)
        now = get_current_time().isoformat()

        try:
            user_id = execute_query(
                """
                INSERT INTO users (first_name, last_name, email, phone, address, password_hash, created_at, address_latitude, address_longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    first_name,
                    last_name,
                    email,
                    phone,
                    address,
                    password_hash,
                    now,
                    address_latitude or None,
                    address_longitude or None,
                ),
            )

            # Session ma'lumotlarini yangilash
            session["user_id"] = user_id
            session["user_name"] = f"{first_name} {last_name}".strip()
            session["user_email"] = email
            session["interface_language"] = "uz"  # Default til
            session["font_size"] = "medium"  # Default font size
            session["dark_theme"] = True  # Default theme

            flash(
                f"Muvaffaqiyatli ro'yxatdan o'tdingiz! Xush kelibsiz, {first_name}!",
                "success",
            )
            return redirect(url_for("index"))

        except Exception as e:
            app_logger.error(f"User registration error: {str(e)}")
            flash("Ro'yxatdan o'tishda xatolik yuz berdi.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/profile")
def profile():
    # Allow viewing profile for any authenticated principal (user, staff, courier, super_admin)
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        flash("Profilni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("login_page"))

    try:
        user = None
        orders = []
        sessions_list = []  # Initialize sessions_list for all cases

        # Prefer staff/courier detection first: session may contain multiple ids (e.g., user_id left set)
        is_staff = bool(session.get("staff_id"))
        is_courier = bool(session.get("courier_id"))
        is_user = bool(session.get("user_id"))
        is_super = bool(session.get("super_admin"))

        # Priority order: super_admin > staff > courier > user (to avoid conflicts)
        if is_super:
            is_staff = is_courier = is_user = False
        elif is_staff:
            is_courier = is_user = False
        elif is_courier:
            is_user = False

        # Regular user: load full profile + recent orders
        if is_user:
            uid = session.get("user_id")
            user_row = execute_query(
                "SELECT * FROM users WHERE id = ?", (uid,), fetch_one=True
            )
            if user_row:
                # Prioritize database avatar over session avatar
                avatar_url = (
                    user_row.get("avatar") or "/static/images/default-avatar.svg"
                )
                # Update session with current avatar from database
                session["user_avatar"] = avatar_url

                user = {
                    "first_name": user_row.get("first_name") or "",
                    "last_name": user_row.get("last_name") or "",
                    "email": user_row.get("email") or session.get("user_email", ""),
                    "phone": user_row.get("phone") or session.get("user_phone", ""),
                    "address": user_row.get("address")
                    or session.get("user_address", ""),
                    "avatar": avatar_url,
                    "card_number": user_row.get("card_number")
                    or session.get("user_card_number", ""),
                }

            orders_raw = execute_query(
                """
                SELECT o.*, COALESCE(r.total_amount, 0) as total_amount,
                       GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
                FROM orders o
                LEFT JOIN receipts r ON o.id = r.order_id
                LEFT JOIN order_details od ON o.id = od.order_id
                LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
                WHERE o.user_id = ?
                GROUP BY o.id
                ORDER BY o.created_at DESC
                LIMIT 50
                """,
                (uid,),
                fetch_all=True,
            )
            orders = [dict(r) for r in orders_raw] if orders_raw else []
            # Load active sessions for this user
            try:
                sessions_list = get_user_sessions(uid)
            except Exception:
                sessions_list = []

        # Staff profile
        elif is_staff:
            sid = session.get("staff_id")
            staff = execute_query(
                "SELECT * FROM staff WHERE id = ?", (sid,), fetch_one=True
            )
            if staff:
                user = {
                    "first_name": staff.get("first_name") or "",
                    "last_name": staff.get("last_name") or "",
                    "email": staff.get("email") or session.get("staff_email", ""),
                    "phone": staff.get("phone") or session.get("staff_phone", ""),
                    "address": staff.get("address") or "",
                    "avatar": staff.get("avatar")
                    or session.get("staff_avatar")
                    or session.get("user_avatar")
                    or "/static/images/default-avatar.svg",
                }
            else:
                user = {
                    "first_name": session.get("staff_name", ""),
                    "last_name": "",
                    "email": session.get("staff_email", ""),
                    "phone": session.get("staff_phone", ""),
                    "address": "",
                    "avatar": session.get("staff_avatar")
                    or session.get("user_avatar")
                    or "/static/images/default-avatar.svg",
                }

        # Courier profile
        elif is_courier:
            cid = session.get("courier_id")
            courier = execute_query(
                "SELECT * FROM couriers WHERE id = ?", (cid,), fetch_one=True
            )
            if courier:
                user = {
                    "first_name": courier.get("first_name") or "",
                    "last_name": courier.get("last_name") or "",
                    "email": courier.get("email") or session.get("courier_email", ""),
                    "phone": courier.get("phone") or session.get("courier_phone", ""),
                    "address": courier.get("address") or "",
                    "avatar": courier.get("avatar")
                    or session.get("courier_avatar")
                    or session.get("user_avatar")
                    or "/static/images/default-avatar.svg",
                }
            else:
                user = {
                    "first_name": session.get("courier_name", ""),
                    "last_name": "",
                    "email": session.get("courier_email", ""),
                    "phone": session.get("courier_phone", ""),
                    "address": "",
                    "avatar": session.get("courier_avatar")
                    or session.get("user_avatar")
                    or "/static/images/default-avatar.svg",
                }

        # Super admin: profile from persistent settings
        elif is_super:
            creds = get_superadmin_creds()
            # Update session with current avatar from settings
            persistent_avatar = (
                creds.get("avatar") or "/static/images/default-avatar.svg"
            )
            session["user_avatar"] = persistent_avatar

            user = {
                "first_name": creds.get("first_name", "")
                or (
                    (session.get("user_name", "") or "").split(" ")[0]
                    if session.get("user_name")
                    else "Super"
                ),
                "last_name": creds.get("last_name", "")
                or (
                    " ".join((session.get("user_name", "") or "").split(" ")[1:])
                    if session.get("user_name")
                    else ""
                ),
                "email": session.get("user_email", ""),
                "phone": creds.get("phone", "") or session.get("user_phone", ""),
                "address": session.get("user_address", ""),
                "avatar": persistent_avatar,
            }

        return render_template(
            "profile.html",
            user=user,
            orders=orders,
            sessions=sessions_list if is_user else [],
        )

    except Exception as e:
        app_logger.error(f"Profile sahifasida xatolik: {str(e)}")
        flash("Profilni yuklashda xatolik yuz berdi.", "error")
        return redirect(url_for("index"))


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    card_number_new = request.form.get("card_number", "").strip()
    avatar_file = None
    try:
        avatar_file = request.files.get("avatar")
    except Exception:
        avatar_file = None

    if not all([first_name, last_name, email]):
        flash("Ism, familiya va email majburiy.", "error")
        return redirect(url_for("profile"))

    # Email takrorlanishini tekshirish
    existing_user = execute_query(
        "SELECT id FROM users WHERE email = ? AND id != ?",
        (email, user_id),
        fetch_one=True,
    )
    if existing_user:
        flash("Bu email allaqachon ishlatilmoqda.", "error")
        return redirect(url_for("profile"))

    # Ma'lumotlarni yangilash
    try:
        # Ensure avatar column exists
        try:
            raw = execute_query("PRAGMA table_info(users);", fetch_all=True) or []
            cols = []
            for c in raw:
                try:
                    # row may be dict-like or tuple
                    if isinstance(c, dict) and "name" in c:
                        cols.append(c["name"])
                    elif isinstance(c, (list, tuple)) and len(c) >= 2:
                        cols.append(c[1])
                except Exception:
                    continue
        except Exception:
            cols = []
        if "avatar" not in cols:
            try:
                execute_query("ALTER TABLE users ADD COLUMN avatar TEXT;")
            except Exception:
                pass

        # Build update dynamically
        update_fields = ["first_name = ?", "last_name = ?", "email = ?", "phone = ?"]
        params = [first_name, last_name, email, phone]

        if card_number_new:
            update_fields.append("card_number = ?")
            params.append(card_number_new)

        avatar_path = None
        if avatar_file and avatar_file.filename:
            from werkzeug.utils import secure_filename

            filename = secure_filename(avatar_file.filename)
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext in app.config.get(
                "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"}
            ):
                unique_name = f"avatar_{uuid.uuid4().hex}.{ext}"
                save_path = os.path.join(
                    app.config.get("UPLOAD_FOLDER", "static/uploads"), unique_name
                )
                try:
                    avatar_file.save(save_path)
                    avatar_path = "/" + save_path.replace("\\", "/")
                    update_fields.append("avatar = ?")
                    params.append(avatar_path)
                except Exception as e:
                    app_logger.warning(f"Avatar save failed: {str(e)}")

        params.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        execute_query(query, tuple(params))

        # Session ma'lumotlarini yangilash
        session["user_name"] = f"{first_name} {last_name}".strip()
        session["user_email"] = email
        if card_number_new:
            session["user_card_number"] = card_number_new
        if avatar_path:
            session["user_avatar"] = avatar_path

        flash("Profil muvaffaqiyatli yangilandi!", "success")
    except Exception as e:
        app_logger.error(f"Update profile error: {str(e)}")
        flash("Profilni yangilashda xatolik yuz berdi.", "error")

    return redirect(url_for("profile"))


@app.route("/api/terminate-session", methods=["POST"])
def api_terminate_session():
    """Terminate another active session by its session_id. User can only terminate their own sessions."""
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    sid = data.get("session_id")
    if not sid:
        return jsonify({"error": "session_id required"}), 400

    # Prevent terminating session that does not belong to the user
    user_sessions = get_user_sessions(session.get("user_id"))
    allowed = any(s.get("session_id") == sid for s in user_sessions)
    if not allowed:
        return jsonify({"error": "Forbidden"}), 403

    success = terminate_session(sid, current_session_id=session.get("session_id"))
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to terminate session"}), 500


@app.route("/api/terminate-all-sessions", methods=["POST"])
def api_terminate_all_sessions():
    """Terminate all sessions for the current user. This will log the user out everywhere."""
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = session.get("user_id")
        sessions = get_user_sessions(user_id)
        current_sid = session.get("session_id")
        failed = []
        for s in sessions:
            sid = s.get("session_id")
            try:
                terminate_session(sid, current_session_id=current_sid)
            except Exception as e:
                app_logger.warning(
                    f"Failed to terminate session {sid} for user {user_id}: {e}"
                )
                failed.append(sid)

        # Always clear current session to force logout
        session.clear()

        if failed:
            return (
                jsonify(
                    {"success": False, "error": "Some sessions could not be terminated"}
                ),
                500,
            )
        return jsonify({"success": True})
    except Exception as e:
        app_logger.error(f"api_terminate_all_sessions error: {e}")
        return jsonify({"success": False, "error": "Internal error"}), 500


@app.route("/update_address", methods=["POST"])
def update_address():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login_page"))

    user_id = session.get("user_id")
    address = request.form.get("address", "").strip()
    address_latitude = request.form.get("address_latitude", "")
    address_longitude = request.form.get("address_longitude", "")

    if not address:
        flash("Manzilni xaritadan tanlang.", "error")
        return redirect(url_for("profile"))

    try:
        # Manzilni yangilash
        execute_query(
            """
            UPDATE users
            SET address = ?, address_latitude = ?, address_longitude = ?
            WHERE id = ?
        """,
            (address, address_latitude or None, address_longitude or None, user_id),
        )

        # Session ma'lumotlarini yangilash
        session["user_address"] = address
        session["user_address_latitude"] = address_latitude or None
        session["user_address_longitude"] = address_longitude or None

        flash("Manzil muvaffaqiyatli yangilandi!", "success")
    except Exception as e:
        app_logger.error(f"Update address error: {str(e)}")
        flash("Manzilni yangilashda xatolik yuz berdi.", "error")

    return redirect(url_for("profile"))


@app.route("/change_password", methods=["POST"])
def change_password():
    # Har qanday turdagi foydalanuvchi parolini o'zgartirishi mumkin
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("index"))

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not all([current_password, new_password, confirm_password]):
        flash("Barcha parol maydonlarini to'ldiring.", "error")
        return redirect(url_for("profile_settings"))

    if new_password != confirm_password:
        flash("Yangi parollar mos kelmaydi.", "error")
        return redirect(url_for("profile_settings"))

    if len(new_password) < 6:
        flash("Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak.", "error")
        return redirect(url_for("profile_settings"))

    try:
        # Foydalanuvchi turiga qarab parol hash ni olish va yangilash
        current_hash = None

        if session.get("user_id"):
            # Oddiy foydalanuvchi
            user_data = execute_query(
                "SELECT password_hash FROM users WHERE id = ?",
                (session.get("user_id"),),
                fetch_one=True,
            )
            current_hash = user_data.get("password_hash") if user_data else None
            table = "users"
            user_id = session.get("user_id")

        elif session.get("staff_id"):
            # Xodim
            staff_data = execute_query(
                "SELECT password_hash FROM staff WHERE id = ?",
                (session.get("staff_id"),),
                fetch_one=True,
            )
            current_hash = staff_data.get("password_hash") if staff_data else None
            table = "staff"
            user_id = session.get("staff_id")

        elif session.get("courier_id"):
            # Kuryer
            courier_data = execute_query(
                "SELECT password_hash FROM couriers WHERE id = ?",
                (session.get("courier_id"),),
                fetch_one=True,
            )
            current_hash = courier_data.get("password_hash") if courier_data else None
            table = "couriers"
            user_id = session.get("courier_id")

        elif session.get("super_admin"):
            # Super admin - faqat session uchun parolni tekshirish
            if current_password == Config.SUPER_ADMIN_PASSWORD:
                flash(
                    "Super admin paroli tizim sozlamalari orqali o'zgartiriladi.",
                    "warning",
                )
                return redirect(url_for("profile_settings"))
            else:
                flash("Joriy super admin paroli noto'g'ri.", "error")
                return redirect(url_for("profile_settings"))

        if not current_hash:
            flash("Foydalanuvchi ma'lumotlari topilmadi.", "error")
            return redirect(url_for("profile_settings"))

        # Joriy parolni tekshirish
        if not check_password_hash(current_hash, current_password):
            flash("Joriy parol noto'g'ri.", "error")
            return redirect(url_for("profile_settings"))

        # Yangi parolni saqlash
        new_password_hash = generate_password_hash(new_password)
        execute_query(
            f"UPDATE {table} SET password_hash = ? WHERE id = ?",
            (new_password_hash, user_id),
        )

        flash("Parol muvaffaqiyatli o'zgartirildi!", "success")
        app_logger.info(f"Password changed for {table} user ID: {user_id}")

    except Exception as e:
        app_logger.error(f"Change password error: {str(e)}")
        flash("Parolni o'zgartirishda xatolik yuz berdi.", "error")

    return redirect(url_for("profile_settings"))


@app.route("/profile/settings")
def profile_settings():
    # Har qanday turdagi foydalanuvchi (user, staff, courier, super_admin) kirishi mumkin
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        flash("Profil sozlamalarini ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    # Provide current values with safe defaults so template inputs work
    profile_settings_data = {
        "interface_language": session.get("interface_language", "uz"),
        "font_size": session.get("font_size", "medium"),
        "dark_theme": bool(session.get("dark_theme", True)),
        "user_name": session.get("user_name", ""),
        "user_email": session.get("user_email", ""),
    }

    # If logged in as user, try to populate from DB
    if session.get("user_id"):
        try:
            user_row = execute_query(
                "SELECT first_name, last_name, email, phone, address, interface_language, font_size, dark_theme FROM users WHERE id = ?",
                (session.get("user_id"),),
                fetch_one=True,
            )
            if user_row:
                profile_settings_data.update(
                    {
                        "user_name": f"{user_row.get('first_name','')} {user_row.get('last_name','')}".strip(),
                        "user_email": user_row.get("email")
                        or profile_settings_data["user_email"],
                        "interface_language": user_row.get(
                            "interface_language",
                            profile_settings_data["interface_language"],
                        ),
                        "font_size": user_row.get(
                            "font_size", profile_settings_data["font_size"]
                        ),
                        "dark_theme": bool(
                            user_row.get(
                                "dark_theme", profile_settings_data["dark_theme"]
                            )
                        ),
                    }
                )
        except Exception:
            app_logger.exception("Failed to load user profile for settings")

    return render_template("profile_settings.html", settings=profile_settings_data)


@app.route("/settings")
def general_settings():
    # Har qanday turdagi foydalanuvchi (user, staff, courier, super_admin) kirishi mumkin
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        flash("Umumi sozlamalarni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    # Provide a safe system_config payload
    system_config = session.get("system_config", {})
    default_system_config = {
        "maxOrdersPerHour": int(system_config.get("maxOrdersPerHour", 100)),
        "sessionTimeout": int(system_config.get("sessionTimeout", 120)),
        "rateLimit": int(system_config.get("rateLimit", 1000)),
        "updated_at": system_config.get("updated_at", get_current_time().isoformat()),
    }

    # Ensure CSRF token available for forms/ajax
    # CSRF helpers are defined earlier to be available at import-time
    try:
        csrf = generate_csrf_token()
    except Exception:
        # Fallback: generate a token here if helper isn't available for some reason
        import secrets as _secrets

        token = _secrets.token_urlsafe(32)
        session.setdefault("csrf_token", token)
        csrf = token

    return render_template(
        "general_settings.html", system_config=default_system_config, csrf_token=csrf
    )


@app.route("/settings", methods=["POST"])
@csrf_protect
def general_settings_post():
    # Save posted system/user settings into session and persist for super_admin
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        flash("Umumi sozlamalarni o'zgartirish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    # Accept both form and JSON
    data = request.get_json(silent=True) or request.form.to_dict()

    try:
        # Normalize and store into session
        if "maxOrdersPerHour" in data:
            try:
                session.setdefault("system_config", {})["maxOrdersPerHour"] = int(
                    data.get("maxOrdersPerHour", 100)
                )
            except Exception:
                pass

        if "sessionTimeout" in data:
            try:
                session.setdefault("system_config", {})["sessionTimeout"] = int(
                    data.get("sessionTimeout", 120)
                )
            except Exception:
                pass

        if "rateLimit" in data:
            try:
                session.setdefault("system_config", {})["rateLimit"] = int(
                    data.get("rateLimit", 1000)
                )
            except Exception:
                pass

        # UI prefs for logged in users
        if "theme" in data:
            val = data.get("theme")
            if isinstance(val, str):
                session["dark_theme"] = val.lower() == "dark"
            else:
                session["dark_theme"] = bool(val)

        if "font_size" in data:
            session["font_size"] = data.get("font_size") or session.get(
                "font_size", "medium"
            )

        if "language" in data:
            session["interface_language"] = data.get("language") or session.get(
                "interface_language", "uz"
            )

        # Persist system_config if super_admin
        if session.get("super_admin"):
            try:
                with open("superadmin_settings.json", "w", encoding="utf-8") as f:
                    json.dump(
                        session.get("system_config", {}),
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
            except Exception as e:
                app_logger.warning(f"Could not persist super admin settings file: {e}")

        # Persist user prefs to users table if user logged in
        user_id = session.get("user_id")
        if user_id:
            try:
                execute_query(
                    "UPDATE users SET dark_theme = ?, font_size = ?, interface_language = ? WHERE id = ?",
                    (
                        1 if session.get("dark_theme") else 0,
                        session.get("font_size", "medium"),
                        session.get("interface_language", "uz"),
                        user_id,
                    ),
                )
            except Exception as e:
                app_logger.warning(f"Could not persist user settings to DB: {e}")

        # If this was an AJAX/JSON request, return JSON so frontend can handle it
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return jsonify({"success": True, "message": "Sozlamalar saqlandi."})

        flash("Sozlamalar saqlandi.", "success")
        return redirect(url_for("general_settings"))

    except Exception as e:
        app_logger.error(f"general_settings_post error: {e}")
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return (
                jsonify(
                    {"success": False, "message": "Sozlamalarni saqlashda xatolik."}
                ),
                500,
            )
        flash("Sozlamalarni saqlashda xatolik.", "error")
        return redirect(url_for("general_settings"))


def generate_csrf_token():
    """Generate or return existing CSRF token stored in session."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_protect(fn):
    """Simple CSRF protection decorator for POST endpoints that checks token in form/json headers."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            # Check token in header first, then json body, then form
            header = request.headers.get("X-CSRF-Token")
            token = (
                header
                or (request.get_json(silent=True) or {}).get("csrf_token")
                or request.form.get("csrf_token")
            )
            if not token or token != session.get("csrf_token"):
                app_logger.warning("CSRF token mismatch or missing")
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "CSRF token missing or invalid"}), 403
                flash("CSRF token noto'g'ri yoki yo'q", "error")
                return redirect(request.referrer or url_for("index"))
        return fn(*args, **kwargs)

    return wrapper


@app.route("/logout")
def logout():
    user_name = session.get("user_name", "")

    # Terminate the session in database if session_id exists
    current_session_id = session.get("session_id")
    if current_session_id:
        try:
            terminate_session(current_session_id, current_session_id=current_session_id)
        except Exception as e:
            app_logger.warning(f"Failed to terminate session in database: {e}")

    session.clear()
    flash(f"Tizimdan chiqdingiz. Xayr, {user_name}!", "info")
    return redirect(url_for("index"))


# ---- PLACE ORDER ----
@app.route("/place_order", methods=["POST"])
@app.route("/place-order", methods=["POST"])
def place_order():
    "Buyurtma berish funksiyasi - to'liq qayta ishlangan"
    try:
        # Rate limiting
        identifier = request.remote_addr
        if not rate_limiter.is_allowed(identifier, 500, 60):  # 500 заказов в минуту
            flash("Juda ko'p buyurtma. Biroz kuting.", "error")
            return redirect(url_for("cart"))

        # Foydalanuvchi session'dan ismni olish
        if not session.get("user_id"):
            flash("Buyurtma berish uchun avval tizimga kiring.", "error")
            return redirect(url_for("login_page"))

        name = session.get("user_name", "")
        user_id = session.get("user_id")

        if not name:
            flash("Foydalanuvchi ma'lumotlari topilmadi.", "error")
            return redirect(url_for("login_page"))

        # Ma'lumotlar bazasi bilan ishash
        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Foydalanuvchi profilidan ma'lumotlarni olish
            user_profile = execute_query(
                "SELECT phone, address, card_number FROM users WHERE id = ?",
                (user_id,),
                fetch_one=True,
            )

            # Session ga profil ma'lumotlarini saqlash
            if user_profile:
                session["user_phone"] = user_profile.get("phone", "") or ""
                session["user_address"] = user_profile.get("address", "") or ""
                session["user_card_number"] = user_profile.get("card_number", "") or ""

            session_id = get_session_id()

            # Savatchani tekshirish
            cart_items = get_cart_items(conn, session_id, user_id)

            if not cart_items or len(cart_items) == 0:
                flash("Savatchangiz bo'sh. Avval taom tanlang.", "error")
                return redirect(url_for("menu"))

            # Formdan ma'lumotlarni xavfsiz olish
            # Default to delivery since in-store pickup was removed from UI
            order_type = request.form.get("order_type", "delivery")
            delivery_address = request.form.get("delivery_address", "").strip()
            home_address = request.form.get("home_address", "").strip()
            customer_phone_new = request.form.get("customer_phone", "").strip()
            card_number_new = request.form.get("card_number", "").strip()

            # Delivery uchun kerakli tekshiruvlar
            if order_type == "delivery":
                if not delivery_address:
                    flash("Yetkazib berish manzilini kiriting!", "error")
                    return redirect(url_for("cart"))

                # Telefon tekshiruvi
                if not session.get("user_phone") and not customer_phone_new:
                    flash("Telefon raqamingizni kiriting!", "error")
                    return redirect(url_for("cart"))

            # Foydalanuvchi profilini yangilash
            if home_address:
                execute_query(
                    "UPDATE users SET address = ? WHERE id = ?", (home_address, user_id)
                )
                session["user_address"] = home_address
            if customer_phone_new:
                execute_query(
                    "UPDATE users SET phone = ? WHERE id = ?",
                    (customer_phone_new, user_id),
                )
                session["user_phone"] = customer_phone_new
            if card_number_new:
                execute_query(
                    "UPDATE users SET card_number = ? WHERE id = ?",
                    (card_number_new, user_id),
                )
                session["user_card_number"] = card_number_new

            # Buyurtma raqami va vaqt hisoblash
            tno = next_ticket_no(conn)
            eta_minutes = calc_eta_minutes(conn)
            now = get_current_time()
            eta_time = now + datetime.timedelta(minutes=eta_minutes)
            total = get_cart_total(conn, session_id, user_id)

            # Delivery uchun qo'shimcha ma'lumotlar
            delivery_latitude = request.form.get("delivery_latitude", "")
            delivery_longitude = request.form.get("delivery_longitude", "")
            delivery_distance = request.form.get("delivery_distance", 0)
            delivery_map_url = request.form.get("delivery_map_url", "")
            customer_note = request.form.get("customer_note", "")

            # Telefon va karta ma'lumotlarini olish
            customer_phone = session.get("user_phone", "") or customer_phone_new
            card_number = session.get("user_card_number", "") or card_number_new

            # Payment method handling: default to cash; only require card if selected
            payment_method = request.form.get("payment_method", "cash") or "cash"
            if payment_method in ("card", "online") and not card_number:
                flash(
                    "Tanlangan to'lov usuli uchun karta ma'lumotlari talab qilinadi. Iltimos, karta ma'lumotlarini kiriting.",
                    "error",
                )
                return redirect(url_for("cart"))

            # Masofa va vaqtni xavfsiz aylantirish
            try:
                delivery_distance = float(delivery_distance) if delivery_distance else 0
            except (ValueError, TypeError):
                delivery_distance = 0

            # Delivery uchun ETA ni qayta hisoblash
            if order_type == "delivery":
                courier_delivery_time = 30
                eta_time = now + datetime.timedelta(
                    minutes=eta_minutes + courier_delivery_time
                )

            # Branch ID ni xavfsiz olish
            branch_id = 1
            try:
                branch_id_str = request.form.get("branch_id", "1")
                branch_id = int(branch_id_str) if branch_id_str else 1
            except (ValueError, TypeError):
                branch_id = 1

            # Buyurtma yaratish
            order_id = execute_query(
                """
                INSERT INTO orders (user_id, customer_name, ticket_no, order_type, status, delivery_address, delivery_distance, delivery_latitude, delivery_longitude, delivery_map_url, customer_note, customer_phone, card_number, branch_id, created_at, eta_time)
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    user_id,
                    name,
                    tno,
                    order_type,
                    delivery_address,
                    delivery_distance,
                    delivery_latitude or None,
                    delivery_longitude or None,
                    delivery_map_url,
                    customer_note,
                    customer_phone,
                    card_number,
                    branch_id,
                    now.isoformat(),
                    eta_time.isoformat(),
                ),
            )

            if not order_id:
                raise Exception("Buyurtma yaratilmadi.")

            # Log yangi buyurtma yaratilganini
            app_logger.info(
                f"Yangi buyurtma yaratildi: ID={order_id}, Ticket={tno}, User={name}, Type={order_type}, Status=waiting"
            )

            # Savatchadagi mahsulotlarni order_details ga ko'chirish
            order_items_for_json = []
            total_amount = 0

            for item in cart_items:
                # Skidka narxini hisoblash
                discount_percentage = item.get("discount_percentage", 0) or 0
                final_price = item["price"]
                if discount_percentage > 0:
                    try:
                        final_price = item["price"] * (100 - discount_percentage) / 100
                    except:  # Handle potential errors in calculation
                        final_price = item["price"]

                item_total = final_price * item["quantity"]
                total_amount += item_total

                # Try to include size and color if columns exist; fallback otherwise
                try:
                    execute_query(
                        """
                        INSERT INTO order_details (order_id, menu_item_id, quantity, price, size, color)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            order_id,
                            item["menu_item_id"],
                            item["quantity"],
                            final_price,
                            item.get("size"),
                            item.get("color"),
                        ),
                    )
                except Exception:
                    # Older schema fallback
                    execute_query(
                        """
                        INSERT INTO order_details (order_id, menu_item_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                    """,
                        (order_id, item["menu_item_id"], item["quantity"], final_price),
                    )

                # JSON uchun mahsulot ma'lumotlarini to'plash
                order_items_for_json.append(
                    {
                        "nomi": item.get("name", "N/A"),
                        "miqdori": item["quantity"],
                        "asl_narxi": item["price"],
                        "skidka_foizi": discount_percentage,
                        "jami": item_total,
                    }
                )

            # Chek yaratish
            receipt_number = f"R{tno}{now.strftime('%H%M%S')}"
            cashback_percentage = 1.0  # Default cashback
            cashback_amount = total_amount * (cashback_percentage / 100)

            execute_query(
                """
                INSERT INTO receipts (order_id, receipt_number, total_amount, cashback_amount, cashback_percentage, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """,
                (
                    order_id,
                    receipt_number,
                    total_amount,
                    cashback_amount,
                    cashback_percentage,
                    now.isoformat(),
                ),
            )

            # Savatchani tozalash
            clear_cart(conn, session_id, user_id)

            # Cache ni tozalash (safe)
            try:
                cm3 = cache_manager or get_cache_manager()
            except Exception:
                cm3 = None
            if cm3:
                try:
                    if user_id:
                        cm3.delete(f"cart_count_{user_id}")
                    else:
                        cm3.delete(f"cart_count_{session_id}")
                except Exception:
                    pass

            # Foydalanuvchini JSON fayliga saqlash (async)
            # Use safe_submit to avoid None executor issues and ensure background task runs or falls back
            try:
                safe_submit(save_user_to_json, name, tno, now, order_items_for_json)
            except Exception as submit_err:
                app_logger.warning(
                    f"Background save_user_to_json submission failed, running sync: {submit_err}"
                )
                try:
                    # last-resort synchronous call so it doesn't break user flow
                    save_user_to_json(name, tno, now, order_items_for_json)
                except Exception:
                    # swallow any errors here to avoid breaking the user experience
                    app_logger.exception(
                        "Failed to save user JSON synchronously after submit failure"
                    )

            # Avtomatik bildirishnoma yuborish
            send_order_notifications(order_id, "pending", name, total_amount)

            flash("Buyurtma yuborildi. Super admin tasdiqlashi kutilmoqda.", "info")
            return redirect(url_for("order_pending_approval", order_id=order_id))

    except Exception as e:
        app_logger.error(f"Buyurtma berishda xatolik: {str(e)}")
        flash("Buyurtma berishda xatolik yuz berdi. Qaytadan urinib ko'ring.", "error")
        return redirect(url_for("cart"))


@app.route("/user", methods=["GET", "POST"])
def user_page():
    "User page - buyurtma berish"
    if request.method == "POST":
        return place_order()

    # GET request uchun cart sahifasini ko'rsatish
    session_id = get_session_id()
    user_id = session.get("user_id")

    try:
        cart_items = get_cart_items(None, session_id, user_id)
        total = get_cart_total(None, session_id, user_id)
        return render_template(
            "cart.html", cart_items=cart_items or [], total=total or 0
        )
    except Exception as e:
        app_logger.error(f"User page error: {str(e)}")
        return redirect(url_for("menu"))


@app.route("/user/status/<int:ticket_no>")
def user_status(ticket_no):
    "Buyurtma holatini JSON formatda qaytarish"
    try:
        order = execute_query(
            "SELECT * FROM orders WHERE ticket_no = ?", (ticket_no,), fetch_one=True
        )
        if not order:
            return jsonify({"error": "Buyurtma topilmadi", "status": "not_found"}), 404

        return jsonify(
            {
                "ticket_no": order["ticket_no"],
                "status": order["status"],
                "created_at": order["created_at"],
                "eta_time": order["eta_time"],
            }
        )
    except Exception as e:
        app_logger.error(f"user_status error: {str(e)}")
        return jsonify({"error": "Server xatosi"}), 500


# ----- Order pending approval page (shows superadmin contacts) -----
@app.route("/order/pending/<int:order_id>")
def order_pending_approval(order_id):
    try:
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("menu"))

        # Load superadmin contact info from settings
        creds = get_superadmin_creds()
        contact = {
            "email": creds.get("email", ""),
            "telegram": creds.get("telegram", ""),
            "instagram": creds.get("instagram", ""),
            "phone": creds.get("phone", ""),
        }

        return render_template(
            "order_pending.html",
            order=order,
            contact=contact,
        )
    except Exception as e:
        app_logger.error(f"Order pending page error: {str(e)}")
        flash("Sahifani yuklashda xatolik.", "error")
        return redirect(url_for("menu"))
    except Exception as e:
        app_logger.error(f"User status error: {str(e)}")
        return jsonify({"error": "Server xatoligi"}), 500


@app.route("/user/cancel/<int:ticket_no>", methods=["POST"])
def user_cancel_order(ticket_no):
    "Foydalanuvchi buyurtmasini bekor qilish"
    try:
        order = execute_query(
            "SELECT * FROM orders WHERE ticket_no = ? AND status IN ('waiting', 'ready')",
            (ticket_no,),
            fetch_one=True,
        )
        if not order:
            flash("Buyurtma topilmadi yoki bekor qilib bo'lmaydi.", "error")
            return redirect(url_for("index"))

        execute_query(
            "UPDATE orders SET status = 'cancelled' WHERE ticket_no = ?", (ticket_no,)
        )
        flash("Buyurtma bekor qilindi.", "success")
        return redirect(url_for("index"))
    except Exception as e:
        app_logger.error(f"User cancel order error: {str(e)}")
        flash("Buyurtmani bekor qilishda xatolik.", "error")
        return redirect(url_for("index"))


@app.route("/user/success/<int:ticket_no>")
def user_success(ticket_no):
    conn = get_db()
    cur = conn.cursor()

    # Buyurtma ma'lumotlarini olish
    order = execute_query(
        "SELECT * FROM orders WHERE ticket_no=? ORDER BY id DESC LIMIT 1",
        (ticket_no,),
        fetch_one=True,
    )

    if not order:
        flash("Buyurtma topilmadi.", "error")
        return redirect(url_for("menu"))

    # Buyurtma tafsilotlarini olish (size/color bilan)
    order_items_raw = execute_query(
        """
        SELECT od.quantity, mi.name, od.price, od.size, od.color
        FROM order_details od
        JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE od.order_id = ?
    """,
        (order["id"],),
        fetch_all=True,
    )
    order_items = []
    if order_items_raw:
        for r in order_items_raw:
            rd = dict(r)
            order_items.append(
                {
                    "quantity": rd.get("quantity"),
                    "name": rd.get("name"),
                    "price": rd.get("price"),
                    "size": rd.get("size"),
                    "color": rd.get("color"),
                }
            )

    conn.close()

    # ETA vaqtini formatlash
    eta_time_str = order.get("eta_time")
    eta_hhmm = ""
    if eta_time_str:
        try:
            eta_time = datetime.datetime.fromisoformat(eta_time_str)
            eta_hhmm = eta_time.strftime("%H:%M")
        except:
            eta_hhmm = "N/A"  # Handle potential parsing errors

    # Load superadmin settings (contact info) so the success page can show admin contact
    superadmin_settings = load_superadmin_settings() or {}

    return render_template(
        "user_success.html",
        order=order,
        order_items=order_items,
        eta_hhmm=eta_hhmm,
        superadmin_settings=superadmin_settings,
    )


@app.route("/receipt/<int:ticket_no>")
def view_receipt(ticket_no):
    "Chekni ko'rish sahifasi"
    try:
        # Buyurtma va chek ma'lumotlarini olish
        order_receipt_data = execute_query(
            """
            SELECT o.*,
                   r.receipt_number, r.total_amount, r.cashback_amount, r.cashback_percentage, r.created_at as receipt_created
            FROM orders o
            LEFT JOIN receipts r ON o.id = r.order_id
            WHERE o.ticket_no = ?
            ORDER BY o.id DESC LIMIT 1
        """,
            (ticket_no,),
            fetch_one=True,
        )

        if not order_receipt_data:
            flash("Buyurtma yoki chek topilmadi.", "error")
            return redirect(url_for("menu"))

        # Buyurtma tafsilotlarini olish (size/color bilan)
        order_items_raw = execute_query(
            """
            SELECT od.quantity, mi.name, od.price, od.size, od.color
            FROM order_details od
            JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE od.order_id = ?
        """,
            (order_receipt_data["id"],),
            fetch_all=True,
        )

        order_items = []
        if order_items_raw:
            for r in order_items_raw:
                rd = dict(r)
                name = rd.get("name", "N/A")
                qty = rd.get("quantity", 0)
                size = rd.get("size")
                color = rd.get("color")
                label = f"{name} x{qty}"
                if size:
                    label += f" ({size})"
                if color:
                    label += f" - {color}"
                order_items.append(label)
        # QR kod yaratish
        qr_code = None
        if order_receipt_data.get("receipt_number"):
            try:
                receipt_data = {
                    "receipt_number": order_receipt_data.get("receipt_number") or "",
                    "total_amount": float(order_receipt_data.get("total_amount") or 0),
                    "cashback_amount": float(
                        order_receipt_data.get("cashback_amount") or 0
                    ),
                    "cashback_percentage": float(
                        order_receipt_data.get("cashback_percentage") or 0
                    ),
                    "receipt_created": order_receipt_data.get("receipt_created") or "",
                }
                qr_code = generate_qr_code(receipt_data)
            except Exception as qr_error:
                app_logger.warning(f"QR kod yaratishda xatolik: {str(qr_error)}")

        return render_template(
            "receipt.html",
            order=order_receipt_data,
            order_items=order_items,
            qr_code=qr_code,
        )

    except Exception as e:
        app_logger.error(f"Receipt view error: {str(e)}")
        flash("Chekni yuklashda xatolik yuz berdi.", "error")
        return redirect(url_for("menu"))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    "Aloqa sahifasi"
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            if not all([name, subject, message]):
                flash("Ism, mavzu va xabar majburiy maydonlar.", "error")
                return redirect(url_for("contact"))

            # Savolni ma'lumotlar bazasiga saqlash
            now = get_current_time().isoformat()
            execute_query(
                """
                INSERT INTO questions (user_name, email, phone, subject, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (name, email, phone, subject, message, now),
            )

            flash(
                "Savolingiz muvaffaqiyatli yuborildi! Tez orada javob beramiz.",
                "success",
            )
            return redirect(url_for("contact"))

        except Exception as e:
            app_logger.error(f"Contact form error: {str(e)}")
            flash("Xabar yuborishda xatolik yuz berdi.", "error")
            return redirect(url_for("contact"))

    return render_template("contact.html", current_page="contact")


@app.route("/about")
def about():
    "About sahifasi"
    return render_template("about.html", current_page="about")


@app.route("/kafolatlar", endpoint="kafolatlar")
def kafolatlar_page():
    return render_template("kafolatlar.html")


@app.route("/downloads")
def downloads():
    "Downloads sahifasi - mobil ilovalar"
    return render_template("downloads.html", current_page="downloads")


# ---- COURIER AUTH ----
@app.route("/courier-secure-login-k4m7p", methods=["GET", "POST"])
def courier_login():
    if request.method == "POST":
        courier_id_str = request.form.get("courier_id", "").strip()
        password = request.form.get("password", "")

        if not courier_id_str or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("courier_login"))

        # ID raqam ekanligini tekshirish
        try:
            courier_id = int(courier_id_str)
        except ValueError:
            flash("ID raqam bo'lishi kerak.", "error")
            return redirect(url_for("courier_login"))

        # Courier ma'lumotlarini olish
        row = execute_query(
            "SELECT * FROM couriers WHERE id=?", (courier_id,), fetch_one=True
        )

        if row:
            # Faollik vaqtini yangilash va ishchi soatlarini hisoblash
            now = get_current_time()
            now_iso = now.isoformat()

            try:
                # Row obyektini dict ga aylantirish
                if hasattr(row, "keys"):
                    row_dict = dict(row)
                else:
                    # Tuple format uchun manual dict yaratish
                    columns = [
                        "id",
                        "first_name",
                        "last_name",
                        "birth_date",
                        "phone",
                        "passport_series",
                        "passport_number",
                        "password_hash",
                        "total_hours",
                        "deliveries_completed",
                        "last_activity",
                        "created_at",
                    ]
                    row_dict = {
                        columns[i]: row[i] if i < len(row) else None
                        for i in range(len(columns))
                    }

                # Agar avvalgi faollik vaqti mavjud bo'lsa, ishchi soatlarni yangilash
                if row_dict.get("last_activity"):
                    try:
                        last_activity = datetime.datetime.fromisoformat(
                            row_dict["last_activity"]
                        )
                        current_time = get_current_time()
                        time_diff = current_time - last_activity

                        # Agar 8 soatdan kam bo'lsa, ishchi vaqtga qo'shish
                        if time_diff.total_seconds() < 28800:  # 8 soat
                            additional_hours = time_diff.total_seconds() / 3600
                            execute_query(
                                "UPDATE couriers SET total_hours = COALESCE(total_hours, 0) + ?, last_activity = ? WHERE id = ?",
                                (additional_hours, now_iso, courier_id),
                            )
                        else:
                            execute_query(
                                "UPDATE couriers SET last_activity = ? WHERE id = ?",
                                (now_iso, courier_id),
                            )
                    except Exception as update_error:
                        app_logger.warning(
                            f"Courier faollik yangilashda xatolik: {str(update_error)}"
                        )
                        execute_query(
                            "UPDATE couriers SET last_activity = ? WHERE id = ?",
                            (now_iso, courier_id),
                        )  # Update last_activity even if calculation fails
                else:
                    execute_query(
                        "UPDATE couriers SET last_activity = ? WHERE id = ?",
                        (now_iso, courier_id),
                    )

            except Exception as dict_error:
                app_logger.error(
                    f"Courier row dict conversion error: {str(dict_error)}"
                )
                flash("Ma'lumotlarni qayta ishlashda xatolik.", "error")
                return redirect(url_for("courier_login"))

            # Password hash ni tekshirish
            password_hash = row_dict.get("password_hash", "")
            if password_hash and check_password_hash(password_hash, password):
                # Login muvaffaqiyatli - set exclusive courier role
                display = f"{row_dict['first_name']} {row_dict['last_name']}"
                set_role_session("courier", id=row_dict["id"], name=display)

                flash(f"Xush kelibsiz, {row_dict['first_name']}!", "success")
                return redirect(url_for("courier_dashboard"))
            else:
                flash("Noto'g'ri ID yoki parol.", "error")
        else:
            flash("Kuryer topilmadi.", "error")

    return render_template("courier_login.html")


@app.route("/courier/dashboard")
@role_required("courier")
def courier_dashboard():
    if "courier_id" not in session:
        flash("Kuryer tizimiga kirish talab qilinadi.", "error")
        return redirect(url_for("courier_login"))

    cleanup_expired_orders()

    try:
        # Barcha ready delivery buyurtmalar va kuryerga tegishli buyurtmalarni olish
        delivery_orders_raw = execute_query(
            """
         SELECT o.*,
             o.delivery_latitude AS delivery_lat,
             o.delivery_longitude AS delivery_lon,
             GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE
              (o.order_type = 'delivery' AND o.status = 'ready') -- all ready delivery orders (including unassigned)
              OR (o.courier_id = ? AND o.status IN ('on_way', 'delivered')) -- orders assigned to this courier
            GROUP BY o.id
            ORDER BY
                CASE
                    WHEN o.status = 'ready' THEN 1
                    WHEN o.status = 'on_way' THEN 2
                    WHEN o.status = 'delivered' THEN 3
                    ELSE 4
                END,
                o.created_at ASC
        """,
            (session.get("courier_id"),),
            fetch_all=True,
        )
        delivery_orders = (
            [dict(row) for row in delivery_orders_raw] if delivery_orders_raw else []
        )

        # Kuryer statistikasini olish - xavfsiz usul
        try:
            courier_id = session.get("courier_id")
            if not courier_id:
                raise ValueError("Courier ID topilmadi sessionda")

            # Kuryer ma'lumotlarini olish
            courier_stats = execute_query(
                "SELECT COALESCE(deliveries_completed, 0) as deliveries_completed, COALESCE(total_hours, 0.0) as total_hours FROM couriers WHERE id = ?",
                (courier_id,),
                fetch_one=True,
            )

            # Faol buyurtmalar sonini olish
            active_orders_result = execute_query(
                "SELECT COUNT(*) FROM orders WHERE courier_id = ? AND status = 'on_way'",
                (courier_id,),
                fetch_one=True,
            )

            # Session ga statistikani saqlash - xavfsiz usul
            if courier_stats:
                try:
                    # Safe handling of courier_stats - check if it's a dict or tuple
                    if hasattr(courier_stats, "get"):
                        # It's a dict-like object
                        deliveries = courier_stats.get("deliveries_completed", 0)
                        hours = courier_stats.get("total_hours", 0.0)
                    elif (
                        isinstance(courier_stats, (list, tuple))
                        and len(courier_stats) >= 2
                    ):
                        # It's a tuple or list
                        deliveries = (
                            courier_stats[0] if courier_stats[0] is not None else 0
                        )
                        hours = (
                            courier_stats[1] if courier_stats[1] is not None else 0.0
                        )
                    else:
                        # Fallback
                        deliveries = 0
                        hours = 0.0

                    # Safe conversion
                    session["courier_deliveries"] = max(
                        0, int(deliveries) if deliveries is not None else 0
                    )
                    session["courier_hours"] = max(
                        0.0, round(float(hours) if hours is not None else 0.0, 1)
                    )

                except (
                    TypeError,
                    ValueError,
                    AttributeError,
                    IndexError,
                ) as conversion_error:
                    app_logger.warning(
                        f"Kuryer statistikasini conversion xatoligi: {str(conversion_error)}"
                    )
                    session["courier_deliveries"] = 0
                    session["courier_hours"] = 0.0
            else:
                app_logger.warning(f"Kuryer ma'lumotlari topilmadi ID: {courier_id}")
                session["courier_deliveries"] = 0
                session["courier_hours"] = 0.0

            # Active orders - safe conversion
            active_orders = 0
            if active_orders_result:
                try:
                    # Handle both dict and tuple formats
                    if hasattr(active_orders_result, "get"):
                        active_orders = max(
                            0, int(active_orders_result.get("COUNT(*)", 0) or 0)
                        )
                    elif (
                        isinstance(active_orders_result, (list, tuple))
                        and len(active_orders_result) > 0
                    ):
                        active_orders = max(
                            0,
                            (
                                int(active_orders_result[0])
                                if active_orders_result[0] is not None
                                else 0
                            ),
                        )
                    else:
                        active_orders = 0
                except (ValueError, TypeError, IndexError):
                    active_orders = 0
            session["courier_active_orders"] = active_orders

        except Exception as stats_error:
            app_logger.error(
                f"Kuryer statistikasini olishda umumiy xatolik: {str(stats_error)}"
            )
            # Set all stats to safe defaults
            session["courier_deliveries"] = 0
            session["courier_hours"] = 0.0
            session["courier_active_orders"] = 0

        app_logger.info(
            f"Courier dashboard loaded for courier_id: {session.get('courier_id')}, found {len(delivery_orders)} orders"
        )

        # Get notifications for courier
        current_user = {"type": "courier", "id": session.get("courier_id")}
        notifications = get_notifications_for_user(current_user)

        # Template ni xavfsiz render qilish
        try:
            # Ensure orders is always a list
            safe_orders = delivery_orders if isinstance(delivery_orders, list) else []
            return render_template(
                "courier_dashboard.html",
                orders=safe_orders,
                notifications=notifications,
            )
        except Exception as template_error:
            app_logger.error(
                f"Courier dashboard template render error: {str(template_error)}"
            )
            # Fallback template with empty orders
            try:
                return render_template("courier_dashboard.html", orders=[])
            except Exception as fallback_error:
                app_logger.error(
                    f"Courier dashboard fallback template error: {str(fallback_error)}"
                )
                # Emergency HTML fallback
                return (
                    f"""
                <!DOCTYPE html>
                <html>
                <head><title>Kuryer Dashboard</title></head>
                <body>
                    <h1>Kuryer Dashboard</h1>
                    <p>Template yuklashda xatolik: {str(template_error)}</p>
                    <a href="{url_for('courier_login')}">Login sahifasiga qaytish</a>
                </body>
                </html>
                """,
                    500,
                )

    except Exception as e:
        app_logger.error(f"Courier dashboard error: {str(e)}")
        flash("Dashboard yuklashda xatolik yuz berdi.", "error")
        try:
            return render_template("courier_dashboard.html", orders=[])
        except Exception as template_error:
            app_logger.error(f"Courier dashboard template error: {str(template_error)}")
            return (
                """
            <!DOCTYPE html>
            <html><head><title>Courier Dashboard - Error</title></head>
            <body>
                <h1>Kuryer Dashboard - Xatolik</h1>
                <p>Dashboard yuklashda xatolik yuz berdi.</p>
                <a href="/courier-secure-login-k4m7p">Login sahifasiga qaytish</a>
            </body></html>
            """,
                500,
            )


@app.route("/courier/order/<int:order_id>/take", methods=["POST"])
@role_required("courier")
def courier_take_order(order_id):
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    courier_id = session.get("courier_id")

    try:
        # Buyurtma ma'lumotlarini olish
        order = execute_query(
            "SELECT * FROM orders WHERE id=? AND status='ready' AND order_type='delivery'",
            (order_id,),
            fetch_one=True,
        )

        if order:
            # Avtomatik narx va vaqt hisoblash
            distance = (
                float(order["delivery_distance"])
                if order.get("delivery_distance")
                else 5.0
            )
            auto_price, auto_delivery_time = auto_calculate_courier_delivery_price(
                distance
            )

            # Buyurtmani yangilash
            execute_query(
                """
                UPDATE orders
                SET status='on_way', courier_id=?, courier_price=?, courier_delivery_minutes=?, delivery_price=?
                WHERE id=? AND status='ready'
            """,
                (courier_id, auto_price, auto_delivery_time, auto_price, order_id),
            )

            flash(
                f"Buyurtma olib ketildi! Avtomatik narx: {auto_price:,.0f} so'm, Vaqt: {auto_delivery_time} daqiqa",
                "success",
            )
        else:
            flash("Buyurtma topilmadi yoki allaqachon olingan!", "error")

    except Exception as e:
        app_logger.error(f"Courier take order error: {str(e)}")
        flash("Buyurtmani olishda xatolik yuz berdi.", "error")

    return redirect(url_for("courier_dashboard"))


@app.route("/courier/order/<int:order_id>/delivered", methods=["GET", "POST"])
@role_required("courier")
def courier_mark_delivered(order_id):
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    # If GET request, redirect to dashboard with info message
    if request.method == "GET":
        flash("Buyurtmani yetkazib berildi deb belgilash uchun tugmani bosing.", "info")
        return redirect(url_for("courier_dashboard"))

    courier_id = session.get("courier_id")

    try:
        # Buyurtma ma'lumotlarini olish
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("courier_dashboard"))

        # Buyurtmani 'delivered' qilib belgilash
        execute_query(
            "UPDATE orders SET status='delivered' WHERE id=? AND courier_id=?",
            (order_id, courier_id),
        )

        # Kuryerning yetkazib bergan buyurtmalar sonini oshirish
        execute_query(
            "UPDATE couriers SET deliveries_completed = COALESCE(deliveries_completed, 0) + 1 WHERE id = ?",
            (courier_id,),
        )

        # Avtomatik bildirishnoma yuborish
        customer_name = order.get("customer_name", "Mijoz")
        total_amount = order.get("total_amount", 0)
        send_order_notifications(order_id, "delivered", customer_name, total_amount)

        flash("Buyurtma yetkazib berildi!", "success")
    except Exception as e:
        app_logger.error(f"Courier mark delivered error: {str(e)}")
        flash("Buyurtmani yetkazib berildi deb belgilashda xatolik.", "error")

    return redirect(url_for("courier_dashboard"))


@app.route("/courier/set-price-time", methods=["POST"])
@role_required("courier")
def courier_set_price_time():
    if "courier_id" not in session:
        return jsonify({"success": False, "message": "Kuryer tizimga kirmagan"}), 401

    data = request.get_json()
    order_id = data.get("order_id")
    price_str = data.get("price")
    delivery_time_str = data.get("delivery_time")

    if not all([order_id, price_str, delivery_time_str]):
        return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

    try:
        price = float(price_str)
        delivery_time = int(delivery_time_str)

        if price <= 0 or delivery_time <= 0:
            return jsonify(
                {"success": False, "message": "Narx va vaqt musbat bo'lishi kerak"}
            )

        # Buyurtma mavjudligini va statusini tekshirish
        order = execute_query(
            "SELECT * FROM orders WHERE id = ? AND status = 'ready'",
            (order_id,),
            fetch_one=True,
        )

        if not order:
            return jsonify(
                {"success": False, "message": "Buyurtma topilmadi yoki tayyor emas"}
            )

        # Narx va vaqtni yangilash
        execute_query(
            """
            UPDATE orders
            SET courier_price = ?, courier_delivery_minutes = ?, delivery_price = ?
            WHERE id = ?
        """,
            (price, delivery_time, price, order_id),
        )

        return jsonify({"success": True, "message": "Narx va vaqt belgilandi"})

    except Exception as e:
        app_logger.error(f"Kuryer narx belgilashda xatolik: {str(e)}")
        return jsonify({"success": False, "message": "Server xatoligi"}), 500


@app.route("/courier/logout")
def courier_logout():
    # Terminate the session in database if session_id exists
    current_session_id = session.get("session_id")
    if current_session_id:
        try:
            terminate_session(current_session_id, current_session_id=current_session_id)
        except Exception as e:
            app_logger.warning(f"Failed to terminate courier session in database: {e}")

    session.clear()  # Clear entire session instead of just popping specific keys
    flash("Kuryer tizimidan chiqdingiz.", "info")
    return redirect(url_for("index"))


# Admin JSON API routes
@app.route("/admin/orders.json")
def admin_orders_json():
    "Get all orders in JSON format"
    if not session.get("staff_id") and not session.get("super_admin"):
        return jsonify({"error": "Authentication required"}), 401

    try:
        orders_raw = execute_query(
            """
            SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 100
        """,
            fetch_all=True,
        )

        orders = [dict(row) for row in orders_raw] if orders_raw else []

        return jsonify({"success": True, "orders": orders, "total": len(orders)})
    except Exception as e:
        app_logger.error(f"Admin orders JSON error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/add_menu_item", methods=["POST"])
def admin_add_menu_item():
    "Add new menu item"
    if not session.get("staff_id") and not session.get("super_admin"):
        flash("Xodim huquqi kerak.", "error")
        return redirect(url_for("staff_login"))

    try:
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price", 0))
        category = request.form.get("category", "footwear")
        description = request.form.get("description", "").strip()
        sizes = request.form.get("sizes", "").strip()  # comma-separated
        colors = request.form.get("colors", "").strip()  # comma-separated
        discount_percentage = float(request.form.get("discount_percentage", 0) or 0)

        if not name or price <= 0:
            flash("Nomi va narxi to'g'ri bo'lishi kerak.", "error")
            return redirect(url_for("staff_menu"))

        now = get_current_time().isoformat()

        # Birinchi mahsulotni qo'shamiz (image_url ni hozircha None bilan)
        menu_item_id = execute_query(
            """
            INSERT INTO menu_items (name, price, category, description, sizes, colors, discount_percentage, image_url, created_at, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
            (
                name,
                price,
                category,
                description,
                sizes,
                colors,
                discount_percentage,
                None,
                now,
            ),
        )

        if menu_item_id:
            # Ko'p rasm va videolarni yuklash
            media_files = request.files.getlist("media_files")  # Yangi input nomi
            uploaded_media = []
            main_image_set = False

            upload_dir = os.path.join(app.root_path, "static", "uploads", "products")
            os.makedirs(upload_dir, exist_ok=True)

            for idx, file in enumerate(media_files):
                if file and file.filename:
                    try:
                        from werkzeug.utils import secure_filename
                        import uuid

                        # Fayl kengaytmasini aniqlash
                        ext = (
                            file.filename.rsplit(".", 1)[1].lower()
                            if "." in file.filename
                            else ""
                        )

                        # Media turini aniqlash
                        image_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
                        video_extensions = {"mp4", "avi", "mov", "wmv", "flv", "webm"}

                        if ext in image_extensions:
                            media_type = "image"
                        elif ext in video_extensions:
                            media_type = "video"
                        else:
                            continue  # Noma'lum fayl turini o'tkazib yuboramiz

                        # Unique fayl nomi yaratish
                        unique_filename = f"{menu_item_id}_{uuid.uuid4().hex}.{ext}"
                        save_path = os.path.join(upload_dir, unique_filename)

                        file.save(save_path)
                        media_url = f"/static/uploads/products/{unique_filename}"

                        # Birinchi rasmni asosiy qilish
                        is_main = not main_image_set and media_type == "image"
                        if is_main:
                            main_image_set = True
                            # Menu items jadvalidagi image_url ni yangilash
                            execute_query(
                                "UPDATE menu_items SET image_url = ? WHERE id = ?",
                                (media_url, menu_item_id),
                            )

                        # Product media jadvaliga qo'shish
                        execute_query(
                            """
                            INSERT INTO product_media (menu_item_id, media_type, media_url, display_order, is_main, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                menu_item_id,
                                media_type,
                                media_url,
                                idx,
                                1 if is_main else 0,
                                now,
                                now,
                            ),
                        )

                        uploaded_media.append({"type": media_type, "url": media_url})

                    except Exception as media_error:
                        app_logger.warning(
                            f"Media yuklashda xatolik: {str(media_error)}"
                        )
                        continue

            if uploaded_media:
                flash(
                    f"Yangi mahsulot va {len(uploaded_media)} ta media fayl qo'shildi!",
                    "success",
                )
            else:
                flash(
                    "Yangi mahsulot qo'shildi, lekin media fayllar yuklanmadi!",
                    "warning",
                )
        else:
            flash("Mahsulot qo'shishda xatolik yuz berdi.", "error")

    except Exception as e:
        app_logger.error(f"Add menu item error: {str(e)}")
        flash("Mahsulot qo'shishda xatolik yuz berdi.", "error")

    return redirect(url_for("staff_menu"))


@app.route("/admin/edit_menu_item/<int:item_id>", methods=["POST"])
def admin_edit_menu_item(item_id):
    "Edit menu item"
    if not session.get("staff_id") and not session.get("super_admin"):
        flash("Xodim huquqi kerak.", "error")
        return redirect(url_for("staff_login"))

    try:
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price", 0))
        description = request.form.get("description", "").strip()
        sizes = request.form.get("sizes", "").strip()
        colors = request.form.get("colors", "").strip()
        discount_percentage = float(request.form.get("discount_percentage", 0) or 0)

        if not name or price <= 0:
            flash("Nomi va narxi to'g'ri bo'lishi kerak.", "error")
            return redirect(url_for("staff_menu"))

        # Build update dynamically
        params = [name, price, description, discount_percentage]
        sql_set = "name = ?, price = ?, description = ?, discount_percentage = ?"
        if sizes is not None:
            sql_set += ", sizes = ?"
            params.append(sizes)
        if colors is not None:
            sql_set += ", colors = ?"
            params.append(colors)

        params.append(item_id)

        execute_query(
            f"""
            UPDATE menu_items 
            SET {sql_set}
            WHERE id = ?
        """,
            tuple(params),
        )

        # Yangi media fayllarni yuklash
        media_files = request.files.getlist("media_files")
        if media_files:
            now = get_current_time().isoformat()
            uploaded_media = []

            upload_dir = os.path.join(app.root_path, "static", "uploads", "products")
            os.makedirs(upload_dir, exist_ok=True)

            # Hozirgi media fayllar sonini olish
            current_media_count = execute_query(
                "SELECT COUNT(*) FROM product_media WHERE menu_item_id = ?",
                (item_id,),
                fetch_one=True,
            )
            next_order = current_media_count[0] if current_media_count else 0

            for idx, file in enumerate(media_files):
                if file and file.filename:
                    try:
                        from werkzeug.utils import secure_filename
                        import uuid

                        # Fayl kengaytmasini aniqlash
                        ext = (
                            file.filename.rsplit(".", 1)[1].lower()
                            if "." in file.filename
                            else ""
                        )

                        # Media turini aniqlash
                        image_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
                        video_extensions = {"mp4", "avi", "mov", "wmv", "flv", "webm"}

                        if ext in image_extensions:
                            media_type = "image"
                        elif ext in video_extensions:
                            media_type = "video"
                        else:
                            continue

                        # Unique fayl nomi yaratish
                        unique_filename = f"{item_id}_{uuid.uuid4().hex}.{ext}"
                        save_path = os.path.join(upload_dir, unique_filename)

                        file.save(save_path)
                        media_url = f"/static/uploads/products/{unique_filename}"

                        # Agar hech qanday asosiy rasm yo'q bo'lsa va bu birinchi rasm bo'lsa
                        is_main = False
                        if media_type == "image":
                            main_image_exists = execute_query(
                                "SELECT COUNT(*) FROM product_media WHERE menu_item_id = ? AND is_main = 1 AND media_type = 'image'",
                                (item_id,),
                                fetch_one=True,
                            )
                            if not main_image_exists[0]:
                                is_main = True
                                # Menu items jadvalidagi image_url ni yangilash
                                execute_query(
                                    "UPDATE menu_items SET image_url = ? WHERE id = ?",
                                    (media_url, item_id),
                                )

                        # Product media jadvaliga qo'shish
                        execute_query(
                            """
                            INSERT INTO product_media (menu_item_id, media_type, media_url, display_order, is_main, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                item_id,
                                media_type,
                                media_url,
                                next_order + idx,
                                1 if is_main else 0,
                                now,
                                now,
                            ),
                        )

                        uploaded_media.append({"type": media_type, "url": media_url})

                    except Exception as media_error:
                        app_logger.warning(
                            f"Media yuklashda xatolik: {str(media_error)}"
                        )
                        continue

            if uploaded_media:
                flash(
                    f"Mahsulot yangilandi va {len(uploaded_media)} ta yangi media fayl qo'shildi!",
                    "success",
                )
            else:
                flash("Mahsulot yangilandi!", "success")
        else:
            flash("Mahsulot yangilandi!", "success")

    except Exception as e:
        app_logger.error(f"Edit menu item error: {str(e)}")
        flash("Mahsulotni yangilashda xatolik yuz berdi.", "error")

    return redirect(url_for("staff_menu"))


# Media fayllarni boshqarish API'lari
@app.route("/api/product-media/<int:item_id>", methods=["GET"])
@role_required("staff")
def api_get_product_media(item_id):
    """Mahsulot media fayllarini olish"""
    try:
        media_files = execute_query(
            """
            SELECT id, media_type, media_url, display_order, is_main, created_at
            FROM product_media 
            WHERE menu_item_id = ? 
            ORDER BY is_main DESC, display_order ASC
            """,
            (item_id,),
            fetch_all=True,
        )

        media_list = [dict(media) for media in media_files] if media_files else []
        return jsonify({"success": True, "media": media_list})

    except Exception as e:
        app_logger.error(f"Get product media error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Media fayllarni olishda xatolik"}),
            500,
        )


@app.route("/api/product-media/<int:media_id>/set-main", methods=["POST"])
@role_required("staff")
def api_set_main_media(media_id):
    """Media faylni asosiy qilib belgilash"""
    try:
        # Avval ushbu media fayl qaysi mahsulotga tegishliligini aniqlaymiz
        media_item = execute_query(
            "SELECT menu_item_id, media_url FROM product_media WHERE id = ?",
            (media_id,),
            fetch_one=True,
        )

        if not media_item:
            return jsonify({"success": False, "message": "Media fayl topilmadi"}), 404

        menu_item_id = media_item["menu_item_id"]
        media_url = media_item["media_url"]

        # Barcha media fayllarni asosiy emas deb belgilaymiz
        execute_query(
            "UPDATE product_media SET is_main = 0 WHERE menu_item_id = ?",
            (menu_item_id,),
        )

        # Tanlangan media faylni asosiy qilib belgilaymiz
        now = get_current_time().isoformat()
        execute_query(
            "UPDATE product_media SET is_main = 1, updated_at = ? WHERE id = ?",
            (now, media_id),
        )

        # Menu items jadvalidagi image_url ni ham yangilaymiz
        execute_query(
            "UPDATE menu_items SET image_url = ? WHERE id = ?",
            (media_url, menu_item_id),
        )

        return jsonify({"success": True, "message": "Asosiy rasm belgilandi"})

    except Exception as e:
        app_logger.error(f"Set main media error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Asosiy rasm belgilashda xatolik"}),
            500,
        )


@app.route("/api/product-media/<int:media_id>/delete", methods=["DELETE"])
@role_required("staff")
def api_delete_product_media(media_id):
    """Media faylni o'chirish"""
    try:
        # Media fayl ma'lumotlarini olish
        media_item = execute_query(
            "SELECT media_url, menu_item_id FROM product_media WHERE id = ?",
            (media_id,),
            fetch_one=True,
        )

        if not media_item:
            return jsonify({"success": False, "message": "Media fayl topilmadi"}), 404

        # Faylni diskdan o'chirish
        try:
            media_path = media_item["media_url"].replace("/static/", "static/")
            if os.path.exists(media_path):
                os.remove(media_path)
        except Exception as file_error:
            app_logger.warning(f"Could not delete media file: {file_error}")

        # Database dan o'chirish
        execute_query("DELETE FROM product_media WHERE id = ?", (media_id,))

        # Agar bu asosiy rasm bo'lsa, boshqa rasmni asosiy qilish
        menu_item_id = media_item["menu_item_id"]
        remaining_images = execute_query(
            "SELECT id, media_url FROM product_media WHERE menu_item_id = ? AND media_type = 'image' ORDER BY display_order ASC LIMIT 1",
            (menu_item_id,),
            fetch_one=True,
        )

        if remaining_images:
            # Boshqa rasmni asosiy qilish
            execute_query(
                "UPDATE product_media SET is_main = 1 WHERE id = ?",
                (remaining_images["id"],),
            )
            execute_query(
                "UPDATE menu_items SET image_url = ? WHERE id = ?",
                (remaining_images["media_url"], menu_item_id),
            )
        else:
            # Hech qanday rasm qolmasa, default rasm qo'yish
            execute_query(
                "UPDATE menu_items SET image_url = ? WHERE id = ?",
                ("/static/images/default-men.jpg", menu_item_id),
            )

        return jsonify({"success": True, "message": "Media fayl o'chirildi"})

    except Exception as e:
        app_logger.error(f"Delete product media error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Media faylni o'chirishda xatolik"}),
            500,
        )


@app.route("/api/product-media/reorder", methods=["POST"])
@role_required("staff")
def api_reorder_product_media():
    """Media fayllar tartibini o'zgartirish"""
    try:
        data = request.get_json() or {}
        media_ids = data.get("media_ids", [])

        if not media_ids:
            return jsonify({"success": False, "message": "Media ID'lar kerak"}), 400

        now = get_current_time().isoformat()

        # Har bir media fayl uchun yangi tartib raqamini belgilash
        for index, media_id in enumerate(media_ids):
            execute_query(
                "UPDATE product_media SET display_order = ?, updated_at = ? WHERE id = ?",
                (index, now, media_id),
            )

        return jsonify(
            {"success": True, "message": "Media fayllar tartibi o'zgartirildi"}
        )

    except Exception as e:
        app_logger.error(f"Reorder product media error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Tartibni o'zgartirishda xatolik"}),
            500,
        )


@app.route("/admin/toggle_menu_item/<int:item_id>", methods=["POST"])
def admin_toggle_menu_item(item_id):
    "Toggle menu item availability"
    if not session.get("staff_id") and not session.get("super_admin"):
        return jsonify({"error": "Authentication required"}), 401

    try:
        execute_query(
            """
            UPDATE menu_items 
            SET available = CASE WHEN available = 1 THEN 0 ELSE 1 END 
            WHERE id = ?
        """,
            (item_id,),
        )

        return jsonify({"success": True, "message": "Mahsulot holati o'zgartirildi"})
    except Exception as e:
        app_logger.error(f"Toggle menu item error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/admin/delete_menu_item/<int:item_id>", methods=["POST"])
def admin_delete_menu_item(item_id):
    "Admin menu item ni butunlay o'chirish"
    if not session.get("staff_id") and not session.get("super_admin"):
        return jsonify({"success": False, "error": "Admin huquqi talab qilinadi"}), 401

    try:
        # Avval mahsulot mavjudligini tekshiramiz
        current_item = execute_query(
            "SELECT id, name FROM menu_items WHERE id = ?", (item_id,), fetch_one=True
        )
        if not current_item:
            return jsonify({"success": False, "error": "Mahsulot topilmadi"}), 404

        item_name = (
            current_item.get("name", "N/A")
            if hasattr(current_item, "get")
            else current_item[1]
        )

        # Bog'langan ma'lumotlarni o'chirish (xavfsizlik uchun)
        # Cart itemsni o'chirish
        execute_query("DELETE FROM cart_items WHERE menu_item_id = ?", (item_id,))

        # Order detailsni o'chirish
        execute_query("DELETE FROM order_details WHERE menu_item_id = ?", (item_id,))

        # Ratingsni o'chirish
        execute_query("DELETE FROM ratings WHERE menu_item_id = ?", (item_id,))

        # Favoritesni o'chirish
        execute_query("DELETE FROM favorites WHERE menu_item_id = ?", (item_id,))

        # Oxirida menu itemni o'chirish
        execute_query("DELETE FROM menu_items WHERE id = ?", (item_id,))

        # Log yozish
        staff_info = (
            f"Staff ID: {session.get('staff_id')}"
            if session.get("staff_id")
            else "Super Admin"
        )
        app_logger.info(
            f"Menu item o'chirildi: {item_name} (ID: {item_id}) by {staff_info}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Mahsulot '{item_name}' muvaffaqiyatli o'chirildi",
            }
        )

    except Exception as e:
        app_logger.error(f"Delete menu item error: {str(e)}")
        return (
            jsonify(
                {"success": False, "error": "Mahsulotni o'chirishda xatolik yuz berdi"}
            ),
            500,
        )


# API routes
@app.route("/api")
def api_home():
    "API home page"
    return jsonify(
        {
            "message": "Restaurant API",
            "version": "1.0",
            "endpoints": [
                "/api/cart-count",
                "/api/menu",
                "/api/orders",
                "/api/status",
                "/api/get-menu-ratings",
            ],
        }
    )


@app.route("/api/get-menu-ratings/<int:menu_item_id>")
def api_get_menu_ratings(menu_item_id):
    "Get ratings for a specific menu item"
    try:
        # Get ratings for the menu item
        ratings_raw = execute_query(
            """
            SELECT r.rating, r.comment, r.created_at,
                   COALESCE(u.first_name || ' ' || u.last_name, 'Anonim') as user_name
            FROM ratings r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.menu_item_id = ?
            ORDER BY r.created_at DESC
            LIMIT 20
        """,
            (menu_item_id,),
            fetch_all=True,
        )

        ratings = [dict(row) for row in ratings_raw] if ratings_raw else []

        # Calculate average rating
        if ratings:
            total_rating = sum(r["rating"] for r in ratings)
            average_rating = round(total_rating / len(ratings), 1)
        else:
            average_rating = 0.0

        return jsonify(
            {
                "success": True,
                "ratings": ratings,
                "average_rating": average_rating,
                "total_ratings": len(ratings),
            }
        )

    except Exception as e:
        app_logger.error(f"Get menu ratings error: {str(e)}")
        return jsonify(
            {
                "success": False,
                "message": "Baholarni yuklashda xatolik",
                "ratings": [],
                "average_rating": 0.0,
                "total_ratings": 0,
            }
        )


@app.route("/api/submit-rating", methods=["POST"])
@csrf_protect
def api_submit_rating():
    """Accept rating submissions for menu items or branches.
    Expected JSON: { menu_item_id: int, rating: int (1-5), comment: str }
    Requires authenticated user (session['user_id']).
    """
    try:
        if not session.get("user_id"):
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        data = request.get_json() or {}
        menu_item_id = data.get("menu_item_id")
        rating = data.get("rating")
        comment = (data.get("comment") or "").strip()

        # Basic validation
        try:
            rating = int(rating)
        except Exception:
            return jsonify({"success": False, "message": "Invalid rating value"}), 400

        if rating < 1 or rating > 5:
            return jsonify({"success": False, "message": "Rating must be 1..5"}), 400

        user_id = session.get("user_id")
        now = get_current_time().isoformat()

        # Allow menu_item_id to be negative to indicate branch rating as existing codebase uses
        if menu_item_id is None:
            return jsonify({"success": False, "message": "menu_item_id required"}), 400

        try:
            menu_item_id_int = int(menu_item_id)
        except Exception:
            return jsonify({"success": False, "message": "Invalid menu_item_id"}), 400

        # Validate that the user exists
        try:
            user_row = execute_query(
                "SELECT id FROM users WHERE id = ?", (user_id,), fetch_one=True
            )
            if not user_row:
                app_logger.warning(f"Submit rating: missing user id={user_id}")
                return jsonify({"success": False, "message": "User not found"}), 400
        except Exception as e:
            app_logger.error(f"Submit rating user check failed: {str(e)}")
            return jsonify({"success": False, "message": "Server error"}), 500

        # Validate menu item or branch existence
        try:
            if menu_item_id_int < 0:
                branch_id = -menu_item_id_int
                branch_row = execute_query(
                    "SELECT id FROM branches WHERE id = ?", (branch_id,), fetch_one=True
                )
                if not branch_row:
                    app_logger.warning(f"Submit rating: missing branch id={branch_id}")
                    return (
                        jsonify({"success": False, "message": "Branch not found"}),
                        400,
                    )
            else:
                mi_row = execute_query(
                    "SELECT id FROM menu_items WHERE id = ?",
                    (menu_item_id_int,),
                    fetch_one=True,
                )
                if not mi_row:
                    app_logger.warning(
                        f"Submit rating: missing menu_item id={menu_item_id_int}"
                    )
                    return (
                        jsonify({"success": False, "message": "Menu item not found"}),
                        400,
                    )
        except Exception as e:
            app_logger.error(f"Submit rating parent check failed: {str(e)}")
            return jsonify({"success": False, "message": "Server error"}), 500

        try:
            if menu_item_id_int < 0:
                branch_id = -menu_item_id_int
                # Insert branch rating (menu_item_id NULL)
                execute_query(
                    "INSERT INTO ratings (menu_item_id, branch_id, user_id, rating, comment, created_at) VALUES (NULL, ?, ?, ?, ?, ?)",
                    (branch_id, user_id, rating, comment, now),
                )
            else:
                # Insert menu item rating (branch_id NULL)
                execute_query(
                    "INSERT INTO ratings (menu_item_id, branch_id, user_id, rating, comment, created_at) VALUES (?, NULL, ?, ?, ?, ?)",
                    (menu_item_id_int, user_id, rating, comment, now),
                )
        except Exception as e:
            # If FK still fails here, log full context for debugging
            if "FOREIGN KEY constraint failed" in str(e):
                app_logger.error(
                    f"Submit rating FK failed for user_id={user_id} menu_item_id={menu_item_id_int}: {str(e)}"
                )
                return (
                    jsonify(
                        {"success": False, "message": "Foreign key constraint failed"}
                    ),
                    400,
                )
            app_logger.error(f"Submit rating insert failed: {str(e)}")
            return jsonify({"success": False, "message": "Server error"}), 500

        return jsonify({"success": True, "message": "Rahmat! Baho qabul qilindi."})
    except Exception as e:
        app_logger.error(f"Submit rating error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/api/status")
def api_status():
    "API status endpoint"
    return jsonify(
        {"status": "OK", "timestamp": get_current_time().isoformat(), "version": "1.0"}
    )


@app.route("/api/news/active", methods=["GET"])
def api_get_active_news():
    """Get active news for ticker display"""
    try:
        # Ensure schema has show_in_ticker
        try:
            cols = execute_query("PRAGMA table_info(news)", fetch_all=True)
            has_show = False
            if cols:
                for c in cols:
                    name = c[1] if isinstance(c, tuple) else c.get("name")
                    if name == "show_in_ticker":
                        has_show = True
                        break
            if not has_show:
                try:
                    execute_query(
                        "ALTER TABLE news ADD COLUMN show_in_ticker BOOLEAN DEFAULT 0"
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Get active ticker news sorted by display order
        news_query = """
            SELECT id, title, content, type, image_url, video_url, is_active, display_order, created_at 
            FROM news 
            WHERE is_active = 1 AND COALESCE(show_in_ticker, 0) = 1
            ORDER BY display_order ASC, created_at DESC
            LIMIT 20
        """

        news_items = execute_query(news_query, fetch_all=True)

        if news_items:
            news_list = []
            for item in news_items:
                news_dict = {
                    "id": item[0] if isinstance(item, tuple) else item.get("id"),
                    "title": (
                        item[1] if isinstance(item, tuple) else item.get("title", "")
                    ),
                    "content": (
                        item[2] if isinstance(item, tuple) else item.get("content", "")
                    ),
                    "type": (
                        item[3] if isinstance(item, tuple) else item.get("type", "news")
                    ),
                    "image_url": (
                        item[4] if isinstance(item, tuple) else item.get("image_url")
                    ),
                    "video_url": (
                        item[5] if isinstance(item, tuple) else item.get("video_url")
                    ),
                    "is_active": bool(
                        item[6]
                        if isinstance(item, tuple)
                        else item.get("is_active", False)
                    ),
                    "display_order": (
                        item[7]
                        if isinstance(item, tuple)
                        else item.get("display_order", 0)
                    ),
                    "created_at": (
                        item[8]
                        if isinstance(item, tuple)
                        else item.get("created_at", "")
                    ),
                }
                news_list.append(news_dict)

            return jsonify(
                {"success": True, "news": news_list, "total": len(news_list)}
            )
        else:
            return jsonify({"success": True, "news": [], "total": 0})

    except Exception as e:
        app_logger.error(f"Get active news error: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Yangiliklar yuklanmadi",
                    "news": [],
                    "total": 0,
                }
            ),
            500,
        )


@app.route("/api/payment-cards", methods=["GET"])
def api_get_payment_cards():
    """Get active payment cards for cart display"""
    try:
        # Get active payment cards sorted by display order
        cards_query = """
            SELECT id, card_name, card_number, card_holder_name, bank_name, 
                   card_type, is_active, display_order
            FROM payment_cards 
            WHERE is_active = 1 
            ORDER BY display_order ASC, id ASC
        """

        cards_items = execute_query(cards_query, fetch_all=True)

        if cards_items:
            cards_list = []
            for item in cards_items:
                card_dict = {
                    "id": item[0] if isinstance(item, tuple) else item.get("id"),
                    "card_name": (
                        item[1]
                        if isinstance(item, tuple)
                        else item.get("card_name", "")
                    ),
                    "card_number": (
                        item[2]
                        if isinstance(item, tuple)
                        else item.get("card_number", "")
                    ),
                    "card_holder_name": (
                        item[3]
                        if isinstance(item, tuple)
                        else item.get("card_holder_name", "")
                    ),
                    "bank_name": (
                        item[4]
                        if isinstance(item, tuple)
                        else item.get("bank_name", "")
                    ),
                    "card_type": (
                        item[5]
                        if isinstance(item, tuple)
                        else item.get("card_type", "visa")
                    ),
                    "is_active": bool(
                        item[6]
                        if isinstance(item, tuple)
                        else item.get("is_active", False)
                    ),
                    "display_order": (
                        item[7]
                        if isinstance(item, tuple)
                        else item.get("display_order", 0)
                    ),
                }
                cards_list.append(card_dict)

            return jsonify(
                {"success": True, "cards": cards_list, "total": len(cards_list)}
            )
        else:
            return jsonify({"success": True, "cards": [], "total": 0})

    except Exception as e:
        app_logger.error(f"Get payment cards error: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "To'lov kartalari yuklanmadi",
                    "cards": [],
                    "total": 0,
                }
            ),
            500,
        )


@app.route("/api/payment-methods", methods=["GET"])
def api_get_payment_methods():
    """Get available payment methods for cart"""
    try:
        payment_methods = {
            "cash": {"available": True, "name": "Naqd pul", "icon": "💵"},
            "card": {
                "available": False,
                "name": "Bank kartasi",
                "icon": "💳",
                "cards": [],
            },
            "click": {
                "available": False,
                "name": "Click",
                "icon": "🟦",
                "qr_url": None,
            },
            "payme": {
                "available": False,
                "name": "Payme",
                "icon": "🟨",
                "qr_url": None,
            },
        }

        # Check for active payment cards
        cards = execute_query(
            "SELECT id, card_name, card_number, card_holder_name, bank_name FROM payment_cards WHERE is_active = 1 ORDER BY display_order ASC",
            fetch_all=True,
        )

        if cards:
            payment_methods["card"]["available"] = True
            payment_methods["card"]["cards"] = cards

        # Check for QR codes
        qr_settings = execute_query(
            "SELECT click_qr_url, payme_qr_url FROM card_payment_settings WHERE id = 1",
            fetch_one=True,
        )

        if qr_settings:
            if qr_settings.get("click_qr_url"):
                payment_methods["click"]["available"] = True
                payment_methods["click"]["qr_url"] = qr_settings["click_qr_url"]

            if qr_settings.get("payme_qr_url"):
                payment_methods["payme"]["available"] = True
                payment_methods["payme"]["qr_url"] = qr_settings["payme_qr_url"]

        return jsonify({"success": True, "payment_methods": payment_methods})

    except Exception as e:
        app_logger.error(f"Get payment methods error: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "To'lov usullari yuklanmadi",
                    "payment_methods": {
                        "cash": {"available": True, "name": "Naqd pul", "icon": "💵"}
                    },
                }
            ),
            500,
        )


@app.route("/api/set-language", methods=["POST"])
def api_set_language():
    "Set user language preference"
    try:
        data = request.get_json()
        language = data.get("language", "uz")

        # Validate language
        if language not in ["uz", "ru", "en"]:
            language = "uz"

        # Save to session
        session["interface_language"] = language

        # If user is logged in, save to database
        user_id = session.get("user_id")
        if user_id:
            try:
                execute_query(
                    "UPDATE users SET interface_language = ? WHERE id = ?",
                    (language, user_id),
                )
            except Exception as db_error:
                app_logger.error(f"Error saving language to database: {str(db_error)}")

        return jsonify(
            {
                "success": True,
                "message": "Til muvaffaqiyatli o'zgartirildi",
                "language": language,
            }
        )
    except Exception as e:
        app_logger.error(f"Set language error: {str(e)}")
        return jsonify({"success": False, "message": "Til o'zgartirishda xatolik"}), 500


@app.route("/api/set-theme", methods=["POST"])
def api_set_theme():
    "Set user theme preference"
    try:
        data = request.get_json()
        dark_theme = data.get("dark_theme", True)

        # Save to session
        session["dark_theme"] = bool(dark_theme)

        # If user is logged in, save to database
        user_id = session.get("user_id")
        if user_id:
            try:
                execute_query(
                    "UPDATE users SET dark_theme = ? WHERE id = ?",
                    (1 if dark_theme else 0, user_id),
                )
            except Exception as db_error:
                app_logger.error(f"Error saving theme to database: {str(db_error)}")

        return jsonify(
            {
                "success": True,
                "message": "Mavzu muvaffaqiyatli o'zgartirildi",
                "dark_theme": dark_theme,
            }
        )
    except Exception as e:
        app_logger.error(f"Set theme error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Mavzu o'zgartirishda xatolik"}),
            500,
        )


@app.route("/api/set-font-size", methods=["POST"])
def api_set_font_size():
    "Set user font size preference"
    try:
        data = request.get_json()
        font_size = data.get("font_size", "medium")

        # Validate font size
        if font_size not in ["small", "medium", "large", "xlarge"]:
            font_size = "medium"

        # Save to session
        session["font_size"] = font_size

        # If user is logged in, save to database
        user_id = session.get("user_id")
        if user_id:
            try:
                execute_query(
                    "UPDATE users SET font_size = ? WHERE id = ?", (font_size, user_id)
                )
            except Exception as db_error:
                app_logger.error(f"Error saving font size to database: {str(db_error)}")

        return jsonify(
            {
                "success": True,
                "message": "Shrift o'lchami muvaffaqiyatli o'zgartirildi",
                "font_size": font_size,
            }
        )
    except Exception as e:
        app_logger.error(f"Set font size error: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Shrift o'lchamini o'zgartirishda xatolik",
                }
            ),
            500,
        )


@app.route("/api/search-nearby-places", methods=["POST"])
def api_search_nearby_places():
    "Yaqin joylarni qidirish API"
    try:
        data = request.get_json()
        query = data.get("query", "restoran")
        user_latitude = float(data.get("latitude", 41.2995))
        user_longitude = float(data.get("longitude", 69.2401))
        radius = int(data.get("radius", 2000))  # metrda

        # Location service orqali qidirish
        if location_service:
            search_result = location_service.search_places(f"{query} Toshkent")

            if search_result.get("places"):
                # Faqat radius ichidagi joylarni qaytarish
                nearby_places = []
                for place in search_result["places"][:10]:  # maksimal 10 ta
                    if place.get("gps_coordinates"):
                        place_lat = place["gps_coordinates"].get("latitude", 0)
                        place_lng = place["gps_coordinates"].get("longitude", 0)

                        if place_lat and place_lng:
                            # Masofani hisoblash
                            import math

                            lat1, lng1 = math.radians(user_latitude), math.radians(
                                user_longitude
                            )
                            lat2, lng2 = math.radians(place_lat), math.radians(
                                place_lng
                            )

                            dlat = lat2 - lat1
                            dlng = lng2 - lng1

                            a = (
                                math.sin(dlat / 2) ** 2
                                + math.cos(lat1)
                                * math.cos(lat2)
                                * math.sin(dlng / 2) ** 2
                            )
                            c = 2 * math.asin(math.sqrt(a))
                            distance_m = 6371000 * c  # metrda

                            if distance_m <= radius:
                                nearby_places.append(
                                    {
                                        "name": place.get("title", query),
                                        "address": place.get("address", ""),
                                        "latitude": place_lat,
                                        "longitude": place_lng,
                                        "distance": round(distance_m),
                                        "rating": place.get("rating", 0),
                                    }
                                )

                return jsonify(
                    {
                        "success": True,
                        "places": nearby_places,
                        "total": len(nearby_places),
                    }
                )

        # Fallback - demo data
        demo_places = [
            {
                "name": f"Demo {query.title()} 1",
                "address": "Toshkent shahri",
                "latitude": user_latitude + 0.001,
                "longitude": user_longitude + 0.001,
                "distance": 150,
                "rating": 4.2,
            },
            {
                "name": f"Demo {query.title()} 2",
                "address": "Toshkent shahri",
                "latitude": user_latitude - 0.002,
                "longitude": user_longitude + 0.002,
                "distance": 300,
                "rating": 4.5,
            },
        ]

        return jsonify(
            {"success": True, "places": demo_places, "total": len(demo_places)}
        )

    except Exception as e:
        app_logger.error(f"Search nearby places API error: {str(e)}")
        return jsonify(
            {"success": False, "message": "Qidirishda xatolik yuz berdi", "places": []}
        )


@app.route("/api/find-nearest-branch", methods=["POST"])
def api_find_nearest_branch():
    "Eng yaqin filialni topish API"
    try:
        data = request.get_json()
        user_latitude = float(data.get("latitude", 41.2995))
        user_longitude = float(data.get("longitude", 69.2401))

        # Eng yaqin filialni topish
        nearest_branch_data = find_nearest_branch(user_latitude, user_longitude)

        if nearest_branch_data:
            branch = nearest_branch_data["branch"]
            distance = nearest_branch_data["distance"]

            # Yetkazib berish narxi va vaqtini hisoblash
            delivery_cost, delivery_time = calculate_delivery_cost_and_time(distance)

            return jsonify(
                {
                    "success": True,
                    "branch": {
                        "id": branch["id"],
                        "name": branch["name"],
                        "address": branch["address"],
                        "latitude": branch["latitude"],
                        "longitude": branch["longitude"],
                        "phone": branch.get("phone", ""),
                        "working_hours": branch.get("working_hours", "09:00-22:00"),
                    },
                    "distance": distance,
                    "delivery_cost": delivery_cost,
                    "delivery_time": delivery_time,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "Yaqin atrofda faol filial topilmadi. Iltimos, boshqa manzilni sinab ko'ring.",
                }
            )

    except Exception as e:
        app_logger.error(f"Find nearest branch API error: {str(e)}")
        return jsonify(
            {"success": False, "message": "Filial topishda xatolik yuz berdi"}
        )


@app.route("/api/health")
def api_health():
    "Health check endpoint"
    try:
        # Database connection test
        execute_query("SELECT 1", fetch_one=True)

        return jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": get_current_time().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": get_current_time().isoformat(),
                }
            ),
            500,
        )


@app.route("/get_cart_count")
@app.route("/api/cart-count")
def api_cart_count():
    "Savatchadagi mahsulotlar sonini qaytarish - API endpoint"
    try:
        session_id = get_session_id()
        user_id = session.get("user_id")

        # Cache dan olishga harakat qilish (lazy-init cache_manager)
        cache_key = f"cart_count_{user_id}_{session_id}"
        cm = get_cache_manager()
        cached_count = None
        try:
            if cm is not None:
                cached_count = cm.get(cache_key)
        except Exception as cache_err:
            app_logger.warning(f"Cache get error in api_cart_count: {str(cache_err)}")

        if cached_count is not None:
            return jsonify({"success": True, "cart_count": cached_count})

        # Hisoblash
        cart_count = 0

        try:
            if user_id:
                cart_count_result = execute_query(
                    "SELECT COALESCE(SUM(quantity), 0) as total_count FROM cart_items WHERE user_id = ?",
                    (user_id,),
                    fetch_one=True,
                )
            else:
                cart_count_result = execute_query(
                    "SELECT COALESCE(SUM(quantity), 0) as total_count FROM cart_items WHERE session_id = ?",
                    (session_id,),
                    fetch_one=True,
                )

            # Extract count from result - handle both dict and tuple formats
            if cart_count_result:
                if isinstance(cart_count_result, dict):
                    cart_count = cart_count_result.get("total_count", 0) or 0
                elif (
                    isinstance(cart_count_result, (list, tuple))
                    and len(cart_count_result) > 0
                ):
                    cart_count = cart_count_result[0] or 0
                elif isinstance(cart_count_result, (int, float)):
                    cart_count = int(cart_count_result)
                else:
                    cart_count = 0

            # Type validation
            cart_count = max(0, int(cart_count)) if cart_count is not None else 0

        except Exception as query_error:
            app_logger.error(f"Cart count query error: {str(query_error)}")
            cart_count = 0

        # Cache ga saqlash
        try:
            if cm is not None:
                cm.set(cache_key, cart_count, ttl=60)
        except Exception as cache_err:
            app_logger.warning(f"Cache set error in api_cart_count: {str(cache_err)}")

        return jsonify(
            {
                "success": True,
                "cart_count": cart_count,
                "user_id": user_id,
                "session_id": session_id[:8] if session_id else None,
            }
        )

    except Exception as e:
        app_logger.error(f"Cart count API error: {str(e)}")
        return (
            jsonify({"success": False, "cart_count": 0, "error": "API xatoligi"}),
            500,
        )


# Cart count endpoint moved to top priority section


# Admin panel redirects
@app.route("/admin-panel")
@app.route("/admin-panel-secure")
@app.route("/admin-dashboard")
def admin_panel_redirect():
    "Admin panel redirects"
    if session.get("super_admin"):
        return redirect(url_for("super_admin_dashboard"))
    elif session.get("staff_id"):
        return redirect(url_for("staff_dashboard"))
    else:
        return redirect(url_for("staff_login"))


@app.route("/staff-panel")
@app.route("/employee-panel")
def staff_panel_redirect():
    "Staff panel redirects"
    if session.get("staff_id"):
        return redirect(url_for("staff_dashboard"))
    else:
        return redirect(url_for("staff_login"))


@app.route("/courier-panel")
def courier_panel_redirect():
    "Courier panel redirects"
    if session.get("courier_id"):
        return redirect(url_for("courier_dashboard"))
    else:
        return redirect(url_for("courier_login"))


# ---- STATIC FILE HANDLING ----
@app.route("/static/<path:filename>")
def static_files(filename):
    "Static fayllar uchun xavfsiz route"
    try:
        return app.send_static_file(filename)
    except Exception as e:
        app_logger.error(f"Static file error for {filename}: {str(e)}")
        return "File not found", 404


# Order tracking route
@app.route("/order/<int:ticket_no>")
def track_order(ticket_no):
    "Buyurtma holatini kuzatish"
    try:
        order = execute_query(
            "SELECT * FROM orders WHERE ticket_no = ?", (ticket_no,), fetch_one=True
        )

        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("index"))

        # Buyurtma tafsilotlarini olish
        order_items_raw = execute_query(
            """
            SELECT od.quantity, mi.name, od.price
            FROM order_details od
            JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE od.order_id = ?
        """,
            (order["id"],),
            fetch_all=True,
        )
        order_items = [dict(row) for row in order_items_raw] if order_items_raw else []

        return render_template(
            "user_success.html", order=order, order_items=order_items
        )

    except Exception as e:
        app_logger.error(f"Track order error: {str(e)}")
        flash("Buyurtma ma'lumotlarini yuklashda xatolik.", "error")
        return redirect(url_for("index"))


# ---- LOGIN ROUTES ----
@app.route("/login")
def login():
    "Login route - login_page ga yo'naltirish"
    # URL dan role parametrini tekshirish
    role_param = request.args.get("role")

    if role_param == "staff":
        return redirect(url_for("staff_login"))
    elif role_param == "courier":
        return redirect(url_for("courier_login"))
    elif role_param == "admin":
        return redirect(url_for("super_admin_login"))
    else:
        # Regular user login
        return redirect(url_for("login_page"))


@app.route("/login_page", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email va parolni kiriting.", "error")
            return redirect(url_for("login_page"))

        user = execute_query(
            "SELECT * FROM users WHERE email = ?", (email,), fetch_one=True
        )

        if user:
            try:
                # SQLite Row obyektini xavfsiz dict ga aylantirish
                user_dict = dict(user)

                password_hash = user_dict.get("password_hash", "")

                if password_hash and check_password_hash(password_hash, password):
                    # Use secure helper to set session and avoid mixed-role conflicts
                    user_id = user_dict.get("id")
                    session_payload = {
                        "user_id": user_id,
                        "first_name": user_dict.get("first_name", ""),
                        "last_name": user_dict.get("last_name", ""),
                        "email": user_dict.get("email", ""),
                        "phone": user_dict.get("phone", ""),
                        "address": user_dict.get("address", ""),
                        "address_latitude": user_dict.get("address_latitude"),
                        "address_longitude": user_dict.get("address_longitude"),
                        "avatar": user_dict.get("avatar")
                        or user_dict.get("gravatar")
                        or None,
                    }

                    secure_session_login("user", session_payload)
                    # UI preferences
                    session["interface_language"] = (
                        user_dict.get("interface_language")
                        or session.get("interface_language")
                        or "uz"
                    )
                    session["font_size"] = (
                        user_dict.get("font_size")
                        or session.get("font_size")
                        or "medium"
                    )
                    session["dark_theme"] = bool(
                        user_dict.get("dark_theme", session.get("dark_theme", 1))
                    )

                    flash(
                        f"Xush kelibsiz, {user_dict.get('first_name','')}!", "success"
                    )
                    return redirect(url_for("index"))
                else:
                    flash("Noto'g'ri email yoki parol.", "error")
                    app_logger.warning(f"Failed login attempt for email: {email}")
                    return redirect(url_for("login_page"))
            except Exception as login_error:
                app_logger.error(f"User login processing error: {str(login_error)}")
                flash("Login jarayonida xatolik yuz berdi.", "error")
                return redirect(url_for("login_page"))
        else:
            flash("Foydalanuvchi topilmadi.", "error")
            return redirect(url_for("login_page"))

    return render_template("login.html")


# ---- SUPER ADMIN ROUTES ----
# Super admin kredentsiallari - universal konfiguratsiyadan
SUPER_ADMIN_USERNAME = Config.SUPER_ADMIN_USERNAME
SUPER_ADMIN_PASSWORD = Config.SUPER_ADMIN_PASSWORD


SUPERADMIN_SETTINGS_PATH = os.path.join(
    os.path.dirname(__file__), "superadmin_settings.json"
)


def load_superadmin_settings():
    try:
        if os.path.exists(SUPERADMIN_SETTINGS_PATH):
            with open(SUPERADMIN_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
                return data
    except Exception as e:
        try:
            app_logger.error(f"Failed to load superadmin settings: {e}")
        except Exception:
            pass
    return {}


def save_superadmin_settings(data: dict):
    try:
        # ensure directory exists
        d = os.path.dirname(SUPERADMIN_SETTINGS_PATH)
        os.makedirs(d, exist_ok=True)
        # atomic write
        tmp = SUPERADMIN_SETTINGS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, SUPERADMIN_SETTINGS_PATH)
        return True
    except Exception as e:
        try:
            app_logger.error(f"Failed to save superadmin settings: {e}")
        except Exception:
            pass
        return False


def get_superadmin_creds():
    settings = load_superadmin_settings() or {}
    username = settings.get("username") or Config.SUPER_ADMIN_USERNAME
    password = settings.get("password") or Config.SUPER_ADMIN_PASSWORD
    # other profile fields
    first_name = settings.get("first_name") or settings.get("name") or ""
    last_name = settings.get("last_name") or ""
    phone = settings.get("phone") or ""
    avatar = settings.get("avatar") or None
    return {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "avatar": avatar,
    }


# News storage path (simple JSON-backed list so we don't alter DB schema)
NEWS_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "news.json")


def load_news():
    try:
        if os.path.exists(NEWS_STORAGE_PATH):
            with open(NEWS_STORAGE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f) or []
                # ensure it's a list and sort by created_at desc
                if isinstance(data, list):
                    return sorted(
                        data, key=lambda x: x.get("created_at", ""), reverse=True
                    )
    except Exception as e:
        try:
            app_logger.error(f"Failed to load news: {e}")
        except Exception:
            pass
    return []


def save_news(list_of_items):
    try:
        d = os.path.dirname(NEWS_STORAGE_PATH)
        os.makedirs(d, exist_ok=True)
        tmp = NEWS_STORAGE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(list_of_items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, NEWS_STORAGE_PATH)
        return True
    except Exception as e:
        try:
            app_logger.error(f"Failed to save news: {e}")
        except Exception:
            pass
    return False


@app.route("/news")
def news_page():
    """Public news list from database (active only)"""
    try:
        rows = (
            execute_query(
                "SELECT id, title, content, type, image_url, video_url, is_active, display_order, created_at FROM news WHERE is_active = 1 ORDER BY display_order ASC, created_at DESC",
                fetch_all=True,
            )
            or []
        )

        # Normalize rows to dicts
        news_items = []
        for r in rows:
            if isinstance(r, dict):
                item = r
            else:
                # tuple ordering per SELECT above
                item = {
                    "id": r[0],
                    "title": r[1],
                    "content": r[2],
                    "type": r[3],
                    "image_url": r[4],
                    "video_url": r[5],
                    "is_active": bool(r[6]),
                    "display_order": r[7],
                    "created_at": r[8],
                }
            news_items.append(item)

        return render_template("news.html", news=news_items)
    except Exception as e:
        app_logger.error(f"News page error: {e}")
        flash("Yangiliklarni yuklashda xatolik.", "error")
        return redirect(url_for("index"))


@app.route("/super-admin/news", methods=["GET"])
@role_required("super_admin")
def super_admin_news_list():
    news = load_news()
    return render_template("admin/news_manage.html", news=news)


@app.route("/super-admin/news/add", methods=["POST"])
@role_required("super_admin")
def super_admin_add_news():
    try:
        title = request.form.get("title", "").strip()
        image_url = request.form.get("image_url", "").strip() or None
        youtube_url = request.form.get("youtube_url", "").strip() or None
        video_url = request.form.get("video_url", "").strip() or None
        description = request.form.get("description", "").strip() or ""
        published = bool(request.form.get("published"))

        if not title:
            flash("Sarlavha majburiy.", "error")
            return redirect(url_for("super_admin_news_list"))

        news = load_news()
        new_id = max([n.get("id", 0) for n in news] or [0]) + 1
        item = {
            "id": new_id,
            "title": title,
            "image": image_url,
            "youtube_url": youtube_url,
            "video": video_url,
            "description": description,
            "published": published,
            "created_at": get_current_time().isoformat(),
        }
        news.insert(0, item)
        ok = save_news(news)
        if ok:
            flash("Yangilik qo'shildi.", "success")
        else:
            flash("Yangilikni saqlashda xatolik.", "error")
        return redirect(url_for("super_admin_news_list"))
    except Exception as e:
        app_logger.error(f"Add news error: {e}")
        flash("Yangilikni qo'shishda xatolik.", "error")
        return redirect(url_for("super_admin_news_list"))


@app.route("/super-admin/news/delete/<int:news_id>", methods=["POST"])
@role_required("super_admin")
def super_admin_delete_news(news_id):
    try:
        news = load_news()
        newlist = [n for n in news if int(n.get("id", 0)) != int(news_id)]
        ok = save_news(newlist)
        if ok:
            flash("Yangilik o'chirildi.", "success")
        else:
            flash("Yangilikni o'chirishda xatolik.", "error")
        return redirect(url_for("super_admin_news_list"))
    except Exception as e:
        app_logger.error(f"Delete news error: {e}")
        flash("Yangilikni o'chirishda xatolik.", "error")
        return redirect(url_for("super_admin_news_list"))


def clear_role_sessions():
    """Clear all known role-related session keys to avoid role leakage."""
    keys = [
        "super_admin",
        "super_admin_name",
        "super_admin_first_name",
        "super_admin_last_name",
        "super_admin_phone",
        "super_admin_avatar",
        "staff_id",
        "staff_name",
        "courier_id",
        "courier_name",
        "user_id",
        "user_name",
    ]
    for k in keys:
        session.pop(k, None)


def set_role_session(role, id=None, name=None, **kwargs):
    """Set a single role in session and clear other role flags.

    role: one of 'super_admin', 'staff', 'courier', 'user'
    id: numeric id for staff/courier/user when applicable
    name: display name
    kwargs: additional metadata (first_name, last_name, phone, avatar)
    """
    clear_role_sessions()
    if role == "super_admin":
        session["super_admin"] = True
        if name:
            session["super_admin_name"] = name
        session["super_admin_first_name"] = kwargs.get("first_name", "")
        session["super_admin_last_name"] = kwargs.get("last_name", "")
        session["super_admin_phone"] = kwargs.get("phone", "")
        session["super_admin_avatar"] = kwargs.get("avatar")
    elif role == "staff":
        if id is not None:
            session["staff_id"] = id
        if name:
            session["staff_name"] = name
    elif role == "courier":
        if id is not None:
            session["courier_id"] = id
        if name:
            session["courier_name"] = name
    elif role == "user":
        if id is not None:
            session["user_id"] = id
        if name:
            session["user_name"] = name


@app.route("/super-admin-master-login-z9x4m", methods=["GET", "POST"])
def super_admin_login():
    "Super admin login"
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        creds = get_superadmin_creds()
        if username == creds.get("username") and password == creds.get("password"):
            # Use helper to set role and clear other role flags
            name_parts = []
            if creds.get("first_name"):
                name_parts.append(creds.get("first_name"))
            if creds.get("last_name"):
                name_parts.append(creds.get("last_name"))
            display_name = " ".join(name_parts) if name_parts else "Super Administrator"
            # Load avatar from persistent settings
            persistent_avatar = (
                creds.get("avatar") or "/static/images/default-avatar.svg"
            )

            set_role_session(
                "super_admin",
                name=display_name,
                first_name=creds.get("first_name", ""),
                last_name=creds.get("last_name", ""),
                phone=creds.get("phone", ""),
                avatar=persistent_avatar,
            )

            # Ensure user_avatar is also set for template consistency
            session["user_avatar"] = persistent_avatar

            app_logger.info(f"Super admin kirdi: {username}")
            flash("Super Admin tizimiga xush kelibsiz!", "success")
            return redirect(url_for("super_admin_dashboard"))
        else:
            app_logger.warning(f"Super admin login failed for username: {username}")
            flash("Noto'g'ri username yoki parol.", "error")

    return render_template("super_admin_login.html")


@app.route("/super-admin/logout")
def super_admin_logout():
    "Super admin logout"
    # Terminate the session in database if session_id exists
    current_session_id = session.get("session_id")
    if current_session_id:
        try:
            terminate_session(current_session_id, current_session_id=current_session_id)
        except Exception as e:
            app_logger.warning(
                f"Failed to terminate super admin session in database: {e}"
            )

    session.clear()  # Clear entire session instead of just popping specific keys
    flash("Super Admin tizimidan chiqdingiz.", "info")
    return redirect(url_for("index"))


@app.route("/super-admin/profile")
@role_required("super_admin")
def super_admin_profile():
    creds = get_superadmin_creds()
    user = {
        "first_name": creds.get("first_name", ""),
        "last_name": creds.get("last_name", ""),
        "phone": creds.get("phone", ""),
        "username": creds.get("username", ""),
        "avatar": creds.get("avatar") or "/static/images/default-avatar.svg",
    }
    return render_template("super_admin_profile.html", user=user)


@app.route("/super-admin/profile/update", methods=["POST"])
@role_required("super_admin")
def super_admin_profile_update():
    try:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()

        avatar_file = None
        try:
            avatar_file = request.files.get("avatar")
        except Exception:
            avatar_file = None

        settings = load_superadmin_settings() or {}

        if username:
            settings["username"] = username
        if password:
            settings["password"] = password
        settings["first_name"] = first_name
        settings["last_name"] = last_name
        settings["phone"] = phone

        # handle avatar upload
        if avatar_file and avatar_file.filename:
            fname = secure_filename(avatar_file.filename)
            ext = os.path.splitext(fname)[1].lower()
            if ext.replace(".", "") in app.config.get(
                "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"}
            ):
                unique = f"superadmin_{uuid.uuid4().hex}{ext}"
                save_path = os.path.join(
                    app.config.get("UPLOAD_FOLDER", "static/uploads"), unique
                )
                avatar_file.save(save_path)
                settings["avatar"] = "/" + os.path.join(
                    app.config.get("UPLOAD_FOLDER", "static/uploads"), unique
                ).replace("\\", "/")

        ok = save_superadmin_settings(settings)
        if ok:
            # Refresh session values
            session["super_admin_first_name"] = settings.get("first_name", "")
            session["super_admin_last_name"] = settings.get("last_name", "")
            session["super_admin_phone"] = settings.get("phone", "")
            session["super_admin_avatar"] = settings.get("avatar")
            # Also update the main user_avatar session key
            session["user_avatar"] = (
                settings.get("avatar") or "/static/images/default-avatar.svg"
            )

            flash("Profil saqlandi", "success")
        else:
            flash("Profilni saqlashda xatolik", "error")

        return redirect(url_for("super_admin_profile"))
    except Exception as e:
        app_logger.error(f"Super admin profile update error: {str(e)}")
        flash("Server xatolik", "error")
        return redirect(url_for("super_admin_profile"))


# Missing Super Admin API Routes
@app.route("/super-admin/get-orders")
@role_required("super_admin")
def super_admin_get_orders():
    if not session.get("super_admin"):
        return jsonify({"error": "Super admin huquqi kerak"}), 401
        return jsonify({"error": "Super admin huquqi kerak"}), 401

    try:
        orders_raw = execute_query(
            """
            SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 100
        """,
            fetch_all=True,
        )

        orders = [dict(row) for row in orders_raw] if orders_raw else []
        return jsonify(orders)
    except Exception as e:
        app_logger.error(f"Super admin get orders error: {str(e)}")
        return jsonify([])


@app.route("/super-admin/get-menu")
@role_required("super_admin")
def super_admin_get_menu():
    if not session.get("super_admin"):
        return jsonify({"error": "Super admin huquqi kerak"}), 401
        return jsonify({"error": "Super admin huquqi kerak"}), 401

    try:
        menu_raw = execute_query(
            "SELECT * FROM menu_items ORDER BY category, name", fetch_all=True
        )
        menu = [dict(row) for row in menu_raw] if menu_raw else []
        return jsonify(menu)
    except Exception as e:
        app_logger.error(f"Super admin get menu error: {str(e)}")
        return jsonify([])


@app.route("/super-admin/get-receipts")
@role_required("super_admin")
def super_admin_get_receipts():
    if not session.get("super_admin"):
        return jsonify({"error": "Super admin huquqi kerak"}), 401
        return jsonify({"error": "Super admin huquqi kerak"}), 401

    try:
        receipts_raw = execute_query(
            "SELECT * FROM receipts ORDER BY created_at DESC LIMIT 50", fetch_all=True
        )
        receipts = [dict(row) for row in receipts_raw] if receipts_raw else []
        return jsonify(receipts)
    except Exception as e:
        app_logger.error(f"Super admin get receipts error: {str(e)}")
        return jsonify([])


@app.route("/super-admin/get-ratings")
def super_admin_get_ratings():
    if not session.get("super_admin"):
        return jsonify({"error": "Super admin huquqi kerak"}), 401

    try:
        # Menu ratings
        menu_ratings_raw = execute_query(
            """
            SELECT r.*, mi.name as menu_item_name, 
                   COALESCE(u.first_name || ' ' || u.last_name, 'Anonim') as user_name
            FROM ratings r
            LEFT JOIN menu_items mi ON r.menu_item_id = mi.id
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.menu_item_id > 0
            ORDER BY r.created_at DESC
            LIMIT 50
        """,
            fetch_all=True,
        )

        menu_ratings = (
            [dict(row) for row in menu_ratings_raw] if menu_ratings_raw else []
        )

        # Branch ratings (negative menu_item_id)
        branch_ratings_raw = execute_query(
            """
            SELECT r.*, b.name as branch_name, 
                   COALESCE(u.first_name || ' ' || u.last_name, 'Anonim') as user_name
            FROM ratings r
            LEFT JOIN branches b ON r.menu_item_id = -b.id
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.menu_item_id < 0
            ORDER BY r.created_at DESC
            LIMIT 50
        """,
            fetch_all=True,
        )

        branch_ratings = (
            [dict(row) for row in branch_ratings_raw] if branch_ratings_raw else []
        )

        return jsonify({"menu_ratings": menu_ratings, "branch_ratings": branch_ratings})
    except Exception as e:
        app_logger.error(f"Super admin get ratings error: {str(e)}")
        return jsonify({"menu_ratings": [], "branch_ratings": []})


@app.route("/super-admin/add-menu-item", methods=["POST"])
@role_required("super_admin")
def super_admin_add_menu_item():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        name = request.form.get("name", "").strip()
        price = float(request.form.get("price", 0))
        # Default to 'men' (Erkaklar) for new items - all products are for men only
        category = request.form.get("category", "men")
        description = request.form.get("description", "").strip()

        if not name or price <= 0:
            flash("Nomi va narxi to'g'ri bo'lishi kerak.", "error")
            return redirect(url_for("super_admin_dashboard"))

        now = get_current_time().isoformat()
        execute_query(
            """
            INSERT INTO menu_items (name, price, category, description, created_at, available)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (name, price, category, description, now),
        )

        flash("Yangi mahsulot qo'shildi!", "success")
    except Exception as e:
        app_logger.error(f"Super admin add menu item error: {str(e)}")
        flash("Mahsulot qo'shishda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/add-branch", methods=["POST"])
@role_required("super_admin")
def super_admin_add_branch():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        latitude = float(request.form.get("latitude", 0))
        longitude = float(request.form.get("longitude", 0))
        phone = request.form.get("phone", "").strip()
        working_hours = request.form.get("working_hours", "09:00-22:00")
        delivery_radius = float(request.form.get("delivery_radius", 15))

        if not all([name, address]) or latitude == 0 or longitude == 0:
            flash("Barcha majburiy maydonlarni to'ldiring.", "error")
            return redirect(url_for("super_admin_dashboard"))

        now = get_current_time().isoformat()
        execute_query(
            """
            INSERT INTO branches (name, address, latitude, longitude, phone, working_hours, delivery_radius, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
            (
                name,
                address,
                latitude,
                longitude,
                phone,
                working_hours,
                delivery_radius,
                now,
            ),
        )

        flash("Yangi filial qo'shildi!", "success")
    except Exception as e:
        app_logger.error(f"Super admin add branch error: {str(e)}")
        flash("Filial qo'shishda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/toggle-branch/<int:branch_id>", methods=["POST"])
@role_required("super_admin")
def super_admin_toggle_branch(branch_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        execute_query(
            "UPDATE branches SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (branch_id,),
        )
        flash("Filial holati o'zgartirildi.", "success")
    except Exception as e:
        app_logger.error(f"Super admin toggle branch error: {str(e)}")
        flash("Filial holatini o'zgartirishda xatolik.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/delete-branch/<int:branch_id>", methods=["POST"])
@role_required("super_admin")
def super_admin_delete_branch(branch_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        execute_query("DELETE FROM branches WHERE id = ?", (branch_id,))
        flash("Filial o'chirildi.", "success")
    except Exception as e:
        app_logger.error(f"Super admin delete branch error: {str(e)}")
        flash("Filialni o'chirishda xatolik.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/delete-user-db/<int:user_id>", methods=["POST"])
@role_required("super_admin")
def super_admin_delete_user_db(user_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        user_data = execute_query(
            "SELECT first_name, last_name FROM users WHERE id = ?",
            (user_id,),
            fetch_one=True,
        )
        if not user_data:
            flash("Foydalanuvchi topilmadi.", "error")
        else:
            # Delete related data first
            execute_query("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
            execute_query("DELETE FROM favorites WHERE user_id = ?", (user_id,))
            execute_query("DELETE FROM ratings WHERE user_id = ?", (user_id,))
            execute_query("DELETE FROM users WHERE id = ?", (user_id,))

            flash(
                f"Foydalanuvchi {user_data.get('first_name', 'N/A')} {user_data.get('last_name', 'N/A')} o'chirildi.",
                "success",
            )
    except Exception as e:
        app_logger.error(f"Super admin delete user db error: {str(e)}")
        flash("Foydalanuvchini o'chirishda xatolik.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/reset-staff-password", methods=["POST"])
@role_required("super_admin")
def super_admin_reset_staff_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        data = request.get_json()
        staff_id = data.get("staff_id")
        new_password = data.get("new_password")

        if not staff_id or not new_password:
            return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

        password_hash = generate_password_hash(new_password)
        execute_query(
            "UPDATE staff SET password_hash = ? WHERE id = ?", (password_hash, staff_id)
        )

        return jsonify({"success": True, "message": "Parol yangilandi"})
    except Exception as e:
        app_logger.error(f"Reset staff password error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})


@app.route("/super-admin/reset-courier-password", methods=["POST"])
@role_required("super_admin")
def super_admin_reset_courier_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        data = request.get_json()
        courier_id = data.get("courier_id")
        new_password = data.get("new_password")

        if not courier_id or not new_password:
            return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

        password_hash = generate_password_hash(new_password)
        execute_query(
            "UPDATE couriers SET password_hash = ? WHERE id = ?",
            (password_hash, courier_id),
        )

        return jsonify({"success": True, "message": "Parol yangilandi"})
    except Exception as e:
        app_logger.error(f"Reset courier password error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})


@app.route("/super-admin/reset-user-password", methods=["POST"])
@role_required("super_admin")
def super_admin_reset_user_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        data = request.get_json()
        user_id = data.get("user_id")
        new_password = data.get("new_password")

        if not user_id or not new_password:
            return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

        password_hash = generate_password_hash(new_password)
        execute_query(
            "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
        )

        return jsonify({"success": True, "message": "Parol yangilandi"})
    except Exception as e:
        app_logger.error(f"Reset user password error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})


@app.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    """Mark a specific notification as read."""
    try:
        # Use helper to get canonical type, aliases and id
        canonical_type, aliases, current_user_id = get_recipient_info_from_session()

        if not canonical_type:
            return (
                jsonify(
                    {"success": False, "message": "Foydalanuvchi tizimga kirmagan"}
                ),
                401,
            )

        # Update notification as read; try alias-aware update first
        conn = get_db()
        cur = conn.cursor()

        try:
            # Match by id and any acceptable recipient_type (including broadcasts)
            placeholders = ",".join(["?" for _ in aliases]) if aliases else ""
            if placeholders:
                sql = f"UPDATE notifications SET read_flag = 1 WHERE id = ? AND (recipient_type = 'all' OR recipient_type IN ({placeholders}) OR recipient_type = ?) AND (recipient_id = ? OR recipient_id IS NULL)"
                params = (
                    (notification_id,)
                    + tuple(aliases)
                    + (canonical_type, current_user_id)
                )
            else:
                sql = "UPDATE notifications SET read_flag = 1 WHERE id = ? AND (recipient_type = 'all' OR recipient_type = ?) AND (recipient_id = ? OR recipient_id IS NULL)"
                params = (notification_id, canonical_type, current_user_id)

            cur.execute(sql, params)
        except Exception:
            # Fallback to strict match
            cur.execute(
                """
                UPDATE notifications 
                SET read_flag = 1 
                WHERE id = ? AND recipient_type = ? AND (recipient_id = ? OR recipient_id IS NULL)
            """,
                (notification_id, canonical_type, current_user_id),
            )

        if cur.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify(
                {"success": True, "message": "Bildirishnoma o'qilgan deb belgilandi"}
            )
        else:
            conn.close()
            return (
                jsonify({"success": False, "message": "Bildirishnoma topilmadi"}),
                404,
            )

    except Exception as e:
        app_logger.error(f"Mark notification read error: {e}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"}), 500


@app.route("/api/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    """Mark all notifications as read for current user."""
    try:
        # Get current user info using helper (canonical type, aliases, id)
        canonical_type, aliases, current_user_id = get_recipient_info_from_session()

        # If not authenticated, reject
        if not canonical_type:
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        # Super admin marks everything
        if canonical_type == "super_admin":
            execute_query("UPDATE notifications SET read_flag = 1 WHERE read_flag = 0")
            return jsonify(
                {"success": True, "message": "All notifications marked read"}
            )

        # Update all notifications as read for this recipient (alias-aware)
        conn = get_db()
        cur = conn.cursor()
        try:
            placeholders = ",".join(["?" for _ in aliases]) if aliases else ""
            if placeholders:
                sql = f"UPDATE notifications SET read_flag = 1 WHERE (recipient_type = 'all' OR recipient_type IN ({placeholders}) OR recipient_type = ?) AND (recipient_id = ? OR recipient_id IS NULL) AND read_flag = 0"
                params = tuple(aliases) + (canonical_type, current_user_id)
            else:
                sql = "UPDATE notifications SET read_flag = 1 WHERE (recipient_type = 'all' OR recipient_type = ?) AND (recipient_id = ? OR recipient_id IS NULL) AND read_flag = 0"
                params = (canonical_type, current_user_id)

            cur.execute(sql, params)
        except Exception:
            cur.execute(
                "UPDATE notifications SET read_flag = 1 WHERE recipient_type = ? AND (recipient_id = ? OR recipient_id IS NULL) AND read_flag = 0",
                (canonical_type, current_user_id),
            )

        updated_count = cur.rowcount
        conn.commit()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": f"{updated_count} ta bildirishnoma o'qilgan deb belgilandi",
            }
        )

    except Exception as e:
        app_logger.error(f"Mark all notifications read error: {e}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"}), 500


@app.route("/super-admin/send-notification", methods=["POST"])
@role_required("super_admin")
def super_admin_send_notification():
    """Super admin can send notifications to users/staff/couriers or broadcast to all."""
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"}), 401

    try:
        data = request.get_json() or {}
        recipient_type = data.get(
            "recipient_type", "all"
        )  # all, users, staff, couriers
        recipient_id = data.get("recipient_id")  # optional specific id
        title = (data.get("title") or "").strip()
        body = (data.get("body") or "").strip()
        notification_type = data.get("notification_type", "admin_message")

        if not title or not body:
            return jsonify({"success": False, "message": "Sarlavha va matn kerak"}), 400

        # Validate input length
        if len(title) > 200:
            return jsonify({"success": False, "message": "Sarlavha juda uzun"}), 400
        if len(body) > 1000:
            return jsonify({"success": False, "message": "Matn juda uzun"}), 400

        # Normalize recipient_type values
        if recipient_type not in ("all", "users", "staff", "couriers"):
            if recipient_type == "courier":
                recipient_type = "couriers"
            elif recipient_type == "user":
                recipient_type = "users"
            elif recipient_type == "staff_member":
                recipient_type = "staff"
            else:
                recipient_type = "all"

        # Enhanced notification with emoji and formatting
        enhanced_title = f"📢 {title}"
        enhanced_body = f"[ADMIN] {body}"

        # If recipient_id is provided -> targeted single recipient
        if recipient_id:
            success = send_notification(
                recipient_type=recipient_type,
                recipient_id=int(recipient_id),
                title=enhanced_title,
                body=enhanced_body,
                sender_type="super_admin",
                sender_id=None,
            )

            if success:
                app_logger.info(
                    f"Super admin sent notification to {recipient_type} id={recipient_id}"
                )
                return jsonify({"success": True, "message": "Bildirishnoma yuborildi"})
            else:
                return jsonify(
                    {"success": False, "message": "Bildirishnoma yuborishda xatolik"}
                )

        # Broadcast to all users of recipient_type
        else:
            # Get all users of the specified type
            if recipient_type == "all":
                # Send to all users, staff, and couriers
                user_types = ["users", "staff", "couriers"]
            else:
                user_types = [recipient_type]

            total_sent = 0
            for user_type in user_types:
                if user_type == "users":
                    users = execute_query("SELECT id FROM users", fetch_all=True)
                elif user_type == "staff":
                    users = execute_query("SELECT id FROM staff", fetch_all=True)
                elif user_type == "couriers":
                    users = execute_query("SELECT id FROM couriers", fetch_all=True)
                else:
                    continue

                if users:
                    for user in users:
                        user_id = user["id"] if isinstance(user, dict) else user[0]
                        if send_notification(
                            recipient_type=user_type,
                            recipient_id=user_id,
                            title=enhanced_title,
                            body=enhanced_body,
                            sender_type="super_admin",
                            sender_id=None,
                        ):
                            total_sent += 1

            app_logger.info(
                f"Super admin sent broadcast notification to {recipient_type} - {total_sent} recipients"
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Bildirishnoma {total_sent} ta foydalanuvchiga yuborildi",
                }
            )

    except Exception as e:
        app_logger.error(f"Send notification error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Bildirishnoma yuborishda xatolik"}),
            500,
        )


@app.route("/api/notifications")
def api_get_notifications():
    """Get notifications for current session (user/staff/courier) or all for super_admin."""
    try:
        # If super admin, return recent notifications
        if session.get("super_admin"):
            rows = execute_query(
                "SELECT * FROM notifications ORDER BY created_at DESC LIMIT 200",
                fetch_all=True,
            )
            notes = [dict(r) for r in rows] if rows else []
            return jsonify({"success": True, "notifications": notes})

        # Determine recipient type and id from session
        # Determine recipient_type and aliases from session using helper
        canonical_type, aliases, recipient_id = get_recipient_info_from_session()

        # Not authenticated: show broadcasts only
        if not canonical_type:
            rows = execute_query(
                "SELECT * FROM notifications WHERE recipient_type = 'all' ORDER BY created_at DESC LIMIT 50",
                fetch_all=True,
            )
            notes = [dict(r) for r in rows] if rows else []
            return jsonify({"success": True, "notifications": notes})

        # Build SQL to match broadcasts OR any alias for the recipient_type where recipient_id is NULL or equals this id
        try:
            # We'll match recipient_type IN (list-of-aliases) OR recipient_type = 'all'
            placeholders = ",".join(["?" for _ in aliases])
            sql = f"SELECT * FROM notifications WHERE recipient_type = 'all' OR (recipient_type IN ({placeholders}) AND (recipient_id IS NULL OR recipient_id = ?)) ORDER BY created_at DESC LIMIT 200"
            params = tuple(aliases) + (recipient_id,)
            rows = execute_query(sql, params, fetch_all=True)
        except Exception:
            # Fallback to original strict query
            rows = execute_query(
                "SELECT * FROM notifications WHERE recipient_type = 'all' OR (recipient_type = ? AND (recipient_id IS NULL OR recipient_id = ?)) ORDER BY created_at DESC LIMIT 200",
                (canonical_type, recipient_id),
                fetch_all=True,
            )

        notes = [dict(r) for r in rows] if rows else []
        return jsonify({"success": True, "notifications": notes})
    except Exception as e:
        app_logger.error(f"Get notifications error: {str(e)}")
        return jsonify({"success": False, "notifications": []}), 500


@app.route("/super-admin/notifications")
@role_required("super_admin")
def super_admin_notifications():
    """Render the notifications management page for super admin."""
    try:
        return render_template("super_admin_notifications.html")
    except Exception as e:
        app_logger.error(f"Render notifications page error: {str(e)}")
        flash("Bildirishnomalar sahifasini yuklashda xatolik", "error")
        return redirect(url_for("super_admin_dashboard"))


@app.route("/api/notifications/mark-read", methods=["POST"])
def api_mark_notifications_read():
    """Mark notifications as read for the current recipient (or all if super_admin)."""
    try:
        # Determine recipient type and id
        if session.get("super_admin"):
            # mark all as read
            execute_query("UPDATE notifications SET read_flag = 1 WHERE read_flag = 0")
            return jsonify(
                {"success": True, "message": "All notifications marked read"}
            )
        # Use helper to resolve canonical type, aliases and current user id
        canonical_type, aliases, current_user_id = get_recipient_info_from_session()

        if not canonical_type:
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        # Mark broadcasts and notifications for this recipient (alias-aware)
        try:
            if aliases:
                placeholders = ",".join(["?" for _ in aliases])
                sql = f"UPDATE notifications SET read_flag = 1 WHERE recipient_type = 'all' OR (recipient_type IN ({placeholders}) AND (recipient_id IS NULL OR recipient_id = ?))"
                params = tuple(aliases) + (current_user_id,)
            else:
                sql = "UPDATE notifications SET read_flag = 1 WHERE recipient_type = 'all' OR (recipient_type = ? AND (recipient_id IS NULL OR recipient_id = ?))"
                params = (canonical_type, current_user_id)
            execute_query(sql, params)
        except Exception:
            # Fallback to strict
            execute_query(
                "UPDATE notifications SET read_flag = 1 WHERE recipient_type = 'all' OR (recipient_type = ? AND (recipient_id IS NULL OR recipient_id = ?))",
                (canonical_type, current_user_id),
            )
        return jsonify({"success": True, "message": "Notifications marked read"})
    except Exception as e:
        app_logger.error(f"Mark notifications read error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


def ensure_chat_tables_and_groups():
    """Create chat-related tables and default internal groups if missing."""
    try:
        # Tables with proper constraints and indexes
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_group INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS chat_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                member_type TEXT NOT NULL,
                member_id INTEGER,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
            """
        )
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                sender_id INTEGER,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
            """
        )

        # Backwards-compatibility: some older code references `chat_messages` table name.
        # Create it if missing so queries like SELECT FROM chat_messages don't fail.
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                sender_id INTEGER,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
            """
        )

        # Ensure notifications table exists as well (some code paths insert/query it)
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_type TEXT,
                recipient_id INTEGER,
                sender_type TEXT DEFAULT 'system',
                sender_id INTEGER,
                title TEXT,
                body TEXT,
                created_at TEXT,
                read_flag INTEGER DEFAULT 0,
                notification_type TEXT DEFAULT 'general'
            )
            """
        )

        # Add missing columns if they don't exist
        # Add missing columns if they don't exist (use PRAGMA to avoid duplicate ALTER)
        try:
            res = (
                execute_query("PRAGMA table_info(notifications)", fetch_all=True) or []
            )
            cols = [r[1] for r in res]
            if "sender_type" not in cols:
                execute_query(
                    "ALTER TABLE notifications ADD COLUMN sender_type TEXT DEFAULT 'system'"
                )
            if "sender_id" not in cols:
                execute_query("ALTER TABLE notifications ADD COLUMN sender_id INTEGER")
            if "notification_type" not in cols:
                execute_query(
                    "ALTER TABLE notifications ADD COLUMN notification_type TEXT DEFAULT 'general'"
                )
        except Exception:
            pass

        # Default groups: all, staffs, couriers
        now = get_current_time().isoformat()

        # Create default groups if they don't exist
        groups = [
            {
                "name": "All Team",
                "type": "all",
                "description": "Barcha xodimlar guruhi",
            },
            {"name": "Staffs", "type": "staffs", "description": "Xodimlar guruhi"},
            {
                "name": "Couriers",
                "type": "couriers",
                "description": "Yetkazib beruvchilar guruhi",
            },
        ]

        for group in groups:
            # Check if group exists
            existing = execute_query(
                "SELECT id FROM chats WHERE name = ? AND is_group = 1",
                (group["name"],),
                fetch_one=True,
            )

            if not existing:
                # Create group
                group_id = execute_query(
                    "INSERT INTO chats (name, is_group, created_at) VALUES (?, 1, ?)",
                    (group["name"], now),
                )

                if group_id:
                    # Add members based on group type
                    if group["type"] == "all":
                        # All group: add super_admin, all staff, all couriers
                        execute_query(
                            "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'super_admin', NULL)",
                            (group_id,),
                        )
                        # Add all staff members
                        staff_members = execute_query(
                            "SELECT id FROM staff", fetch_all=True
                        )
                        if staff_members:
                            for staff in staff_members:
                                execute_query(
                                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'staff', ?)",
                                    (
                                        group_id,
                                        (
                                            staff["id"]
                                            if isinstance(staff, dict)
                                            else staff[0]
                                        ),
                                    ),
                                )
                        # Add all courier members
                        courier_members = execute_query(
                            "SELECT id FROM couriers", fetch_all=True
                        )
                        if courier_members:
                            for courier in courier_members:
                                execute_query(
                                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'courier', ?)",
                                    (
                                        group_id,
                                        (
                                            courier["id"]
                                            if isinstance(courier, dict)
                                            else courier[0]
                                        ),
                                    ),
                                )

                    elif group["type"] == "staffs":
                        # Staffs group: add super_admin and all staff
                        execute_query(
                            "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'super_admin', NULL)",
                            (group_id,),
                        )
                        staff_members = execute_query(
                            "SELECT id FROM staff", fetch_all=True
                        )
                        if staff_members:
                            for staff in staff_members:
                                execute_query(
                                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'staff', ?)",
                                    (
                                        group_id,
                                        (
                                            staff["id"]
                                            if isinstance(staff, dict)
                                            else staff[0]
                                        ),
                                    ),
                                )

                    elif group["type"] == "couriers":
                        # Couriers group: add super_admin and all couriers
                        execute_query(
                            "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'super_admin', NULL)",
                            (group_id,),
                        )
                        courier_members = execute_query(
                            "SELECT id FROM couriers", fetch_all=True
                        )
                        if courier_members:
                            for courier in courier_members:
                                execute_query(
                                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, 'courier', ?)",
                                    (
                                        group_id,
                                        (
                                            courier["id"]
                                            if isinstance(courier, dict)
                                            else courier[0]
                                        ),
                                    ),
                                )

    except Exception as e:
        app_logger.error(f"Ensure chat tables/groups error: {str(e)}")


def ensure_avatar_columns():
    """Ensure avatar column exists on users, staff and couriers tables to avoid select errors."""
    try:
        for table in ("users", "staff", "couriers"):
            try:
                raw = (
                    execute_query(f"PRAGMA table_info({table});", fetch_all=True) or []
                )
                cols = []
                for c in raw:
                    try:
                        if isinstance(c, dict) and "name" in c:
                            cols.append(c["name"])
                        elif isinstance(c, (list, tuple)) and len(c) >= 2:
                            cols.append(c[1])
                    except Exception:
                        continue
                if "avatar" not in cols:
                    try:
                        execute_query(f"ALTER TABLE {table} ADD COLUMN avatar TEXT;")
                        app_logger.info(f"Added avatar column to {table}")
                    except Exception as _:
                        # best-effort: continue
                        app_logger.warning(f"Failed to add avatar column to {table}")
            except Exception:
                continue
    except Exception as e:
        app_logger.error(f"ensure_avatar_columns error: {str(e)}")


# Ensure avatar columns at startup (best-effort)
try:
    ensure_avatar_columns()
except Exception:
    pass


@app.route("/api/chats", methods=["GET", "POST"])
def api_chats():
    """GET: list chats for session; POST: create private chat with another member."""
    try:
        ensure_chat_tables_and_groups()

        if request.method == "GET":
            # Determine role and id using helper to support alias values (user/userS, courier/couriers, etc.)
            chats = []
            if session.get("super_admin"):
                rows = execute_query(
                    "SELECT * FROM chats ORDER BY id DESC", fetch_all=True
                )
                chats = [dict(r) for r in rows] if rows else []
                return jsonify({"success": True, "chats": chats})

            # Use helper which returns canonical type, aliases and id
            canonical_type, aliases, member_id = get_recipient_info_from_session()

            # Not authenticated -> no chats
            if not canonical_type:
                return jsonify({"success": True, "chats": []})

            member_type = canonical_type

            # Groups available: only groups where the requester is a member (staff/courier)
            try:
                if member_type in ("staff", "courier"):
                    if aliases:
                        placeholders = ",".join(["?" for _ in aliases])
                        sql = f"SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE c.is_group = 1 AND (m.member_type IN ({placeholders}) OR m.member_type = 'super_admin') AND (m.member_id = ? OR m.member_id IS NULL) ORDER BY c.id DESC"
                        params = tuple(aliases) + (member_id,)
                        rows = execute_query(sql, params, fetch_all=True)
                    else:
                        rows = execute_query(
                            "SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE c.is_group = 1 AND m.member_type = ? AND (m.member_id = ? OR m.member_id IS NULL) ORDER BY c.id DESC",
                            (member_type, member_id),
                            fetch_all=True,
                        )
                    chats = [dict(r) for r in rows] if rows else []
                else:
                    # For users, only private chats where they are a member
                    if aliases:
                        placeholders = ",".join(["?" for _ in aliases])
                        sql = f"SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE m.member_type IN ({placeholders}) AND m.member_id = ? ORDER BY c.id DESC"
                        params = tuple(aliases) + (member_id,)
                        rows = execute_query(sql, params, fetch_all=True)
                    else:
                        rows = execute_query(
                            "SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE m.member_type = ? AND m.member_id = ? ORDER BY c.id DESC",
                            (member_type, member_id),
                            fetch_all=True,
                        )
                    chats = [dict(r) for r in rows] if rows else []
            except Exception:
                chats = []

            # Also include private chats where they are a member (ensure no duplicates)
            try:
                if aliases:
                    placeholders = ",".join(["?" for _ in aliases])
                    sql = f"SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE c.is_group = 0 AND m.member_type IN ({placeholders}) AND m.member_id = ? ORDER BY c.id DESC"
                    params = tuple(aliases) + (member_id,)
                    private_rows = execute_query(sql, params, fetch_all=True)
                else:
                    private_rows = execute_query(
                        "SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE c.is_group = 0 AND m.member_type = ? AND m.member_id = ? ORDER BY c.id DESC",
                        (member_type, member_id),
                        fetch_all=True,
                    )
                private = [dict(r) for r in private_rows] if private_rows else []
                existing_ids = {c["id"] for c in chats}
                for p in private:
                    if p["id"] not in existing_ids:
                        chats.append(p)
            except Exception:
                pass
            if private_rows:
                private = [dict(r) for r in private_rows]
                # merge without duplicates
                existing_ids = {c["id"] for c in chats}
                for p in private:
                    if p["id"] not in existing_ids:
                        chats.append(p)

            # Enrich private chats with the other member's metadata so the frontend can show avatar/profile
            try:

                def enrich_chat(chat):
                    try:
                        is_group = chat.get("is_group")
                        # treat numeric strings as ints
                        if isinstance(is_group, str) and is_group.isdigit():
                            is_group = int(is_group)
                        if is_group:
                            return chat

                        cid = chat.get("id")
                        # load members
                        mrows = (
                            execute_query(
                                "SELECT member_type, member_id FROM chat_members WHERE chat_id = ?",
                                (cid,),
                                fetch_all=True,
                            )
                            or []
                        )
                        members = [dict(m) for m in mrows]
                        if not members:
                            return chat

                        # identify the 'other' member relative to requester if possible
                        other = None
                        requester_type = member_type
                        requester_id = member_id
                        for m in members:
                            if not (
                                str(m.get("member_type")) == str(requester_type)
                                and int(m.get("member_id") or 0)
                                == int(requester_id or 0)
                            ):
                                other = m
                                break
                        if not other:
                            # fallback: pick the first member that is not super_admin synthetic 0
                            other = members[0]

                        # normalize
                        ot = other.get("member_type")
                        oid = other.get("member_id")
                        chat["member_type"] = ot
                        chat["member_id"] = oid

                        # try to fetch display name and avatar
                        try:
                            if ot in ("users", "user"):
                                r = execute_query(
                                    "SELECT first_name, last_name, avatar FROM users WHERE id = ?",
                                    (oid,),
                                    fetch_one=True,
                                )
                            elif ot == "staff":
                                r = execute_query(
                                    "SELECT first_name, last_name, avatar FROM staff WHERE id = ?",
                                    (oid,),
                                    fetch_one=True,
                                )
                            elif ot in ("courier", "couriers"):
                                r = execute_query(
                                    "SELECT first_name, last_name, avatar FROM couriers WHERE id = ?",
                                    (oid,),
                                    fetch_one=True,
                                )
                            else:
                                r = None
                        except Exception:
                            r = None

                        if r:
                            name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            chat["display_name"] = name or None
                            chat["avatar"] = r.get("avatar") or None
                        return chat
                    except Exception:
                        return chat

                chats = [enrich_chat(c) for c in chats]
            except Exception:
                pass

            # If the user is a regular user and has no chats yet, auto-create a private chat with super_admin
            try:
                if (not chats) and member_type == "users" and member_id:
                    created_cid = add_private_chat_between("users", member_id)
                    if created_cid:
                        # fetch the newly created private chat and enrich it
                        new_row = execute_query(
                            "SELECT * FROM chats WHERE id = ?",
                            (created_cid,),
                            fetch_one=True,
                        )
                        if new_row:
                            new_chat = dict(new_row)
                            try:
                                new_chat = enrich_chat(new_chat)
                            except Exception:
                                pass
                            chats.insert(0, new_chat)
            except Exception:
                pass

            return jsonify({"success": True, "chats": chats})

        # POST -> create private chat
        if request.method == "POST":
            data = request.get_json() or {}
            target_type = data.get("member_type")
            target_id = data.get("member_id")
            name = (data.get("name") or "").strip()

            # Use helper to get canonical type and aliases and recipient id
            canonical_type, aliases, current_user_id = get_recipient_info_from_session()
            if not canonical_type:
                return (
                    jsonify(
                        {"success": False, "message": "Foydalanuvchi tizimga kirmagan"}
                    ),
                    401,
                )

            conn = get_db()
            cur = conn.cursor()

            # Determine current member type/id for chat membership
            cur_type = None
            cur_id = None
            if session.get("staff_id"):
                cur_type = "staff"
                cur_id = session.get("staff_id")
            elif session.get("courier_id"):
                cur_type = "courier"
                cur_id = session.get("courier_id")
            elif session.get("user_id"):
                cur_type = "users"
                cur_id = session.get("user_id")
            elif session.get("super_admin"):
                cur_type = "super_admin"
                cur_id = None
            else:
                return (
                    jsonify({"success": False, "message": "Authentication required"}),
                    401,
                )

            # Normalize and validate target_id
            try:
                target_id = int(target_id) if target_id is not None else None
            except Exception:
                # leave as-is if not convertible
                pass

            # Prevent duplicate private chats (one-to-one). If a private chat already
            # exists between the current member and the target, return it instead of creating.
            try:
                if target_id is not None and cur_type and cur_id is not None:
                    existing = execute_query(
                        """
                        SELECT c.id FROM chats c
                        JOIN chat_members m1 ON c.id = m1.chat_id
                        JOIN chat_members m2 ON c.id = m2.chat_id
                        WHERE c.is_group = 0
                        AND m1.member_type = ? AND (m1.member_id = ? OR (m1.member_id IS NULL AND ? IS NULL))
                        AND m2.member_type = ? AND (m2.member_id = ? OR (m2.member_id IS NULL AND ? IS NULL))
                        LIMIT 1
                        """,
                        (
                            cur_type,
                            cur_id,
                            cur_id,
                            target_type,
                            target_id,
                            target_id,
                        ),
                        fetch_one=True,
                    )
                    if existing:
                        existing_id = (
                            existing["id"]
                            if isinstance(existing, dict)
                            else existing[0]
                        )
                        return jsonify(
                            {"success": True, "chat_id": existing_id, "name": None}
                        )
            except Exception:
                # best-effort: if lookup fails, proceed to create a new chat
                pass

            # Derive a friendly chat name if not provided
            chat_name = name or None
            try:
                if not chat_name:
                    if target_type in ("users", "user"):
                        r = execute_query(
                            "SELECT first_name, last_name, email FROM users WHERE id = ?",
                            (target_id,),
                            fetch_one=True,
                        )
                        if r:
                            chat_name = (
                                f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            ) or r.get("email")
                    elif target_type in ("staff", "staffs"):
                        r = execute_query(
                            "SELECT first_name, last_name, email FROM staff WHERE id = ?",
                            (target_id,),
                            fetch_one=True,
                        )
                        if r:
                            chat_name = (
                                f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            ) or r.get("email")
                    elif target_type in ("courier", "couriers"):
                        r = execute_query(
                            "SELECT first_name, last_name, email FROM couriers WHERE id = ?",
                            (target_id,),
                            fetch_one=True,
                        )
                        if r:
                            chat_name = (
                                f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            ) or r.get("email")
            except Exception:
                chat_name = chat_name or None

            if not chat_name:
                chat_name = f"Chat_{cur_type}_{cur_id}_{target_type}_{target_id}"

            now = get_current_time().isoformat()
            chat_id = execute_query(
                "INSERT INTO chats (name, is_group, created_at) VALUES (?, 0, ?)",
                (chat_name, now),
            )
            if chat_id:
                execute_query(
                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, ?, ?)",
                    (chat_id, cur_type, cur_id),
                )
                execute_query(
                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, ?, ?)",
                    (chat_id, target_type, target_id),
                )
                return jsonify({"success": True, "chat_id": chat_id, "name": chat_name})

            return jsonify({"success": False, "message": "Could not create chat"}), 500
    except Exception as e:
        app_logger.error(f"API chats error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/api/chats/<chat_id>/messages", methods=["GET", "POST"])
def api_chat_messages(chat_id):
    """GET messages (limit param) and POST new message to chat."""
    try:
        ensure_chat_tables_and_groups()

        # auth
        if session.get("staff_id"):
            sender_type = "staff"
            sender_id = session.get("staff_id")
        elif session.get("courier_id"):
            sender_type = "courier"
            sender_id = session.get("courier_id")
        elif session.get("user_id"):
            sender_type = "users"
            sender_id = session.get("user_id")
        elif session.get("super_admin"):
            sender_type = "super_admin"
            sender_id = None
        else:
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        # Handle special group IDs (all, staffs, couriers)
        actual_chat_id = chat_id
        if chat_id in ["all", "staffs", "couriers"]:
            # Users are not allowed to post/read internal staff/courier group chats
            if sender_type == "users":
                return jsonify({"success": False, "message": "Forbidden"}), 403
            # Get the actual chat ID for the group
            group_name = {
                "all": "All Team",
                "staffs": "Staffs",
                "couriers": "Couriers",
            }.get(chat_id)

            if group_name:
                group_chat = execute_query(
                    "SELECT id FROM chats WHERE name = ? AND is_group = 1",
                    (group_name,),
                    fetch_one=True,
                )
                if group_chat:
                    actual_chat_id = (
                        group_chat["id"]
                        if isinstance(group_chat, dict)
                        else group_chat[0]
                    )
                else:
                    return (
                        jsonify({"success": False, "message": "Group not found"}),
                        404,
                    )
            else:
                return jsonify({"success": False, "message": "Invalid group"}), 400

        # Membership check: requester must be a member of the chat or super_admin
        # Make this alias-aware (e.g. 'user' vs 'users') so legacy member_type tokens don't block access
        try:
            if not session.get("super_admin"):
                try:
                    canonical_type, aliases, member_id_from_session = (
                        get_recipient_info_from_session()
                    )
                    allowed_types = aliases if aliases else [sender_type]
                except Exception:
                    allowed_types = [sender_type]

                # Build IN-clause placeholders
                placeholders = ",".join(["?" for _ in allowed_types])
                sql = f"SELECT 1 FROM chat_members WHERE chat_id = ? AND member_type IN ({placeholders}) AND (member_id = ? OR member_id IS NULL) LIMIT 1"
                params = (actual_chat_id,) + tuple(allowed_types) + (sender_id,)
                member_check = execute_query(sql, params, fetch_one=True)
                if not member_check:
                    return jsonify({"success": False, "message": "Forbidden"}), 403
        except Exception:
            return jsonify({"success": False, "message": "Forbidden"}), 403

        if request.method == "GET":
            limit = int(request.args.get("limit", 100))
            # messages are stored in the chat_messages table (legacy code used both names)
            rows = execute_query(
                "SELECT * FROM chat_messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (actual_chat_id, limit),
                fetch_all=True,
            )
            messages = [dict(r) for r in reversed(rows)] if rows else []
            # Enrich messages with sender display name and avatar when possible
            enriched = []
            for m in messages:
                msg_sender_type = m.get("sender_type")
                msg_sender_id = m.get("sender_id")
                sender_name = None
                sender_avatar = None
                try:
                    if msg_sender_type == "users" and msg_sender_id:
                        r = execute_query(
                            "SELECT first_name, last_name, avatar FROM users WHERE id = ?",
                            (msg_sender_id,),
                            fetch_one=True,
                        )
                        if r:
                            sender_name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            sender_avatar = r.get("avatar")
                    elif msg_sender_type == "staff" and msg_sender_id:
                        r = execute_query(
                            "SELECT first_name, last_name, avatar FROM staff WHERE id = ?",
                            (msg_sender_id,),
                            fetch_one=True,
                        )
                        if r:
                            sender_name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            sender_avatar = r.get("avatar")
                    elif msg_sender_type == "courier" and msg_sender_id:
                        r = execute_query(
                            "SELECT first_name, last_name, avatar FROM couriers WHERE id = ?",
                            (msg_sender_id,),
                            fetch_one=True,
                        )
                        if r:
                            sender_name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                            sender_avatar = r.get("avatar")
                    elif msg_sender_type == "super_admin":
                        sender_name = "Super Admin"
                        sender_avatar = None
                except Exception:
                    pass

                m["sender_name"] = (
                    sender_name
                    or f"{msg_sender_type or 'User'} {('#'+str(msg_sender_id)) if msg_sender_id else ''}"
                )
                m["sender_avatar"] = sender_avatar or None
                enriched.append(m)

            return jsonify({"success": True, "messages": enriched})

        # POST new message
        data = request.get_json() or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"success": False, "message": "Empty message"}), 400

        # Validate text length
        if len(text) > 1000:
            return jsonify({"success": False, "message": "Message too long"}), 400

        # Use the improved post_chat_message function
        success = post_chat_message(actual_chat_id, sender_type, sender_id, text)
        if success:
            now = get_current_time().isoformat()
            return jsonify(
                {
                    "success": True,
                    "message": "Message sent successfully",
                    "created_at": now,
                }
            )
        else:
            return jsonify({"success": False, "message": "Failed to send message"}), 500
    except Exception as e:
        app_logger.error(f"Chat messages error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/debug/chats-info")
def debug_chats_info():
    """Temporary debugging route: returns session info and chat query diagnostics."""
    try:
        # Use helper for canonical type and aliases
        canonical_type, aliases, member_id = get_recipient_info_from_session()

        resp = {
            "session_keys": {
                k: session.get(k)
                for k in ["user_id", "staff_id", "courier_id", "super_admin"]
            },
            "canonical_type": canonical_type,
            "aliases": aliases,
            "member_id": member_id,
            "chats_query_sql": None,
            "chats": [],
            "chat_members": [],
        }

        if not canonical_type:
            return jsonify(resp)

        # Build the SQL used by api_chats for diagnostics (alias-aware)
        try:
            if canonical_type in ("staff", "courier"):
                placeholders = ",".join(["?" for _ in aliases]) if aliases else ""
                if placeholders:
                    sql = f"SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE c.is_group = 1 AND (m.member_type IN ({placeholders}) OR m.member_type = 'super_admin') AND (m.member_id = ? OR m.member_id IS NULL) ORDER BY c.id DESC"
                    params = tuple(aliases) + (member_id,)
                else:
                    sql = "SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE c.is_group = 1 AND m.member_type = ? AND (m.member_id = ? OR m.member_id IS NULL) ORDER BY c.id DESC"
                    params = (canonical_type, member_id)
            else:
                placeholders = ",".join(["?" for _ in aliases]) if aliases else ""
                if placeholders:
                    sql = f"SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE m.member_type IN ({placeholders}) AND m.member_id = ? ORDER BY c.id DESC"
                    params = tuple(aliases) + (member_id,)
                else:
                    sql = "SELECT DISTINCT c.* FROM chats c JOIN chat_members m ON c.id = m.chat_id WHERE m.member_type = ? AND m.member_id = ? ORDER BY c.id DESC"
                    params = (canonical_type, member_id)

            resp["chats_query_sql"] = {"sql": sql, "params": params}
            rows = execute_query(sql, params, fetch_all=True)
            resp["chats"] = [dict(r) for r in rows] if rows else []
        except Exception as e:
            resp["chats_query_error"] = str(e)

        # Also dump matching chat_members rows for the member id for inspection
        try:
            cm_rows = execute_query(
                "SELECT chat_id, member_type, member_id FROM chat_members WHERE member_id = ? OR member_id IS NULL ORDER BY chat_id",
                (member_id,),
                fetch_all=True,
            )
            resp["chat_members"] = [dict(r) for r in cm_rows] if cm_rows else []
        except Exception as e:
            resp["chat_members_error"] = str(e)

        # Also include recent messages for the chats visible to this user (best-effort)
        try:
            resp["recent_messages"] = {}
            # collect chat ids from resp['chats']
            chat_ids = [
                c.get("id") for c in resp.get("chats", []) if c.get("id") is not None
            ]
            # also include chat_ids from chat_members rows
            for cm in resp.get("chat_members", []) or []:
                try:
                    cid = (
                        cm.get("chat_id")
                        if isinstance(cm, dict)
                        else (cm[0] if len(cm) > 0 else None)
                    )
                    if cid and cid not in chat_ids:
                        chat_ids.append(cid)
                except Exception:
                    continue

            for cid in chat_ids:
                try:
                    rows = (
                        execute_query(
                            "SELECT id, chat_id, sender_type, sender_id, text, created_at FROM chat_messages WHERE chat_id = ? ORDER BY id DESC LIMIT 50",
                            (cid,),
                            fetch_all=True,
                        )
                        or []
                    )
                    # return reversed (oldest first)
                    msgs = [dict(r) for r in reversed(rows)] if rows else []
                    resp["recent_messages"][str(cid)] = msgs
                except Exception as e:
                    resp.setdefault("recent_messages_errors", {})[str(cid)] = str(e)
        except Exception as e:
            resp["recent_messages_error"] = str(e)

        # Best-effort: include a sample of the last posted message body if available in a temporary table or last log entry
        try:
            # If a helper table "chat_capture" exists (created by debug runs), fetch its last row
            has_capture = execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_capture'",
                fetch_one=True,
            )
            if has_capture:
                cap = execute_query(
                    "SELECT id, chat_id, posted_by, payload, created_at FROM chat_capture ORDER BY id DESC LIMIT 1",
                    fetch_one=True,
                )
                if cap:
                    resp["last_posted_sample"] = dict(cap)
        except Exception:
            # ignore capture errors
            pass

        # Also include distinct member_type and recipient_type values for diagnostics
        try:
            dm = (
                execute_query(
                    "SELECT DISTINCT member_type FROM chat_members", fetch_all=True
                )
                or []
            )
            resp["distinct_member_types"] = [
                r[0] if not isinstance(r, dict) else next(iter(r.values())) for r in dm
            ]
        except Exception as e:
            resp["distinct_member_types_error"] = str(e)

        try:
            dr = (
                execute_query(
                    "SELECT DISTINCT recipient_type FROM notifications", fetch_all=True
                )
                or []
            )
            resp["distinct_recipient_types"] = [
                r[0] if not isinstance(r, dict) else next(iter(r.values())) for r in dr
            ]
        except Exception as e:
            resp["distinct_recipient_types_error"] = str(e)

        return jsonify(resp)
    except Exception as e:
        app_logger.error(f"debug_chats_info error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/debug/notifications-info")
def debug_notifications_info():
    """Temporary diagnostics: returns notifications visible to the current session and distinct recipient_type values."""
    try:
        canonical_type, aliases, recipient_id = get_recipient_info_from_session()
        resp = {
            "session_keys": {
                k: session.get(k)
                for k in ["user_id", "staff_id", "courier_id", "super_admin"]
            },
            "canonical_type": canonical_type,
            "aliases": aliases,
            "recipient_id": recipient_id,
            "notifications_query_sql": None,
            "notifications": [],
            "distinct_recipient_types": [],
            "unread_count": 0,
        }

        # Build the notifications SQL (same as api_get_notifications)
        if not canonical_type:
            rows = execute_query(
                "SELECT * FROM notifications WHERE recipient_type = 'all' ORDER BY created_at DESC LIMIT 50",
                fetch_all=True,
            )
            resp["notifications"] = [dict(r) for r in rows] if rows else []
        else:
            try:
                placeholders = ",".join(["?" for _ in aliases])
                sql = f"SELECT * FROM notifications WHERE recipient_type = 'all' OR (recipient_type IN ({placeholders}) AND (recipient_id IS NULL OR recipient_id = ?)) ORDER BY created_at DESC LIMIT 200"
                params = tuple(aliases) + (recipient_id,)
                resp["notifications_query_sql"] = {"sql": sql, "params": params}
                rows = execute_query(sql, params, fetch_all=True)
                resp["notifications"] = [dict(r) for r in rows] if rows else []
            except Exception:
                sql = "SELECT * FROM notifications WHERE recipient_type = 'all' OR (recipient_type = ? AND (recipient_id IS NULL OR recipient_id = ?)) ORDER BY created_at DESC LIMIT 200"
                params = (canonical_type, recipient_id)
                resp["notifications_query_sql"] = {"sql": sql, "params": params}
                rows = execute_query(sql, params, fetch_all=True)
                resp["notifications"] = [dict(r) for r in rows] if rows else []

        # distinct recipient_type values
        try:
            dr = (
                execute_query(
                    "SELECT DISTINCT recipient_type FROM notifications", fetch_all=True
                )
                or []
            )
            resp["distinct_recipient_types"] = [
                r[0] if not isinstance(r, dict) else next(iter(r.values())) for r in dr
            ]
        except Exception as e:
            resp["distinct_recipient_types_error"] = str(e)

        # unread count
        try:
            unread = 0
            for n in resp["notifications"]:
                if n.get("read_flag") in (0, "0", None):
                    unread += 1
            resp["unread_count"] = unread
        except Exception:
            resp["unread_count_error"] = "count_error"

        return jsonify(resp)
    except Exception as e:
        app_logger.error(f"debug_notifications_info error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        app_logger.error(f"Chat messages error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/api/private-chats", methods=["GET"])
def api_private_chats():
    """Get available private chats for the current user."""
    try:
        ensure_chat_tables_and_groups()

        # Get current user info
        if session.get("staff_id"):
            user_type = "staff"
            user_id = session.get("staff_id")
        elif session.get("courier_id"):
            user_type = "courier"
            user_id = session.get("courier_id")
        elif session.get("super_admin"):
            user_type = "super_admin"
            user_id = None
        elif session.get("user_id"):
            # Allow regular authenticated users (buyers) to access private chat targets
            user_type = "user"
            user_id = session.get("user_id")
        else:
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        # Get all other users for private chats
        private_chats = []

        if user_type == "staff":
            # Staff can chat with other staff and couriers
            # Get other staff
            other_staff = execute_query(
                "SELECT id, first_name, last_name, avatar FROM staff WHERE id != ?",
                (user_id,),
                fetch_all=True,
            )
            if other_staff:
                for staff in other_staff:
                    private_chats.append(
                        {
                            "id": f"staff_{staff['id'] if isinstance(staff, dict) else staff[0]}",
                            "name": f"{staff.get('first_name', '') if isinstance(staff, dict) else staff[1]} {staff.get('last_name', '') if isinstance(staff, dict) else staff[2]}".strip(),
                            "avatar": (
                                staff.get("avatar")
                                if isinstance(staff, dict)
                                else staff[3]
                            ),
                            "type": "staff",
                            "user_id": (
                                staff["id"] if isinstance(staff, dict) else staff[0]
                            ),
                        }
                    )

            # Get couriers
            couriers = execute_query(
                "SELECT id, first_name, last_name, avatar FROM couriers", fetch_all=True
            )
            if couriers:
                for courier in couriers:
                    private_chats.append(
                        {
                            "id": f"courier_{courier['id'] if isinstance(courier, dict) else courier[0]}",
                            "name": f"{courier.get('first_name', '') if isinstance(courier, dict) else courier[1]} {courier.get('last_name', '') if isinstance(courier, dict) else courier[2]}".strip(),
                            "avatar": (
                                courier.get("avatar")
                                if isinstance(courier, dict)
                                else courier[3]
                            ),
                            "type": "courier",
                            "user_id": (
                                courier["id"]
                                if isinstance(courier, dict)
                                else courier[0]
                            ),
                        }
                    )

        elif user_type == "courier":
            # Couriers can chat with staff and other couriers
            # Get staff
            staff = execute_query(
                "SELECT id, first_name, last_name, avatar FROM staff", fetch_all=True
            )
            if staff:
                for s in staff:
                    private_chats.append(
                        {
                            "id": f"staff_{s['id'] if isinstance(s, dict) else s[0]}",
                            "name": f"{s.get('first_name', '') if isinstance(s, dict) else s[1]} {s.get('last_name', '') if isinstance(s, dict) else s[2]}".strip(),
                            "avatar": s.get("avatar") if isinstance(s, dict) else s[3],
                            "type": "staff",
                            "user_id": s["id"] if isinstance(s, dict) else s[0],
                        }
                    )

            # Get other couriers
            other_couriers = execute_query(
                "SELECT id, first_name, last_name, avatar FROM couriers WHERE id != ?",
                (user_id,),
                fetch_all=True,
            )
            if other_couriers:
                for courier in other_couriers:
                    private_chats.append(
                        {
                            "id": f"courier_{courier['id'] if isinstance(courier, dict) else courier[0]}",
                            "name": f"{courier.get('first_name', '') if isinstance(courier, dict) else courier[1]} {courier.get('last_name', '') if isinstance(courier, dict) else courier[2]}".strip(),
                            "avatar": (
                                courier.get("avatar")
                                if isinstance(courier, dict)
                                else courier[3]
                            ),
                            "type": "courier",
                            "user_id": (
                                courier["id"]
                                if isinstance(courier, dict)
                                else courier[0]
                            ),
                        }
                    )

        elif user_type == "super_admin":
            # Super admin can chat with everyone
            # Get all staff
            staff = execute_query(
                "SELECT id, first_name, last_name, avatar FROM staff", fetch_all=True
            )
            if staff:
                for s in staff:
                    private_chats.append(
                        {
                            "id": f"staff_{s['id'] if isinstance(s, dict) else s[0]}",
                            "name": f"{s.get('first_name', '') if isinstance(s, dict) else s[1]} {s.get('last_name', '') if isinstance(s, dict) else s[2]}".strip(),
                            "avatar": s.get("avatar") if isinstance(s, dict) else s[3],
                            "type": "staff",
                            "user_id": s["id"] if isinstance(s, dict) else s[0],
                        }
                    )

            # Get all couriers
            couriers = execute_query(
                "SELECT id, first_name, last_name, avatar FROM couriers", fetch_all=True
            )
            if couriers:
                for courier in couriers:
                    private_chats.append(
                        {
                            "id": f"courier_{courier['id'] if isinstance(courier, dict) else courier[0]}",
                            "name": f"{courier.get('first_name', '') if isinstance(courier, dict) else courier[1]} {courier.get('last_name', '') if isinstance(courier, dict) else courier[2]}".strip(),
                            "avatar": (
                                courier.get("avatar")
                                if isinstance(courier, dict)
                                else courier[3]
                            ),
                            "type": "courier",
                            "user_id": (
                                courier["id"]
                                if isinstance(courier, dict)
                                else courier[0]
                            ),
                        }
                    )

            elif user_type == "user":
                # Regular users can start private chats with staff and couriers
                staff = execute_query(
                    "SELECT id, first_name, last_name, avatar FROM staff",
                    fetch_all=True,
                )
                if staff:
                    for s in staff:
                        private_chats.append(
                            {
                                "id": f"staff_{s['id'] if isinstance(s, dict) else s[0]}",
                                "name": f"{s.get('first_name', '') if isinstance(s, dict) else s[1]} {s.get('last_name', '') if isinstance(s, dict) else s[2]}".strip(),
                                "avatar": (
                                    s.get("avatar") if isinstance(s, dict) else s[3]
                                ),
                                "type": "staff",
                                "user_id": s["id"] if isinstance(s, dict) else s[0],
                            }
                        )

                couriers = execute_query(
                    "SELECT id, first_name, last_name, avatar FROM couriers",
                    fetch_all=True,
                )
                if couriers:
                    for courier in couriers:
                        private_chats.append(
                            {
                                "id": f"courier_{courier['id'] if isinstance(courier, dict) else courier[0]}",
                                "name": f"{courier.get('first_name', '') if isinstance(courier, dict) else courier[1]} {courier.get('last_name', '') if isinstance(courier, dict) else courier[2]}".strip(),
                                "avatar": (
                                    courier.get("avatar")
                                    if isinstance(courier, dict)
                                    else courier[3]
                                ),
                                "type": "courier",
                                "user_id": (
                                    courier["id"]
                                    if isinstance(courier, dict)
                                    else courier[0]
                                ),
                            }
                        )

        return jsonify({"success": True, "private_chats": private_chats})

    except Exception as e:
        app_logger.error(f"Private chats error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/api/private-chat/<user_type>/<int:user_id>", methods=["GET", "POST"])
def api_private_chat(user_type, user_id):
    """Create or get private chat between current user and specified user."""
    try:
        ensure_chat_tables_and_groups()

        # Get current user info
        if session.get("staff_id"):
            current_user_type = "staff"
            current_user_id = session.get("staff_id")
        elif session.get("courier_id"):
            current_user_type = "courier"
            current_user_id = session.get("courier_id")
        elif session.get("super_admin"):
            current_user_type = "super_admin"
            current_user_id = None
        else:
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        # Validate target user exists
        if user_type == "staff":
            target_user = execute_query(
                "SELECT id, first_name, last_name, avatar FROM staff WHERE id = ?",
                (user_id,),
                fetch_one=True,
            )
        elif user_type == "courier":
            target_user = execute_query(
                "SELECT id, first_name, last_name, avatar FROM couriers WHERE id = ?",
                (user_id,),
                fetch_one=True,
            )
        else:
            return jsonify({"success": False, "message": "Invalid user type"}), 400

        if not target_user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Create chat name
        target_name = f"{target_user.get('first_name', '') if isinstance(target_user, dict) else target_user[1]} {target_user.get('last_name', '') if isinstance(target_user, dict) else target_user[2]}".strip()
        chat_name = f"Private chat with {target_name}"

        # Check if private chat already exists
        existing_chat = execute_query(
            """
            SELECT c.id FROM chats c 
            JOIN chat_members m1 ON c.id = m1.chat_id 
            JOIN chat_members m2 ON c.id = m2.chat_id 
            WHERE c.is_group = 0 
            AND m1.member_type = ? AND m1.member_id = ? 
            AND m2.member_type = ? AND m2.member_id = ?
            """,
            (current_user_type, current_user_id, user_type, user_id),
            fetch_one=True,
        )

        if existing_chat:
            chat_id = (
                existing_chat["id"]
                if isinstance(existing_chat, dict)
                else existing_chat[0]
            )
        else:
            # Create new private chat
            now = get_current_time().isoformat()
            chat_id = execute_query(
                "INSERT INTO chats (name, is_group, created_at) VALUES (?, 0, ?)",
                (chat_name, now),
            )

            if chat_id:
                # Add both users to the chat
                execute_query(
                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, ?, ?)",
                    (chat_id, current_user_type, current_user_id),
                )
                execute_query(
                    "INSERT INTO chat_members (chat_id, member_type, member_id) VALUES (?, ?, ?)",
                    (chat_id, user_type, user_id),
                )

        if request.method == "GET":
            return jsonify(
                {
                    "success": True,
                    "chat_id": chat_id,
                    "chat_name": chat_name,
                    "target_user": {
                        "name": target_name,
                        "avatar": (
                            target_user.get("avatar")
                            if isinstance(target_user, dict)
                            else target_user[3]
                        ),
                        "type": user_type,
                        "id": user_id,
                    },
                }
            )

        # POST - send message to private chat
        data = request.get_json() or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"success": False, "message": "Empty message"})

        now = get_current_time().isoformat()
        msg_id = execute_query(
            "INSERT INTO messages (chat_id, sender_type, sender_id, text, created_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, current_user_type, current_user_id, text, now),
        )

        if msg_id:
            return jsonify({"success": True, "message_id": msg_id, "created_at": now})
        return jsonify({"success": False, "message": "Failed to send"}), 500

    except Exception as e:
        app_logger.error(f"Private chat error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/api/chat-unread-count")
def api_chat_unread_count():
    """Return unread chat count for current session user (used by frontend badge)."""
    try:
        # Ensure chat-related tables exist to avoid 'no such table' runtime errors
        try:
            ensure_chat_tables_and_groups()
        except Exception:
            pass

        current = _current_user_context()
        # guests get zero
        if current.get("type") == "guest":
            return jsonify({"success": True, "count": 0})

        count = get_unread_chat_count_for_user(current)
        return jsonify({"success": True, "count": int(count)})
    except Exception as e:
        try:
            app_logger.error(f"api_chat_unread_count error: {str(e)}")
        except:
            pass
        return jsonify({"success": False, "count": 0}), 500


@app.route("/api/internal-members")
def api_internal_members():
    """Return staff, couriers and superadmin as selectable members for the internal chat."""
    try:
        members = []
        # Super admin synthetic entry
        members.append(
            {"member_type": "super_admin", "member_id": 0, "name": "Super Admin"}
        )

        # Staff
        try:
            staff_rows = execute_query(
                "SELECT id, first_name, last_name FROM staff ORDER BY first_name",
                fetch_all=True,
            )
            if staff_rows:
                for r in staff_rows:
                    name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                    members.append(
                        {
                            "member_type": "staff",
                            "member_id": r.get("id"),
                            "name": name or f"Staff #{r.get('id')}",
                            "avatar": r.get("avatar") if r.get("avatar") else None,
                        }
                    )
        except Exception:
            pass

        # Couriers
        try:
            courier_rows = execute_query(
                "SELECT id, first_name, last_name FROM couriers ORDER BY first_name",
                fetch_all=True,
            )
            if courier_rows:
                for r in courier_rows:
                    name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                    members.append(
                        {
                            "member_type": "courier",
                            "member_id": r.get("id"),
                            "name": name or f"Courier #{r.get('id')}",
                            "avatar": r.get("avatar") if r.get("avatar") else None,
                        }
                    )
        except Exception:
            pass

        return jsonify({"success": True, "members": members})
    except Exception as e:
        app_logger.error(f"Internal members error: {str(e)}")
        return jsonify({"success": False, "members": []}), 500


@app.route("/api/members")
def api_members():
    """Return lists of users, staff and couriers for selection in admin UIs."""
    try:
        users_list = []
        staff_list = []
        couriers_list = []

        try:
            users_rows = (
                execute_query(
                    "SELECT id, first_name, last_name, email, avatar FROM users ORDER BY created_at DESC LIMIT 500",
                    fetch_all=True,
                )
                or []
            )
            for r in users_rows:
                name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip() or (
                    r.get("email") or f"User #{r.get('id')}"
                )
                users_list.append(
                    {
                        "member_type": "users",
                        "member_id": r.get("id"),
                        "name": name,
                        "username": r.get("email") or None,
                        "avatar": r.get("avatar") if r.get("avatar") else None,
                    }
                )
        except Exception:
            pass

        try:
            staff_rows = (
                execute_query(
                    "SELECT id, first_name, last_name, avatar FROM staff ORDER BY first_name LIMIT 500",
                    fetch_all=True,
                )
                or []
            )
            for r in staff_rows:
                name = (
                    f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                    or f"Staff #{r.get('id')}"
                )
                staff_list.append(
                    {
                        "member_type": "staff",
                        "member_id": r.get("id"),
                        "name": name,
                        "username": r.get("email") if r.get("email") else None,
                        "avatar": r.get("avatar") if r.get("avatar") else None,
                    }
                )
        except Exception:
            pass

        try:
            courier_rows = (
                execute_query(
                    "SELECT id, first_name, last_name, avatar FROM couriers ORDER BY first_name LIMIT 500",
                    fetch_all=True,
                )
                or []
            )
            for r in courier_rows:
                name = (
                    f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
                    or f"Courier #{r.get('id')}"
                )
                couriers_list.append(
                    {
                        "member_type": "courier",
                        "member_id": r.get("id"),
                        "name": name,
                        "username": r.get("email") if r.get("email") else None,
                        "avatar": r.get("avatar") if r.get("avatar") else None,
                    }
                )
        except Exception:
            pass

        return jsonify(
            {
                "success": True,
                "users": users_list,
                "staff": staff_list,
                "couriers": couriers_list,
            }
        )
    except Exception as e:
        app_logger.error(f"API members error: {str(e)}")
        return (
            jsonify({"success": False, "users": [], "staff": [], "couriers": []}),
            500,
        )


@app.route("/api/member/<member_type>/<int:member_id>")
def api_member_profile(member_type, member_id):
    """Return basic profile info for a member used by avatar popups.
    member_type: users | staff | courier(s)
    """
    # Require authentication
    try:
        if not (
            session.get("user_id")
            or session.get("staff_id")
            or session.get("courier_id")
            or session.get("super_admin")
        ):
            return (
                jsonify({"success": False, "message": "Authentication required"}),
                401,
            )

        # Access control: regular users can only view their own profile
        requester_is_super = bool(session.get("super_admin"))
        requester_is_staff = bool(session.get("staff_id"))
        requester_is_courier = bool(session.get("courier_id"))
        requester_is_user = bool(session.get("user_id"))

        # If requester is a regular user, enforce same-id and users type only
        if requester_is_user and not (
            requester_is_staff or requester_is_courier or requester_is_super
        ):
            if not (
                member_type in ("users", "user")
                and int(member_id) == int(session.get("user_id"))
            ):
                return jsonify({"success": False, "message": "Forbidden"}), 403

        # Normalize member_type
        mt = member_type
        if mt == "user":
            mt = "users"
        if mt == "courier":
            mt = "couriers"

        if mt == "users":
            r = execute_query(
                "SELECT id, first_name, last_name, email AS username, phone, birth_date, avatar FROM users WHERE id = ?",
                (member_id,),
                fetch_one=True,
            )
        elif mt == "staff":
            r = execute_query(
                "SELECT id, first_name, last_name, email AS username, phone, birth_date, avatar FROM staff WHERE id = ?",
                (member_id,),
                fetch_one=True,
            )
        elif mt == "couriers":
            r = execute_query(
                "SELECT id, first_name, last_name, email AS username, phone, birth_date, avatar FROM couriers WHERE id = ?",
                (member_id,),
                fetch_one=True,
            )
        else:
            return jsonify({"success": False, "message": "Unknown member type"}), 400

        if not r:
            return jsonify({"success": False, "message": "Not found"}), 404

        name = f"{r.get('first_name','') or ''} {r.get('last_name','') or ''}".strip()
        result = {
            "id": r.get("id"),
            "name": name or None,
            "username": r.get("username") or None,
            "phone": r.get("phone") or None,
            "birth_date": r.get("birth_date") or None,
            "avatar": r.get("avatar") or None,
            "role": mt,
        }
        return jsonify({"success": True, "profile": result})
    except Exception as e:
        app_logger.error(f"API member profile error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/api/send-notification", methods=["POST"])
def api_send_notification():
    """Deprecated: only super-admin or system may write notifications.
    To send a notification use /super-admin/send-notification (requires super_admin role).
    This endpoint will now reject non-superadmin attempts to create notifications.
    """
    # Explicitly forbid non-superadmin writes through this endpoint to enforce policy.
    if not session.get("super_admin"):
        return (
            jsonify(
                {"success": False, "message": "Only super admin can send notifications"}
            ),
            403,
        )

    # If super_admin, proxy to the dedicated implementation for consistency
    try:
        data = request.get_json() or {}
        recipient_type = data.get("recipient_type", "all")
        recipient_id = data.get("recipient_id")
        title = (data.get("title") or "").strip()
        body = (data.get("body") or "").strip()

        if not title or not body:
            return jsonify({"success": False, "message": "Title and body required"})

        if not recipient_id:
            return jsonify({"success": False, "message": "recipient_id required"}), 400

        # Ensure notifications table exists
        try:
            execute_query(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_type TEXT,
                    recipient_id INTEGER,
                    sender_type TEXT DEFAULT 'system',
                    sender_id INTEGER,
                    title TEXT,
                    body TEXT,
                    created_at TEXT,
                    read_flag INTEGER DEFAULT 0,
                    notification_type TEXT DEFAULT 'general'
                )
                """
            )

            # Add missing columns if they don't exist
            # Add missing columns if they don't exist (use PRAGMA)
            res = (
                execute_query("PRAGMA table_info(notifications)", fetch_all=True) or []
            )
            cols = [r[1] for r in res]
            if "sender_type" not in cols:
                execute_query(
                    "ALTER TABLE notifications ADD COLUMN sender_type TEXT DEFAULT 'system'"
                )
            if "notification_type" not in cols:
                execute_query(
                    "ALTER TABLE notifications ADD COLUMN notification_type TEXT DEFAULT 'general'"
                )
        except Exception as table_err:
            app_logger.error(
                f"Create notifications table error (send): {str(table_err)}"
            )

        now = get_current_time().isoformat()
        execute_query(
            "INSERT INTO notifications (recipient_type, recipient_id, sender_id, title, body, created_at, read_flag) VALUES (?, ?, ?, ?, ?, ?, 0)",
            (recipient_type, recipient_id, None, title, body, now),
        )

        return jsonify({"success": True, "message": "Bildirishnoma yuborildi"})
    except Exception as e:
        app_logger.error(f"API send-notification error: {str(e)}")
        return jsonify({"success": False, "message": "Server error"}), 500


@app.route("/super-admin/get-logs", methods=["POST"])
@role_required("super_admin")
def super_admin_get_logs():
    "Super admin logs API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        data = request.get_json() or {}
        level = data.get("level", "all")
        date = data.get("date", "")

        logs = []

        # Restaurant log faylini o'qish
        try:
            # Try utf-8 first, then fall back to latin-1 or binary with replacement to avoid decode errors
            lines = []
            try:
                with open("logs/restaurant.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()[-100:]
            except UnicodeDecodeError:
                try:
                    with open("logs/restaurant.log", "r", encoding="latin-1") as f:
                        lines = f.readlines()[-100:]
                except Exception:
                    # Last resort: read binary and replace undecodable bytes
                    with open("logs/restaurant.log", "rb") as f:
                        raw = f.read()
                        text = raw.decode("utf-8", errors="replace")
                        lines = text.splitlines()[-100:]

            # Parse lines (run regardless of which encoding branch succeeded)
            for line in lines:
                if line.strip():
                    # Log formatini parse qilish
                    parts = line.strip().split(" | ")
                    if len(parts) >= 4:
                        log_time = parts[0]
                        log_level = parts[1]
                        log_source = parts[2]
                        log_message = " | ".join(parts[3:])

                        # Level filter
                        if level != "all" and log_level != level:
                            continue

                        # Date filter
                        if date and not log_time.startswith(date):
                            continue

                        logs.append(
                            {
                                "time": log_time,
                                "level": log_level,
                                "source": log_source,
                                "message": log_message,
                            }
                        )
        except FileNotFoundError:
            # Fallback ma'lumotlar
            logs = [
                {
                    "time": get_current_time().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "INFO",
                    "source": "app.py",
                    "message": "Log fayli topilmadi, mock ma'lumotlar ko'rsatilmoqda",
                }
            ]
        except Exception as e:
            app_logger.error(f"Log faylini o'qishda xatolik: {str(e)}")
            logs = [
                {
                    "time": get_current_time().strftime("%Y-%m-%d %H:%M:%S"),
                    "level": "ERROR",
                    "source": "logging.py",
                    "message": f"Log faylini o'qishda xatolik: {str(e)}",
                }
            ]

        return jsonify({"success": True, "logs": logs})

    except Exception as e:
        app_logger.error(f"Get logs API error: {str(e)}")
        return jsonify({"success": False, "message": "Loglarni yuklashda xatolik"})


@app.route("/super-admin/get-performance-stats")
@role_required("super_admin")
def super_admin_get_performance_stats():
    "Super admin performance stats API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        import psutil
        import time

        # CPU va Memory ma'lumotlari
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Performance monitor dan ma'lumotlar
        perf_stats = (
            performance_monitor.get_stats()
            if hasattr(performance_monitor, "get_stats")
            else {}
        )

        # Active sessions - database'dan hisoblash
        active_sessions = 0
        try:
            # Session'lar sonini taxminiy hisoblash
            result = execute_query(
                "SELECT COUNT(DISTINCT user_id) FROM orders WHERE created_at > datetime('now', '-1 hour')",
                fetch_one=True,
            )
            active_sessions = result[0] if result else 0
        except:
            active_sessions = 5  # Fallback

        stats = {
            "responseTime": int(perf_stats.get("avg_response_time", 0.25) * 1000),  # ms
            "memoryUsage": int(memory.percent),
            "activeSessions": active_sessions,
            "errorRate": (
                round(
                    performance_monitor.error_count
                    / max(
                        1,
                        performance_monitor.success_count
                        + performance_monitor.error_count,
                    )
                    * 100,
                    1,
                )
                if hasattr(performance_monitor, "error_count")
                else 0.5
            ),
        }

        return jsonify({"success": True, "stats": stats})

    except ImportError:
        # psutil mavjud bo'lmasa, mock data
        stats = {
            "responseTime": 250,
            "memoryUsage": 45,
            "activeSessions": 12,
            "errorRate": 0.8,
        }
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        app_logger.error(f"Performance stats error: {str(e)}")
        return jsonify(
            {"success": False, "message": "Performance ma'lumotlarini olishda xatolik"}
        )


@app.route("/super-admin/get-errors-summary")
@role_required("super_admin")
def super_admin_get_errors_summary():
    "Super admin errors summary API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        errors = []

        # Error log faylini o'qish
        try:
            lines = []
            try:
                with open("logs/errors.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()[-50:]
            except UnicodeDecodeError:
                try:
                    with open("logs/errors.log", "r", encoding="latin-1") as f:
                        lines = f.readlines()[-50:]
                except Exception:
                    with open("logs/errors.log", "rb") as f:
                        raw = f.read()
                        text = raw.decode("utf-8", errors="replace")
                        lines = text.splitlines()[-50:]

            # Now parse the lines to build error counts
            error_counts = {}
            for line in lines:
                if line.strip():
                    # Error message'ni parse qilish
                    parts = line.strip().split(" - ")
                    if len(parts) >= 2:
                        time_part = parts[0]
                        message_part = " - ".join(parts[1:])

                        # Error message'ni kalta qilish
                        if len(message_part) > 80:
                            message_part = message_part[:77] + "..."

                        if message_part in error_counts:
                            error_counts[message_part]["count"] += 1
                        else:
                            error_counts[message_part] = {
                                "time": (
                                    time_part.split(" ")[1]
                                    if " " in time_part
                                    else time_part[-8:]
                                ),
                                "message": message_part,
                                "count": 1,
                            }

            # Top 10 error
            sorted_errors = sorted(
                error_counts.values(), key=lambda x: x["count"], reverse=True
            )[:10]
            errors = sorted_errors

        except FileNotFoundError:
            errors = []
        except Exception as e:
            app_logger.error(f"Error summary parse error: {str(e)}")
            errors = []

        return jsonify({"success": True, "errors": errors})

    except Exception as e:
        app_logger.error(f"Errors summary API error: {str(e)}")
        return jsonify(
            {"success": False, "message": "Xatoliklar ma'lumotini olishda xatolik"}
        )


@app.route("/super-admin/download-logs")
@role_required("super_admin")
def super_admin_download_logs():
    "Super admin logs download"
    if not session.get("super_admin"):
        return "Super admin huquqi kerak", 401

    try:
        level = request.args.get("level", "all")
        date = request.args.get("date", "")

        # Log fayllarini birlashtirish
        all_logs = []

        # Restaurant logs
        try:
            try:
                with open("logs/restaurant.log", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            all_logs.append(line.strip())
            except UnicodeDecodeError:
                try:
                    with open("logs/restaurant.log", "r", encoding="latin-1") as f:
                        for line in f:
                            if line.strip():
                                all_logs.append(line.strip())
                except Exception:
                    with open("logs/restaurant.log", "rb") as f:
                        raw = f.read()
                        text = raw.decode("utf-8", errors="replace")
                        for line in text.splitlines():
                            if line.strip():
                                all_logs.append(line.strip())
        except FileNotFoundError:
            pass

        # Error logs
        try:
            try:
                with open("logs/errors.log", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            all_logs.append(f"ERROR: {line.strip()}")
            except UnicodeDecodeError:
                try:
                    with open("logs/errors.log", "r", encoding="latin-1") as f:
                        for line in f:
                            if line.strip():
                                all_logs.append(f"ERROR: {line.strip()}")
                except Exception:
                    with open("logs/errors.log", "rb") as f:
                        raw = f.read()
                        text = raw.decode("utf-8", errors="replace")
                        for line in text.splitlines():
                            if line.strip():
                                all_logs.append(f"ERROR: {line.strip()}")
        except FileNotFoundError:
            pass

        # Filter
        filtered_logs = []
        for log in all_logs:
            if level != "all" and level not in log:
                continue
            if date and not log.startswith(date):
                continue
            filtered_logs.append(log)

        # Response yaratish
        log_content = "\n".join(filtered_logs)

        from flask import Response

        response = Response(
            log_content,
            mimetype="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename=restaurant_logs_{date or "all"}_{level}.txt'
            },
        )

        return response

    except Exception as e:
        app_logger.error(f"Download logs error: {str(e)}")
        return f"Loglarni yuklab olishda xatolik: {str(e)}", 500


@app.route("/super-admin/get-system-stats")
@role_required("super_admin")
def super_admin_get_system_stats():
    "Super admin system stats API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        import psutil
        import os

        # System stats
        uptime_seconds = time.time() - start_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)

        # Memory va CPU
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)

        # Database size
        db_size = 0
        try:
            db_size = os.path.getsize(DB_PATH) / (1024 * 1024)  # MB
        except:
            pass

        # Database counts
        total_orders = (
            execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)[0] or 0
        )
        total_users = (
            execute_query("SELECT COUNT(*) FROM users", fetch_one=True)[0] or 0
        )

        # Performance stats
        perf_stats = (
            performance_monitor.get_stats()
            if hasattr(performance_monitor, "get_stats")
            else {}
        )

        stats = {
            "uptime": f"{uptime_days} kun {uptime_hours} soat",
            "memory": f"{int(memory.percent)}%",
            "cpu": f"{int(cpu_percent)}%",
            "dbSize": f"{db_size:.1f} MB",
            "totalOrders": f"{total_orders:,}",
            "totalUsers": f"{total_users:,}",
            "requestsPerMin": f"{perf_stats.get('total_requests', 0) // 60}",
            "errorRate": (
                f"{(performance_monitor.error_count / max(1, performance_monitor.success_count + performance_monitor.error_count) * 100):.1f}%"
                if hasattr(performance_monitor, "error_count")
                else "0.5%"
            ),
            "avgResponse": f"{int(perf_stats.get('avg_response_time', 0.25) * 1000)}ms",
        }

        return jsonify({"success": True, "stats": stats})

    except ImportError:
        # psutil mavjud bo'lmasa fallback
        stats = {
            "uptime": "2 kun 14 soat",
            "memory": "45%",
            "cpu": "23%",
            "dbSize": "15.7 MB",
            "totalOrders": "1,234",
            "totalUsers": "567",
            "requestsPerMin": "12",
            "errorRate": "0.8%",
            "avgResponse": "250ms",
        }
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        app_logger.error(f"System stats error: {str(e)}")
        return jsonify({"success": False, "message": "System stats olishda xatolik"})


@app.route("/super-admin/get-system-logs")
@role_required("super_admin")
def super_admin_get_system_logs():
    "Super admin system logs API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        logs = []
        current_time = get_current_time()

        # Recent system activities
        logs.append(
            {
                "time": current_time.strftime("%H:%M:%S"),
                "message": "System running normally",
            }
        )

        logs.append(
            {
                "time": (current_time - datetime.timedelta(minutes=5)).strftime(
                    "%H:%M:%S"
                ),
                "message": "Database cleanup completed",
            }
        )

        logs.append(
            {
                "time": (current_time - datetime.timedelta(minutes=10)).strftime(
                    "%H:%M:%S"
                ),
                "message": "Auto backup scheduled",
            }
        )

        # Try to get real logs
        try:
            with open("logs/restaurant.log", "r", encoding="utf-8") as f:
                lines = f.readlines()[-10:]  # So'nggi 10 ta
                for line in lines:
                    if "INFO" in line and any(
                        word in line for word in ["server", "system", "start", "init"]
                    ):
                        parts = line.strip().split(" | ")
                        if len(parts) >= 2:
                            time_part = (
                                parts[0].split(" ")[1]
                                if " " in parts[0]
                                else parts[0][-8:]
                            )
                            message_part = " | ".join(parts[1:])
                            logs.append({"time": time_part, "message": message_part})
        except:
            pass

        return jsonify({"success": True, "logs": logs[-15:]})  # So'nggi 15 ta

    except Exception as e:
        app_logger.error(f"System logs error: {str(e)}")
        return jsonify({"success": False, "message": "System logs olishda xatolik"})


@app.route("/super-admin/get-environment-info")
@role_required("super_admin")
def super_admin_get_environment_info():
    "Super admin environment info API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        import sys

        info = {"pythonVersion": f"Python {sys.version.split()[0]}"}

        return jsonify({"success": True, "info": info})

    except Exception as e:
        app_logger.error(f"Environment info error: {str(e)}")
        return jsonify({"success": False, "info": {"pythonVersion": "Python 3.12+"}})


@app.route("/super-admin/clear-cache", methods=["POST"])
@role_required("super_admin")
def super_admin_clear_cache():
    "Super admin clear cache API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        # Cache manager orqali cache ni tozalash (safe)
        try:
            cm = cache_manager or get_cache_manager()
        except Exception:
            cm = None

        if cm and hasattr(cm, "memory_cache"):
            try:
                cm.memory_cache.clear()
                cm.cache_timestamps.clear()
            except Exception:
                pass

        app_logger.info("Super admin cache tozaladi")
        return jsonify({"success": True, "message": "Cache tozalandi"})

    except Exception as e:
        app_logger.error(f"Clear cache error: {str(e)}")
        return jsonify({"success": False, "message": "Cache tozalashda xatolik"})


@app.route("/super-admin/backup-database", methods=["POST"])
@role_required("super_admin")
def super_admin_backup_database():
    "Super admin database backup API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        import shutil
        import os

        # Backup directory yaratish
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        # Backup fayl nomi
        timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"database_backup_{timestamp}.sqlite3"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Database ni backup qilish
        shutil.copy2(DB_PATH, backup_path)

        app_logger.info(f"Super admin database backup yaratdi: {backup_filename}")
        return jsonify(
            {"success": True, "message": f"Backup yaratildi: {backup_filename}"}
        )

    except Exception as e:
        app_logger.error(f"Database backup error: {str(e)}")
        return jsonify({"success": False, "message": "Backup yaratishda xatolik"})


@app.route("/super-admin/save-config", methods=["POST"])
@role_required("super_admin")
def super_admin_save_config():
    "Super admin save config API"
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Super admin huquqi kerak"})

    try:
        data = request.get_json()

        # Konfiguratsiyani saqlash (bu yerda oddiy session'ga saqlash)
        session["system_config"] = {
            "maxOrdersPerHour": int(data.get("maxOrdersPerHour", 100)),
            "sessionTimeout": int(data.get("sessionTimeout", 120)),
            "rateLimit": int(data.get("rateLimit", 1000)),
            "updated_at": get_current_time().isoformat(),
        }

        app_logger.info("Super admin tizim konfiguratsiyasini yangiladi")
        return jsonify({"success": True, "message": "Konfiguratsiya saqlandi"})

    except Exception as e:
        app_logger.error(f"Save config error: {str(e)}")
        return jsonify(
            {"success": False, "message": "Konfiguratsiyani saqlashda xatolik"}
        )


@app.route("/api/super-admin/dashboard-stats")
@role_required("super_admin")
@cached(ttl=15)
def api_super_admin_dashboard_stats():
    # role_required decorator enforces super_admin session

    try:
        stats = {
            "total_orders": 0,
            "waiting_orders": 0,
            "ready_orders": 0,
            "served_orders": 0,
            "total_staff": 0,
            "total_couriers": 0,
            "total_users": 0,
        }

        # Orders statistics - safe execution
        try:
            result = execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)
            stats["total_orders"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Total orders query error: {str(e)}")
            stats["total_orders"] = 0

        try:
            result = execute_query(
                "SELECT COUNT(*) FROM orders WHERE status='waiting'", fetch_one=True
            )
            stats["waiting_orders"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Waiting orders query error: {str(e)}")
            stats["waiting_orders"] = 0

        try:
            result = execute_query(
                "SELECT COUNT(*) FROM orders WHERE status='ready'", fetch_one=True
            )
            stats["ready_orders"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Ready orders query error: {str(e)}")
            stats["ready_orders"] = 0

        try:
            result = execute_query(
                "SELECT COUNT(*) FROM orders WHERE status='served'", fetch_one=True
            )
            stats["served_orders"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Served orders query error: {str(e)}")
            stats["served_orders"] = 0

        # Staff statistics - safe execution
        try:
            result = execute_query("SELECT COUNT(*) FROM staff", fetch_one=True)
            stats["total_staff"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Total staff query error: {str(e)}")
            stats["total_staff"] = 0

        try:
            result = execute_query("SELECT COUNT(*) FROM couriers", fetch_one=True)
            stats["total_couriers"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Total couriers query error: {str(e)}")
            stats["total_couriers"] = 0

        try:
            result = execute_query("SELECT COUNT(*) FROM users", fetch_one=True)
            stats["total_users"] = (
                int(result[0]) if result and result[0] is not None else 0
            )
        except Exception as e:
            app_logger.warning(f"Total users query error: {str(e)}")
            stats["total_users"] = 0

        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        app_logger.error(f"Super admin dashboard stats error: {str(e)}")
        return jsonify(
            {
                "success": False,
                "stats": {
                    "total_orders": 0,
                    "waiting_orders": 0,
                    "ready_orders": 0,
                    "served_orders": 0,
                    "total_staff": 0,
                    "total_couriers": 0,
                    "total_users": 0,
                },
            }
        )


# ---- STAFF AUTH ----
@app.route("/staff-secure-login-w7m2k", methods=["GET", "POST"])
@app.route("/staff-secure-login-j7h3n", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        staff_id_str = request.form.get("staff_id", "").strip()
        password = request.form.get("password", "")

        if not staff_id_str or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("staff_login"))

        # ID raqam ekanligini tekshirish
        try:
            staff_id = int(staff_id_str)
        except ValueError:
            flash("ID raqam bo'lishi kerak.", "error")
            return redirect(url_for("staff_login"))

        # Staff ma'lumotlarini olish
        row = execute_query(
            "SELECT * FROM staff WHERE id=?", (staff_id,), fetch_one=True
        )

        if row:
            # Faollik vaqtini yangilash va ishchi soatlarini hisoblash
            now = get_current_time()
            now_iso = now.isoformat()

            try:
                # Row obyektini dict ga aylantirish
                if hasattr(row, "keys"):
                    row_dict = dict(row)
                else:
                    # Tuple format uchun manual dict yaratish
                    columns = [
                        "id",
                        "first_name",
                        "last_name",
                        "birth_date",
                        "phone",
                        "passport_series",
                        "passport_number",
                        "password_hash",
                        "total_hours",
                        "orders_handled",
                        "last_activity",
                        "created_at",
                    ]
                    row_dict = {
                        columns[i]: row[i] if i < len(row) else None
                        for i in range(len(columns))
                    }

                # Password hash ni tekshirish
                password_hash = row_dict.get("password_hash", "")
                if password_hash and check_password_hash(password_hash, password):
                    # Login muvaffaqiyatli - set exclusive staff role
                    display = f"{row_dict['first_name']} {row_dict['last_name']}"
                    set_role_session("staff", id=row_dict["id"], name=display)

                    # Faollik vaqtini yangilash
                    execute_query(
                        "UPDATE staff SET last_activity = ? WHERE id = ?",
                        (now_iso, staff_id),
                    )

                    flash(f"Xush kelibsiz, {row_dict['first_name']}!", "success")
                    return redirect(url_for("staff_dashboard"))
                else:
                    flash("Noto'g'ri ID yoki parol.", "error")
                    app_logger.warning(f"Failed staff login attempt for ID: {staff_id}")

            except Exception as dict_error:
                app_logger.error(f"Staff row dict conversion error: {str(dict_error)}")
                flash("Ma'lumotlarni qayta ishlashda xatolik.", "error")
                return redirect(url_for("staff_login"))
        else:
            flash("Xodim topilmadi.", "error")

    return render_template("staff_login.html")


@app.route("/staff/dashboard")
@role_required("staff")
def staff_dashboard():
    if "staff_id" not in session:
        flash("Xodim tizimiga kirish talab qilinadi.", "error")
        return redirect(url_for("staff_login"))

    cleanup_expired_orders()

    try:
        # Staff ID ni olish
        staff_id = session.get("staff_id")

        # Buyurtmalarni olish - soddalashtirilgan usul
        orders_raw = execute_query(
            """
            SELECT o.id, o.user_id, o.customer_name, o.ticket_no, o.order_type, 
                   o.status, o.delivery_address, o.delivery_distance, o.customer_phone, 
                   o.created_at, o.eta_time, o.branch_id,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity, ', ') as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            GROUP BY o.id
            ORDER BY
                CASE
                    WHEN o.status = 'waiting' THEN 1
                    WHEN o.status = 'ready' THEN 2
                    WHEN o.status = 'served' THEN 3
                    WHEN o.status = 'cancelled' THEN 4
                    WHEN o.status = 'on_way' THEN 5
                    WHEN o.status = 'delivered' THEN 6
                    ELSE 7
                END,
                o.created_at DESC
        """,
            fetch_all=True,
        )

        # Ma'lumotlarni dict formatiga o'tkazish
        orders = []
        if orders_raw:
            for row in orders_raw:
                try:
                    order_dict = dict(row) if hasattr(row, "keys") else {}
                    orders.append(order_dict)
                except Exception as row_error:
                    app_logger.warning(f"Order row processing error: {str(row_error)}")
                    continue

        # Staff statistikasini olish - xavfsiz usul
        try:
            staff_stats = execute_query(
                "SELECT orders_handled, COALESCE(total_hours, 0) as total_hours FROM staff WHERE id = ?",
                (staff_id,),
                fetch_one=True,
            )

            if staff_stats:
                try:
                    session["staff_orders_handled"] = int(
                        staff_stats.get("orders_handled", 0) or 0
                    )
                    session["staff_hours"] = round(
                        float(str(staff_stats.get("total_hours", 0) or 0)), 1
                    )
                except (ValueError, TypeError):
                    session["staff_orders_handled"] = 0
                    session["staff_hours"] = 0.0
            else:
                session["staff_orders_handled"] = 0
                session["staff_hours"] = 0.0
        except Exception as stats_error:
            app_logger.warning(f"Staff stats error, using defaults: {str(stats_error)}")
            session["staff_orders_handled"] = 0
            session["staff_hours"] = 0.0

        # Get notifications for staff
        current_user = {"type": "staff", "id": staff_id}
        notifications = get_notifications_for_user(current_user)

        app_logger.info(
            f"Staff dashboard loaded for staff_id: {staff_id}, found {len(orders)} orders, {len(notifications)} notifications"
        )

        # Template ni render qilish
        return render_template(
            "staff_dashboard.html", orders=orders, notifications=notifications
        )

    except Exception as e:
        app_logger.error(f"Staff dashboard error: {str(e)}")
        # Emergency fallback HTML
        return (
            f"""
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Xodim Dashboard - Xatolik</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <div class="alert alert-danger">
                    <h4>Xodim Dashboard - Xatolik</h4>
                    <p>Dashboard yuklashda xatolik yuz berdi: {str(e)}</p>
                    <a href="{url_for('staff_login')}" class="btn btn-primary">Login sahifasiga qaytish</a>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h5>Muammolarni hal qilish</h5>
                    </div>
                    <div class="card-body">
                        <ul>
                            <li>Serverni qayta ishga tushiring</li>
                            <li>Database connection ni tekshiring</li>
                            <li>Loglarni ko'rib chiqing</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """,
            500,
        )


@app.route("/staff/order/<int:order_id>/ready", methods=["POST"])
@app.route("/admin/order/<int:order_id>/ready", methods=["POST"])
@role_required("staff")
def staff_mark_order_ready(order_id):
    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    staff_id = session.get("staff_id")

    try:
        # Buyurtma ma'lumotlarini olish
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("staff_dashboard"))

        # Buyurtmani 'ready' qilib belgilash
        execute_query(
            "UPDATE orders SET status='ready' WHERE id=? AND status='waiting'",
            (order_id,),
        )

        # Xodimning ko'rib chiqgan buyurtmalar sonini oshirish
        execute_query(
            "UPDATE staff SET orders_handled = COALESCE(orders_handled, 0) + 1 WHERE id = ?",
            (staff_id,),
        )

        # Avtomatik bildirishnoma yuborish
        customer_name = order.get("customer_name", "Mijoz")
        total_amount = order.get("total_amount", 0)
        send_order_notifications(order_id, "ready", customer_name, total_amount)

        flash("Buyurtma tayyor!", "success")
    except Exception as e:
        app_logger.error(f"Staff mark order ready error: {str(e)}")
        flash("Buyurtmani tayyor qilishda xatolik.", "error")

    return redirect(url_for("staff_dashboard"))


@app.route("/staff/order/<int:order_id>/served", methods=["POST"])
@app.route("/admin/order/<int:order_id>/served", methods=["POST"])
@role_required("staff")
def staff_mark_order_served(order_id):
    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    try:
        # Buyurtma ma'lumotlarini olish
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("staff_dashboard"))

        # Buyurtmani 'served' qilib belgilash
        execute_query(
            "UPDATE orders SET status='served' WHERE id=? AND status='ready'",
            (order_id,),
        )

        # Avtomatik bildirishnoma yuborish
        customer_name = order.get("customer_name", "Mijoz")
        total_amount = order.get("total_amount", 0)
        send_order_notifications(order_id, "served", customer_name, total_amount)

        flash("Buyurtma berildi!", "success")
    except Exception as e:
        app_logger.error(f"Staff mark order served error: {str(e)}")
        flash("Buyurtmani berildi deb belgilashda xatolik.", "error")

    return redirect(url_for("staff_dashboard"))


@app.route("/admin/order/<int:order_id>/cancel", methods=["POST"])
@app.route("/staff/order/<int:order_id>/cancel", methods=["POST"])
@role_required("staff")
def staff_cancel_order(order_id):
    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    try:
        # Buyurtma ma'lumotlarini olish
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("staff_dashboard"))

        # Buyurtmani 'cancelled' qilib belgilash
        execute_query("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))

        # Avtomatik bildirishnoma yuborish
        customer_name = order.get("customer_name", "Mijoz")
        total_amount = order.get("total_amount", 0)
        send_order_notifications(order_id, "cancelled", customer_name, total_amount)

        flash("Buyurtma bekor qilindi!", "success")
    except Exception as e:
        app_logger.error(f"Staff cancel order error: {str(e)}")
        flash("Buyurtmani bekor qilishda xatolik.", "error")

    return redirect(url_for("staff_dashboard"))


# Superadmin explicit approval endpoint - marks pending -> confirmed/accepted
@app.route("/admin/order/<int:order_id>/approve", methods=["POST"])
@role_required("super_admin")
def superadmin_approve_order(order_id):
    """Superadmin approves a pending order. Only super_admin role can call this."""
    try:
        order = execute_query(
            "SELECT * FROM orders WHERE id = ?", (order_id,), fetch_one=True
        )
        if not order:
            flash("Buyurtma topilmadi.", "error")
            return redirect(url_for("super_admin_dashboard"))

        if order.get("status") != "pending":
            flash("Buyurtma tasdiqlash uchun pending holatda emas.", "warning")
            return redirect(url_for("super_admin_dashboard"))

    # Update status in DB to 'waiting' so staff workflows (which expect 'waiting') continue to work.
    # We still notify the customer with a 'confirmed' notification below.
        execute_query("UPDATE orders SET status = 'waiting' WHERE id = ?", (order_id,))

        # Notify customer and staff
        customer_name = order.get("customer_name", "Mijoz")
        total_amount = order.get("total_amount", 0)
        send_order_notifications(order_id, "confirmed", customer_name, total_amount)

        flash("Buyurtma tasdiqlandi va mijozga xabar yuborildi.", "success")
    except Exception as e:
        app_logger.error(f"Superadmin approve order error: {str(e)}")
        flash("Buyurtmani tasdiqlashda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/staff/menu")
@role_required("staff")
def staff_menu():
    "Xodim menu boshqaruvi"
    if "staff_id" not in session and not session.get("super_admin"):
        return redirect(url_for("staff_login"))

    try:
        # Ma'lumotlarni to'g'ri olish
        with db_pool.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM menu_items ORDER BY category, name")
            menu_items_raw = cur.fetchall()

            menu_items = []
            if menu_items_raw:
                for row in menu_items_raw:
                    try:
                        item_dict = dict(row)
                        # Default qiymatlarni qo'shish
                        item_dict.setdefault("description", "")
                        item_dict.setdefault(
                            "image_url", "/static/images/default-men.jpg"
                        )
                        item_dict.setdefault("available", 1)
                        item_dict.setdefault("discount_percentage", 0)
                        item_dict.setdefault("rating", 0.0)
                        item_dict.setdefault("orders_count", 0)

                        # Mahsulot media fayllarini olish
                        media_query = """
                            SELECT media_type, media_url, display_order, is_main
                            FROM product_media 
                            WHERE menu_item_id = ? 
                            ORDER BY is_main DESC, display_order ASC
                        """
                        cur.execute(media_query, (item_dict["id"],))
                        media_files = cur.fetchall()

                        item_dict["media_files"] = []
                        if media_files:
                            for media in media_files:
                                media_dict = dict(media)
                                item_dict["media_files"].append(media_dict)

                        # Agar media fayllar yo'q bo'lsa, eski image_url dan foydalanish
                        if not item_dict["media_files"] and item_dict.get("image_url"):
                            item_dict["media_files"] = [
                                {
                                    "media_type": "image",
                                    "media_url": item_dict["image_url"],
                                    "display_order": 0,
                                    "is_main": True,
                                }
                            ]

                        menu_items.append(item_dict)
                    except Exception as row_error:
                        app_logger.warning(
                            f"Menu item row processing error: {str(row_error)}"
                        )
                        continue

        app_logger.info(f"Staff menu loaded: {len(menu_items)} items found")
        return render_template("staff_menu.html", menu_items=menu_items)

    except Exception as e:
        app_logger.error(f"Staff menu error: {str(e)}")
        return render_template("staff_menu.html", menu_items=[])


@app.route("/admin/menu")
def admin_menu():
    "Admin menu management"
    if not session.get("staff_id") and not session.get("super_admin"):
        return redirect(url_for("staff_login"))
    return staff_menu()


@app.route("/admin/employees")
def admin_employees():
    "Admin employee management"
    if not session.get("staff_id") and not session.get("super_admin"):
        return redirect(url_for("staff_login"))
    return staff_employees()


@app.route("/admin/logout")
def admin_logout():
    "Admin logout"
    if session.get("staff_id"):
        return staff_logout()
    elif session.get("super_admin"):
        return super_admin_logout()
    else:
        return redirect(url_for("index"))


@app.route("/staff/employees")
def staff_employees():
    "Xodimlar ro'yxati"
    if "staff_id" not in session and not session.get("super_admin"):
        return redirect(url_for("staff_login"))

    try:
        # Ma'lumotlarni to'g'ri olish
        with db_pool.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM staff ORDER BY created_at DESC")
            staff_raw = cur.fetchall()

            staff_list = []
            if staff_raw:
                for row in staff_raw:
                    try:
                        staff_dict = dict(row)
                        # Default qiymatlarni qo'shish
                        staff_dict.setdefault("total_hours", 0.0)
                        staff_dict.setdefault("orders_handled", 0)
                        staff_dict.setdefault("last_activity", "")
                        staff_list.append(staff_dict)
                    except Exception as row_error:
                        app_logger.warning(
                            f"Staff row processing error: {str(row_error)}"
                        )
                        continue

        app_logger.info(
            f"Staff employees loaded: {len(staff_list)} staff members found"
        )
        return render_template("staff_employees.html", staff_list=staff_list)

    except Exception as e:
        app_logger.error(f"Staff employees error: {str(e)}")
        return render_template("staff_employees.html", staff_list=[])


@app.route("/staff/logout")
def staff_logout():
    # Terminate the session in database if session_id exists
    current_session_id = session.get("session_id")
    if current_session_id:
        try:
            terminate_session(current_session_id, current_session_id=current_session_id)
        except Exception as e:
            app_logger.warning(f"Failed to terminate staff session in database: {e}")

    session.clear()  # Clear entire session instead of just popping specific keys
    flash("Xodim tizimidan chiqdingiz.", "info")
    return redirect(url_for("index"))


@app.route("/super-admin-control-panel-master-z8x9k")
@app.route("/super-admin-dashboard-ultimate-m4st3r")
@app.route("/super-admin/dashboard-ultimate-m4st3r")
@role_required("super_admin")
def super_admin_dashboard():
    "Super admin dashboard"
    if not session.get("super_admin"):
        flash("Super admin paneliga kirish talab qilinadi.", "error")
        return redirect(url_for("super_admin_login"))

    try:

        # Xodimlar ma'lumotlari - soddalashtirilgan
        staff_db = []
        try:
            staff_raw = execute_query(
                "SELECT * FROM staff ORDER BY created_at DESC", fetch_all=True
            )
            if staff_raw:
                for staff in staff_raw:
                    try:
                        staff_dict = dict(staff) if hasattr(staff, "keys") else {}
                        # Ensure required fields exist
                        staff_dict.setdefault("total_hours", 0.0)
                        staff_dict.setdefault("orders_handled", 0)
                        staff_db.append(staff_dict)
                    except Exception as staff_error:
                        app_logger.warning(
                            f"Staff processing error: {str(staff_error)}"
                        )
                        continue
        except Exception as e:
            app_logger.error(f"Staff ma'lumotlarini olishda xatolik: {str(e)}")
            staff_db = []

        # Kuryerlar ma'lumotlari - soddalashtirilgan
        couriers_db = []
        try:
            couriers_raw = execute_query(
                "SELECT * FROM couriers ORDER BY created_at DESC", fetch_all=True
            )
            if couriers_raw:
                for courier in couriers_raw:
                    try:
                        courier_dict = dict(courier) if hasattr(courier, "keys") else {}
                        # Ensure required fields exist
                        courier_dict.setdefault("total_hours", 0.0)
                        courier_dict.setdefault("deliveries_completed", 0)
                        couriers_db.append(courier_dict)
                    except Exception as courier_error:
                        app_logger.warning(
                            f"Courier processing error: {str(courier_error)}"
                        )
                        continue
        except Exception as e:
            app_logger.error(f"Couriers ma'lumotlarini olishda xatolik: {str(e)}")
            couriers_db = []

        # Foydalanuvchilarni olish - soddalashtirilgan
        users_db = []
        try:
            users_raw = execute_query(
                "SELECT * FROM users ORDER BY created_at DESC", fetch_all=True
            )
            if users_raw:
                users_db = [dict(user) for user in users_raw if hasattr(user, "keys")]
        except Exception as e:
            app_logger.error(f"Users ma'lumotlarini olishda xatolik: {str(e)}")
            users_db = []

        # JSON fayldan foydalanuvchilarni olish - xavfsiz
        users_json = []
        users_file = "users.json"
        if os.path.exists(users_file):
            try:
                with open(users_file, "r", encoding="utf-8") as f:
                    users_json = json.load(f) or []
            except Exception as e:
                app_logger.warning(f"Users JSON faylini o'qishda xatolik: {str(e)}")
                users_json = []

        # Savollarni olish - soddalashtirilgan
        questions = []
        try:
            questions_raw = execute_query(
                "SELECT * FROM questions ORDER BY created_at DESC", fetch_all=True
            )
            if questions_raw:
                questions = [dict(row) for row in questions_raw if hasattr(row, "keys")]
        except Exception as e:
            app_logger.error(f"Questions ma'lumotlarini olishda xatolik: {str(e)}")
            questions = []

        # Filiallarni olish - soddalashtirilgan
        branches = []
        try:
            branches_raw = execute_query(
                "SELECT * FROM branches ORDER BY created_at DESC", fetch_all=True
            )
            if branches_raw:
                for branch in branches_raw:
                    try:
                        branch_dict = dict(branch) if hasattr(branch, "keys") else {}
                        # Ensure required fields exist with defaults
                        branch_dict.setdefault("latitude", 41.2995)
                        branch_dict.setdefault("longitude", 69.2401)
                        branch_dict.setdefault("delivery_radius", 15.0)
                        branch_dict.setdefault("average_rating", 0.0)
                        branch_dict.setdefault("total_ratings", 0)
                        branches.append(branch_dict)
                    except Exception as branch_error:
                        app_logger.warning(
                            f"Branch processing error: {str(branch_error)}"
                        )
                        continue
        except Exception as e:
            app_logger.error(f"Branches ma'lumotlarini olishda xatolik: {str(e)}")
            branches = []

        # Buyurtmalar statistikasi - soddalashtirilgan
        stats = {
            "total_orders": 0,
            "waiting_orders": 0,
            "ready_orders": 0,
            "served_orders": 0,
            "month_orders": 0,
            "total_staff": max(0, len(staff_db) if staff_db else 0),
            "total_couriers": max(0, len(couriers_db) if couriers_db else 0),
            "total_users": max(0, len(users_db) if users_db else 0),
            "total_users_json": max(0, len(users_json) if users_json else 0),
        }

        try:
            # Jami buyurtmalar - safe query
            try:
                result = execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)
                if result and len(result) > 0 and result[0] is not None:
                    stats["total_orders"] = max(0, int(result[0]))
                else:
                    stats["total_orders"] = 0
            except Exception as total_error:
                app_logger.warning(
                    f"Total orders statistikasini olishda xatolik: {str(total_error)}"
                )
                stats["total_orders"] = 0

            # Status bo'yicha statistika - safe queries
            for status in ["waiting", "ready", "served"]:
                try:
                    result = execute_query(
                        "SELECT COUNT(*) FROM orders WHERE status = ?",
                        (status,),
                        fetch_one=True,
                    )
                    if result and len(result) > 0 and result[0] is not None:
                        stats[f"{status}_orders"] = max(0, int(result[0]))
                    else:
                        stats[f"{status}_orders"] = 0
                except Exception as status_error:
                    app_logger.warning(
                        f"{status} orders statistikasini olishda xatolik: {str(status_error)}"
                    )
                    stats[f"{status}_orders"] = 0

            # Bu oylik statistika - safe query
            try:
                current_month = get_current_time().strftime("%Y-%m")
                result = execute_query(
                    "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",
                    (f"{current_month}%",),
                    fetch_one=True,
                )
                if result and len(result) > 0 and result[0] is not None:
                    stats["month_orders"] = max(0, int(result[0]))
                else:
                    stats["month_orders"] = 0
            except Exception as month_error:
                app_logger.warning(
                    f"Bu oylik statistikani olishda xatolik: {str(month_error)}"
                )
                stats["month_orders"] = 0

        except Exception as e:
            app_logger.error(f"Statistikalarni hisoblashda umumiy xatolik: {str(e)}")

        # Get notifications for super admin
        current_user = {"type": "super_admin", "id": None}
        notifications = get_notifications_for_user(current_user)

        return render_template(
            "super_admin_dashboard.html",
            staff_db=staff_db or [],
            couriers_db=couriers_db or [],
            users_db=users_db or [],
            users_json=users_json or [],
            questions=questions or [],
            branches=branches or [],
            stats=stats,
            ats=stats,
            notifications=notifications,
        )

    except Exception as e:
        app_logger.error(f"Super admin dashboard xatoligi: {str(e)}")
        # Emergency HTML fallback
        return (
            f"""
        <!DOCTYPE html>
        <html><head><title>Super Admin Dashboard - Error</title></head>
        <body>
            <h1>Super Admin Dashboard</h1>
            <div style="color: red;">Dashboard yuklashda xatolik: {str(e)}</div>
            <p><a href="{url_for('super_admin_login')}">Login sahifasiga qaytish</a></p>
        </body></html>
        """,
            500,
        )


@app.route("/super-admin/analytics")
@role_required("super_admin")
def super_admin_analytics():
    "Super admin analytics sahifasi"
    if not session.get("super_admin"):
        flash("Super admin paneliga kirish talab qilinadi.", "error")
        return redirect(url_for("super_admin_login"))

    try:
        # Analytics ma'lumotlarini tayyorlash (provide nested dicts expected by templates)
        analytics_data = {
            "monthly_orders": [],
            "popular_items": [],
            "total_revenue": 0,
            "growth_rate": 0,
            # templates expect analytics.monthly.revenue, analytics.monthly.orders, analytics.weekly, analytics.daily
            "monthly": {"revenue": 0, "orders": 0},
            "weekly": {"revenue": 0, "orders": 0},
            "daily": {"revenue": 0, "orders": 0},
        }

        try:
            conn = get_db()
            cur = conn.cursor()

            # So'nggi 6 oylik buyurtmalar statistikasi
            for i in range(6):
                month_date = (
                    get_current_time() - datetime.timedelta(days=30 * i)
                ).strftime("%Y-%m")
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",
                        (f"{month_date}%",),
                    )
                    result = cur.fetchone()
                    count = result[0] if result and result[0] is not None else 0
                    analytics_data["monthly_orders"].append(
                        {"month": month_date, "orders": count}
                    )
                    # accumulate monthly orders for summary
                    analytics_data["monthly"]["orders"] += int(count or 0)
                except Exception as month_error:
                    app_logger.warning(
                        f"Month {month_date} analytics error: {str(month_error)}"
                    )
                    analytics_data["monthly_orders"].append(
                        {"month": month_date, "orders": 0}
                    )

            analytics_data["monthly_orders"].reverse()

            # Weekly and daily quick summaries (safe queries)
            try:
                # daily
                cur.execute(
                    "SELECT COUNT(*), COALESCE(SUM(r.total_amount),0) FROM orders o LEFT JOIN receipts r ON r.order_id = o.id WHERE DATE(o.created_at) = ?",
                    (get_current_time().strftime("%Y-%m-%d"),),
                )
                row = cur.fetchone()
                analytics_data["daily"]["orders"] = int(row[0] or 0) if row else 0
                analytics_data["daily"]["revenue"] = (
                    int(row[1] or 0) if row and len(row) > 1 else 0
                )

                # weekly (7 days)
                week_start = (get_current_time() - datetime.timedelta(days=7)).strftime(
                    "%Y-%m-%d"
                )
                cur.execute(
                    "SELECT COUNT(*), COALESCE(SUM(r.total_amount),0) FROM orders o LEFT JOIN receipts r ON r.order_id = o.id WHERE DATE(o.created_at) >= ?",
                    (week_start,),
                )
                row = cur.fetchone()
                analytics_data["weekly"]["orders"] = int(row[0] or 0) if row else 0
                analytics_data["weekly"]["revenue"] = (
                    int(row[1] or 0) if row and len(row) > 1 else 0
                )

                # monthly revenue (last 30 days)
                month_start = (
                    get_current_time() - datetime.timedelta(days=30)
                ).strftime("%Y-%m-%d")
                cur.execute(
                    "SELECT COALESCE(SUM(r.total_amount),0) FROM orders o LEFT JOIN receipts r ON r.order_id = o.id WHERE DATE(o.created_at) >= ?",
                    (month_start,),
                )
                row = cur.fetchone()
                analytics_data["monthly"]["revenue"] = int(row[0] or 0) if row else 0

                # if monthly.orders is zero (not accumulated), set from monthly_orders list
                if (
                    analytics_data["monthly"]["orders"] == 0
                    and analytics_data["monthly_orders"]
                ):
                    analytics_data["monthly"]["orders"] = sum(
                        [m.get("orders", 0) for m in analytics_data["monthly_orders"]]
                    )

            except Exception as summary_err:
                app_logger.warning(
                    f"Analytics weekly/daily summary error: {str(summary_err)}"
                )

            # Eng ko'p sotilgan mahsulotlar
            try:
                cur.execute(
                    """
                    SELECT mi.name, COALESCE(SUM(od.quantity), 0) as total_sold
                    FROM menu_items mi
                    LEFT JOIN order_details od ON mi.id = od.menu_item_id
                    GROUP BY mi.id, mi.name
                    ORDER BY total_sold DESC
                    LIMIT 5
                """
                )
                popular_items_raw = cur.fetchall() or []
                analytics_data["popular_items"] = [
                    {"name": row[0], "sold": row[1]} for row in popular_items_raw
                ]
            except Exception as popular_error:
                app_logger.warning(
                    f"Popular items analytics error: {str(popular_error)}"
                )
                analytics_data["popular_items"] = []

        finally:
            if "conn" in locals():
                conn.close()

        return render_template("super_admin_analytics.html", analytics=analytics_data)

    except Exception as e:
        app_logger.error(f"Super admin analytics xatoligi: {str(e)}")
        flash("Analytics ma'lumotlarini yuklashda xatolik.", "error")
        return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/reports")
@role_required("super_admin")
def super_admin_reports():
    "Super admin reports sahifasi"
    if not session.get("super_admin"):
        flash("Super admin paneliga kirish talab qilinadi.", "error")
        return redirect(url_for("super_admin_login"))

    try:
        # Hisobotlar ma'lumotlarini hisoblash
        reports_data = {
            "daily": {"orders": 0, "revenue": 0},
            "weekly": {"orders": 0, "revenue": 0},
            "monthly": {"orders": 0, "revenue": 0},
        }

        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Kunlik hisobot
            today = get_current_time().strftime("%Y-%m-%d")
            cur.execute(
                "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?", (today,)
            )
            result = cur.fetchone()
            daily_orders = result[0] if result and result[0] is not None else 0
            reports_data["daily"]["orders"] = daily_orders

            # Haftalik hisobot
            week_ago = (get_current_time() - datetime.timedelta(days=7)).strftime(
                "%Y-%m-%d"
            )
            cur.execute(
                "SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= ?", (week_ago,)
            )
            result = cur.fetchone()
            weekly_orders = result[0] if result and result[0] is not None else 0
            reports_data["weekly"]["orders"] = weekly_orders

            # Oylik hisobot
            month_ago = (get_current_time() - datetime.timedelta(days=30)).strftime(
                "%Y-%m-%d"
            )
            cur.execute(
                "SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= ?", (month_ago,)
            )
            result = cur.fetchone()
            monthly_orders = result[0] if result and result[0] is not None else 0
            reports_data["monthly"]["orders"] = monthly_orders

            # Compute revenue for daily, weekly and monthly using receipts.total_amount (safe joins)
            try:
                # daily revenue
                cur.execute(
                    "SELECT COALESCE(SUM(r.total_amount), 0) FROM orders o LEFT JOIN receipts r ON o.id = r.order_id WHERE DATE(o.created_at) = ?",
                    (today,),
                )
                res = cur.fetchone()
                reports_data["daily"]["revenue"] = (
                    int(res[0]) if res and res[0] is not None else 0
                )

                # weekly revenue (last 7 days)
                cur.execute(
                    "SELECT COALESCE(SUM(r.total_amount), 0) FROM orders o LEFT JOIN receipts r ON o.id = r.order_id WHERE DATE(o.created_at) >= ?",
                    (week_ago,),
                )
                res = cur.fetchone()
                reports_data["weekly"]["revenue"] = (
                    int(res[0]) if res and res[0] is not None else 0
                )

                # monthly revenue (last 30 days)
                cur.execute(
                    "SELECT COALESCE(SUM(r.total_amount), 0) FROM orders o LEFT JOIN receipts r ON o.id = r.order_id WHERE DATE(o.created_at) >= ?",
                    (month_ago,),
                )
                res = cur.fetchone()
                reports_data["monthly"]["revenue"] = (
                    int(res[0]) if res and res[0] is not None else 0
                )
            except Exception as rev_err:
                app_logger.warning(f"Reports revenue aggregation error: {str(rev_err)}")
                # ensure numeric defaults
                reports_data["daily"]["revenue"] = (
                    reports_data["daily"].get("revenue", 0) or 0
                )
                reports_data["weekly"]["revenue"] = (
                    reports_data["weekly"].get("revenue", 0) or 0
                )
                reports_data["monthly"]["revenue"] = (
                    reports_data["monthly"].get("revenue", 0) or 0
                )

        # Template fallback
        template_path = os.path.join(app.template_folder, "super_admin_reports.html")
        if os.path.exists(template_path):
            return render_template("super_admin_reports.html", reports=reports_data)
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reports - Super Admin</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-4">
                    <h2>Hisobotlar</h2>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Bugungi kun</h5>
                                    <p class="card-text">Buyurtmalar: {reports_data['daily']['orders']}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Bu hafta</h5>
                                    <p class="card-text">Buyurtmalar: {reports_data['weekly']['orders']}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Bu oy</h5>
                                    <p class="card-text">Buyurtmalar: {reports_data['monthly']['orders']}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <a href="{url_for('super_admin_dashboard')}" class="btn btn-primary mt-3">Dashboard ga qaytish</a>
                </div>
            </body>
            </html>
            """
            return html_content

    except Exception as e:
        app_logger.error(f"Super admin reports xatoligi: {str(e)}")
        return (
            f"""
        <div class="container mt-4">
            <h2>Reports - Xatolik</h2>
            <div class="alert alert-danger">Hisobotlarni yuklashda xatolik: {str(e)}</div>
            <a href="{url_for('super_admin_dashboard')}" class="btn btn-primary">Dashboard ga qaytish</a>
        </div>
        """,
            500,
        )


@app.route("/super-admin/system")
def super_admin_system():
    "Super admin system sahifasi"
    if not session.get("super_admin"):
        flash("Super admin paneliga kirish talab qilinadi.", "error")
        return redirect(url_for("super_admin_login"))

    try:
        # System ma'lumotlarini to'plash
        system_info = {
            "database": {
                "tables_count": 12,  # Ma'lum jadvallar soni
                "tables": [
                    "users",
                    "staff",
                    "couriers",
                    "orders",
                    "menu_items",
                    "cart_items",
                    "order_details",
                    "ratings",
                    "questions",
                    "receipts",
                    "branches",
                    "favorites",
                ],
            },
            "environment": "production",
            "performance": {
                "total_requests": (
                    getattr(performance_monitor, "success_count", 0)
                    + getattr(performance_monitor, "error_count", 0)
                    if hasattr(performance_monitor, "success_count")
                    and hasattr(performance_monitor, "error_count")
                    else 0
                ),
                "avg_response_time": 0.25,
                "max_response_time": 2.5,
                "min_response_time": 0.05,
            },
        }

        # Template fallback
        template_path = os.path.join(app.template_folder, "super_admin_system.html")
        if os.path.exists(template_path):
            return render_template("super_admin_system.html", system=system_info)
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <title>System - Super Admin</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-4">
                    <h2>Tizim ma'lumotlari</h2>
                    <div class="row">
                        <div class="col-md-6">
                            <h4>Database</h4>
                            <p>Jadvallar soni: {system_info['database']['tables_count']}</p>
                            <p>Environment: {system_info['environment']}</p>
                        </div>
                        <div class="col-md-6">
                            <h4>Performance</h4>
                            <p>Jami so'rovlar: {system_info['performance'].get('total_requests', 0)}</p>
                            <p>O'rtacha javob vaqti: {system_info['performance'].get('avg_response_time', 0):.2f}s</p>
                        </div>
                    </div>
                    <a href="{url_for('super_admin_dashboard')}" class="btn btn-primary mt-3">Dashboard ga qaytish</a>
                </div>
            </body>
            </html>
            """
            return html_content

    except Exception as e:
        app_logger.error(f"Super admin system xatoligi: {str(e)}")
        return (
            f"""
        <div class="container mt-4">
            <h2>System - Xatolik</h2>
            <div class="alert alert-danger">Tizim ma'lumotlarini yuklashda xatolik: {str(e)}</div>
            <a href="{url_for('super_admin_dashboard')}" class="btn btn-primary">Dashboard ga qaytish</a>
        </div>
        """,
            500,
        )


@app.route("/super-admin/logs")
def super_admin_logs():
    "Super admin logs sahifasi"
    if not session.get("super_admin"):
        flash("Super admin paneliga kirish talab qilinadi.", "error")
        return redirect(url_for("super_admin_login"))

    try:
        # Log fayllarini o'qish
        logs_data = {"recent_logs": [], "error_logs": [], "system_logs": []}

        # Recent logs
        try:
            if os.path.exists("logs/restaurant.log"):
                with open("logs/restaurant.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()[-50:]  # So'nggi 50 ta log
                    logs_data["recent_logs"] = [
                        line.strip() for line in lines if line.strip()
                    ]
            else:
                logs_data["recent_logs"] = ["Log fayli topilmadi"]
        except Exception as e:
            app_logger.warning(f"Restaurant log faylini o'qishda xatolik: {str(e)}")
            logs_data["recent_logs"] = ["Log faylini o'qib bo'lmadi"]

        # Error logs
        try:
            if os.path.exists("logs/errors.log"):
                with open("logs/errors.log", "r", encoding="utf-8") as f:
                    lines = f.readlines()[-30:]  # So'nggi 30 ta error
                    logs_data["error_logs"] = [
                        line.strip() for line in lines if line.strip()
                    ]
            else:
                logs_data["error_logs"] = ["Error log fayli topilmadi"]
        except Exception as e:
            app_logger.warning(f"Error log faylini o'qishda xatolik: {str(e)}")
            logs_data["error_logs"] = ["Error log faylini o'qib bo'lmadi"]

        # System logs - mock data
        logs_data["system_logs"] = [
            f"{get_current_time().strftime('%Y-%m-%d %H:%M:%S')} - System started successfully",
            f"{get_current_time().strftime('%Y-%m-%d %H:%M:%S')} - Database connection established",
            f"{get_current_time().strftime('%Y-%m-%d %H:%M:%S')} - Super admin panel accessed",
        ]

        # Template fallback
        template_path = os.path.join(app.template_folder, "super_admin_logs.html")
        if os.path.exists(template_path):
            return render_template("super_admin_logs.html", logs=logs_data)
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Logs - Super Admin</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-4">
                    <h2>Loglar</h2>
                    <div class="row">
                        <div class="col-md-6">
                            <h4>"So'nggi loglar"</h4>
                            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                                {'<br>'.join(logs_data['recent_logs']) if logs_data['recent_logs'] else 'Loglar mavjud emas'}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h4>Xatolar</h4>
                            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                                {'<br>'.join(logs_data['error_logs']) if logs_data['error_logs'] else 'Xatolar mavjud emas'}
                            </div>
                        </div>
                    </div>
                    <a href="{url_for('super_admin_dashboard')}" class="btn btn-primary mt-3">Dashboard ga qaytish</a>
                </div>
            </body>
            </html>
            """
            return html_content

    except Exception as e:
        app_logger.error(f"Super admin logs xatoligi: {str(e)}")
        return (
            f"""
        <div class="container mt-4">
            <h2>Logs - Xatolik</h2>
            <div class="alert alert-danger">Loglarniyuklashda xatolik: {str(e)}</div>
            <a href="{url_for('super_admin_dashboard')}" class="btn btn-primary">Dashboard ga qaytish</a>
        </div>
        """,
            500,
        )


@app.route("/super-admin/delete-courier/<int:courier_id>", methods=["POST"])
def super_admin_delete_courier(courier_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        courier_data = execute_query(
            "SELECT first_name, last_name FROM couriers WHERE id = ?",
            (courier_id,),
            fetch_one=True,
        )
        if not courier_data:
            flash("Kuryer topilmadi.", "error")
        else:
            execute_query("DELETE FROM couriers WHERE id = ?", (courier_id,))
            app_logger.info(
                f"Super admin kuryerni o'chirdi: {courier_data.get('first_name')} {courier_data.get('last_name')} (ID: {courier_id})"
            )
            flash(
                f"Kuryer {courier_data.get('first_name', 'N/A')} {courier_data.get('last_name', 'N/A')} muvaffaqiyatli o'chirildi.",
                "success",
            )

    except Exception as e:
        app_logger.error(f"Delete courier error: {str(e)}")
        flash("Kuryerni o'chirishda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/staff/register", methods=["GET", "POST"])
def staff_register():
    "Xodim ro'yxatdan o'tish"
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        passport_series = request.form.get("passport_series", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        password = request.form.get("password", "")

        if not all(
            [
                first_name,
                last_name,
                birth_date,
                phone,
                passport_series,
                passport_number,
                password,
            ]
        ):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("staff_register"))

        try:
            password_hash = generate_password_hash(password)
            now = get_current_time().isoformat()

            staff_id = execute_query(
                """
                INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    first_name,
                    last_name,
                    birth_date,
                    phone,
                    passport_series,
                    passport_number,
                    password_hash,
                    now,
                ),
            )

            # JSON fayliga saqlash
            executor.submit(
                save_staff_to_json,
                first_name,
                last_name,
                birth_date,
                phone,
                staff_id,
                get_current_time(),
            )

            flash(f"Muvaffaqiyatli ro'yxatdan o'tdingiz! ID: {staff_id}", "success")
            return redirect(url_for("staff_login"))

        except Exception as e:
            app_logger.error(f"Staff registration error: {str(e)}")
            flash("Ro'yxatdan o'tishda xatolik yuz berdi.", "error")

    return render_template("staff_register.html")


@app.route("/staff-register-secure-k3x8p", methods=["GET", "POST"])
@app.route("/staff/register", methods=["GET", "POST"])
def staff_register_new():
    return staff_register()


@app.route("/courier/register", methods=["GET", "POST"])
def courier_register():
    "Kuryer ro'yxatdan o'tish"
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        passport_series = request.form.get("passport_series", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        password = request.form.get("password", "")

        if not all(
            [
                first_name,
                last_name,
                birth_date,
                phone,
                passport_series,
                passport_number,
                password,
            ]
        ):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("courier_register"))

        try:
            password_hash = generate_password_hash(password)
            now = get_current_time().isoformat()

            courier_id = execute_query(
                """
                INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    first_name,
                    last_name,
                    birth_date,
                    phone,
                    passport_series,
                    passport_number,
                    password_hash,
                    now,
                ),
            )

            flash(f"Muvaffaqiyatli ro'yxatdan o'tdingiz! ID: {courier_id}", "success")
            return redirect(url_for("courier_login"))

        except Exception as e:
            app_logger.error(f"Courier registration error: {str(e)}")
            flash("Ro'yxatdan o'tishda xatolik yuz berdi.", "error")

    return render_template("courier_register.html")


@app.route("/super-admin/add-staff", methods=["POST"])
def super_admin_add_staff():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    birth_date = request.form.get("birth_date", "").strip()
    phone = request.form.get("phone", "").strip()
    passport_series = request.form.get("passport_series", "").strip()
    passport_number = request.form.get("passport_number", "").strip()
    password = request.form.get("password", "")

    if not all(
        [
            first_name,
            last_name,
            birth_date,
            phone,
            passport_series,
            passport_number,
            password,
        ]
    ):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        password_hash = generate_password_hash(password)
        now = get_current_time().isoformat()

        staff_id = execute_query(
            """
            INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                first_name,
                last_name,
                birth_date,
                phone,
                passport_series,
                passport_number,
                password_hash,
                now,
            ),
        )

        flash(f"Yangi xodim qo'shildi. ID: {staff_id}", "success")
    except Exception as e:
        app_logger.error(f"Add staff error: {str(e)}")
        flash("Xodim qo'shishda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/delete-staff/<int:staff_id>", methods=["POST"])
def super_admin_delete_staff(staff_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        staff_data = execute_query(
            "SELECT first_name, last_name FROM staff WHERE id = ?",
            (staff_id,),
            fetch_one=True,
        )
        if not staff_data:
            flash("Xodim topilmadi.", "error")
        else:
            execute_query("DELETE FROM staff WHERE id = ?", (staff_id,))
            app_logger.info(
                f"Super admin xodimni o'chirdi: {staff_data.get('first_name')} {staff_data.get('last_name')} (ID: {staff_id})"
            )
            flash(
                f"Xodim {staff_data.get('first_name', 'N/A')} {staff_data.get('last_name', 'N/A')} muvaffaqiyatli o'chirildi.",
                "success",
            )

    except Exception as e:
        app_logger.error(f"Delete staff error: {str(e)}")
        flash("Xodimni o'chirishda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/add-courier", methods=["POST"])
def super_admin_add_courier():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    birth_date = request.form.get("birth_date", "").strip()
    phone = request.form.get("phone", "").strip()
    passport_series = request.form.get("passport_series", "").strip()
    passport_number = request.form.get("passport_number", "").strip()
    password = request.form.get("password", "")

    if not all(
        [
            first_name,
            last_name,
            birth_date,
            phone,
            passport_series,
            passport_number,
            password,
        ]
    ):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        password_hash = generate_password_hash(password)
        now = get_current_time().isoformat()

        new_id = execute_query(
            """
            INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                first_name,
                last_name,
                birth_date,
                phone,
                passport_series,
                passport_number,
                password_hash,
                now,
            ),
        )

        # ID kamida 5 ta raqamdan iborat bo'lishi uchun
        if new_id and new_id < 10000:
            # ID raqamini kattaroq qilish uchun offset qo'shish
            execute_query(
                "UPDATE couriers SET id = ? WHERE id = ?", (new_id + 10000, new_id)
            )
            new_id = new_id + 10000

        flash(f"Yangi kuryer qo'shildi. ID: {new_id}", "success")
    except Exception as e:
        app_logger.error(f"Add courier error: {str(e)}")
        flash("Kuryer qo'shishda xatolik yuz berdi.", "error")

    return redirect(url_for("super_admin_dashboard"))


@app.route("/super-admin/delete-user", methods=["POST"])
def super_admin_delete_user():
    "Super admin delete user"
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    user_id = request.form.get("user_id")

    if not user_id:
        flash("Foydalanuvchi ID kiritilmagan.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        # Get user info first
        user_data = execute_query(
            "SELECT first_name, last_name, email FROM users WHERE id = ?",
            (user_id,),
            fetch_one=True,
        )

        if not user_data:
            flash("Foydalanuvchi topilmadi.", "error")
        else:
            # Delete user and related data
            execute_query("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
            execute_query("DELETE FROM favorites WHERE user_id = ?", (user_id,))
            execute_query("DELETE FROM ratings WHERE user_id = ?", (user_id,))
            execute_query("DELETE FROM users WHERE id = ?", (user_id,))

            app_logger.info(
                f"Super admin foydalanuvchini o'chirdi: {user_data.get('first_name')} {user_data.get('last_name')} (ID: {user_id})"
            )
            flash(
                f"Foydalanuvchi {user_data.get('first_name', 'N/A')} {user_data.get('last_name', 'N/A')} muvaffaqiyatli o'chirildi.",
                "success",
            )

    except Exception as e:
        app_logger.error(f"Super admin foydalanuvchini o'chirishda xatolik: {str(e)}")
        flash("Foydalanuvchini o'chirishda xatolik yuz berdi.", "error")


# General settings API endpoints
@app.route("/api/change-language", methods=["POST"])
def change_language():
    """Change interface language"""
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    language = data.get("language", "uz")

    if language not in SUPPORTED_LANGUAGES:
        return jsonify({"success": False, "message": "Invalid language"}), 400

    session["interface_language"] = language

    # Update database if user is logged in
    if session.get("user_id"):
        try:
            execute_query(
                "UPDATE users SET interface_language = ? WHERE id = ?",
                (language, session.get("user_id")),
            )
        except Exception as e:
            app_logger.error(f"Failed to update user language: {e}")

    return jsonify({"success": True, "message": "Language changed"})


@app.route("/api/change-theme", methods=["POST"])
def change_theme():
    """Change theme (light/dark)"""
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    is_dark = data.get("dark_theme", True)

    session["dark_theme"] = is_dark

    # Update database if user is logged in
    if session.get("user_id"):
        try:
            execute_query(
                "UPDATE users SET dark_theme = ? WHERE id = ?",
                (1 if is_dark else 0, session.get("user_id")),
            )
        except Exception as e:
            app_logger.error(f"Failed to update user theme: {e}")

    return jsonify({"success": True, "message": "Theme changed"})


@app.route("/api/change-font-size", methods=["POST"])
def change_font_size():
    """Change font size"""
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}
    font_size = data.get("font_size", "medium")

    if font_size not in ["small", "medium", "large"]:
        return jsonify({"success": False, "message": "Invalid font size"}), 400

    session["font_size"] = font_size

    # Update database if user is logged in
    if session.get("user_id"):
        try:
            execute_query(
                "UPDATE users SET font_size = ? WHERE id = ?",
                (font_size, session.get("user_id")),
            )
        except Exception as e:
            app_logger.error(f"Failed to update user font size: {e}")

    return jsonify({"success": True, "message": "Font size changed"})


@app.route("/api/save-settings", methods=["POST"])
def save_settings():
    """Save all settings"""
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify({"success": False, "message": "Authentication required"}), 401

    data = request.get_json() or {}

    # Update session
    if "language" in data:
        session["interface_language"] = data["language"]
    if "theme" in data:
        session["dark_theme"] = data["theme"] == "dark"
    if "font_size" in data:
        session["font_size"] = data["font_size"]
    if "notifications_enabled" in data:
        session["notifications_enabled"] = data["notifications_enabled"]
    if "email_notifications" in data:
        session["email_notifications"] = data["email_notifications"]
    if "sms_notifications" in data:
        session["sms_notifications"] = data["sms_notifications"]
    if "order_updates" in data:
        session["order_updates"] = data["order_updates"]

    # Update database if user is logged in
    if session.get("user_id"):
        try:
            execute_query(
                """UPDATE users SET 
                    interface_language = ?, 
                    dark_theme = ?, 
                    font_size = ? 
                    WHERE id = ?""",
                (
                    session.get("interface_language", "uz"),
                    1 if session.get("dark_theme", True) else 0,
                    session.get("font_size", "medium"),
                    session.get("user_id"),
                ),
            )
        except Exception as e:
            app_logger.error(f"Failed to update user settings: {e}")

    return jsonify({"success": True, "message": "Settings saved"})


@app.route("/api/reset-settings", methods=["POST"])
def reset_settings():
    """Reset settings to default"""
    if not (
        session.get("user_id")
        or session.get("staff_id")
        or session.get("courier_id")
        or session.get("super_admin")
    ):
        return jsonify({"success": False, "message": "Authentication required"}), 401

    # Reset session to defaults
    session["interface_language"] = "uz"
    session["dark_theme"] = True
    session["font_size"] = "medium"
    session["notifications_enabled"] = True
    session["email_notifications"] = True
    session["sms_notifications"] = False
    session["order_updates"] = True

    # Update database if user is logged in
    if session.get("user_id"):
        try:
            execute_query(
                """UPDATE users SET 
                    interface_language = 'uz', 
                    dark_theme = 0, 
                    font_size = 'medium' 
                    WHERE id = ?""",
                (session.get("user_id"),),
            )
        except Exception as e:
            app_logger.error(f"Failed to reset user settings: {e}")

    return jsonify({"success": True, "message": "Settings reset to default"})


# ================================
# YANGILIKLAR API ENDPOINTS
# ================================


@app.route("/api/news", methods=["GET"])
def api_news():
    """Get all active news items for ticker"""
    try:
        news_items = execute_query(
            "SELECT * FROM news WHERE is_active = 1 ORDER BY display_order ASC, created_at DESC",
            fetch_all=True,
        )
        return jsonify({"success": True, "news": news_items or []})
    except Exception as e:
        app_logger.error(f"API news error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to load news"}), 500


@app.route("/api/news", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def api_create_news():
    """Create new news item - Super admin only"""
    try:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        news_type = data.get("type", "news")
        image_url = data.get("image_url", "").strip()
        video_url = data.get("video_url", "").strip()
        is_active = bool(data.get("is_active", True))
        display_order = int(data.get("display_order", 0))
        show_in_ticker = 1 if bool(data.get("show_in_ticker", False)) else 0

        if not title:
            return jsonify({"success": False, "message": "Title is required"}), 400

        if news_type not in ["news", "advertisement"]:
            return jsonify({"success": False, "message": "Invalid news type"}), 400

        now = get_current_time().isoformat()
        # Ensure schema has show_in_ticker before insert
        try:
            cols = execute_query("PRAGMA table_info(news)", fetch_all=True)
            has_show = False
            if cols:
                for c in cols:
                    name = c[1] if isinstance(c, tuple) else c.get("name")
                    if name == "show_in_ticker":
                        has_show = True
                        break
            if not has_show:
                try:
                    execute_query(
                        "ALTER TABLE news ADD COLUMN show_in_ticker BOOLEAN DEFAULT 0"
                    )
                except Exception:
                    pass
        except Exception:
            pass

        if has_show:
            news_id = execute_query(
                """INSERT INTO news (title, content, type, image_url, video_url, is_active, display_order, show_in_ticker, created_by, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    content,
                    news_type,
                    image_url or None,
                    video_url or None,
                    1 if is_active else 0,
                    display_order,
                    show_in_ticker,
                    1,
                    now,
                    now,
                ),
            )
        else:
        news_id = execute_query(
            """INSERT INTO news (title, content, type, image_url, video_url, is_active, display_order, created_by, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                content,
                news_type,
                image_url or None,
                video_url or None,
                1 if is_active else 0,
                display_order,
                1,
                now,
                now,
            ),
        )

        # Sync to JSON file
        try:
            items = (
                execute_query(
                    "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
                    fetch_all=True,
                )
                or []
            )
            json_path = os.path.join(os.getcwd(), "data", "news.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"news": items, "metadata": {"last_updated": now}},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as _:
            pass

        return jsonify({"success": True, "message": "News item created", "id": news_id})

    except Exception as e:
        app_logger.error(f"Create news error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to create news"}), 500


@app.route("/api/news/<int:news_id>", methods=["PUT"])
@role_required("super_admin")
@csrf_protect
def api_update_news(news_id):
    """Update news item - Super admin only"""
    try:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        news_type = data.get("type", "news")
        image_url = data.get("image_url", "").strip()
        video_url = data.get("video_url", "").strip()
        is_active = bool(data.get("is_active", True))
        display_order = int(data.get("display_order", 0))
        show_in_ticker = 1 if bool(data.get("show_in_ticker", False)) else 0

        if not title:
            return jsonify({"success": False, "message": "Title is required"}), 400

        if news_type not in ["news", "advertisement"]:
            return jsonify({"success": False, "message": "Invalid news type"}), 400

        # Check if news exists
        existing = execute_query(
            "SELECT id FROM news WHERE id = ?", (news_id,), fetch_one=True
        )
        if not existing:
            return jsonify({"success": False, "message": "News not found"}), 404

        now = get_current_time().isoformat()
        # Check if show_in_ticker column exists
        has_show = False
        try:
            cols = execute_query("PRAGMA table_info(news)", fetch_all=True)
            if cols:
                for c in cols:
                    name = c[1] if isinstance(c, tuple) else c.get("name")
                    if name == "show_in_ticker":
                        has_show = True
                        break
        except Exception:
            has_show = False

        if has_show:
            execute_query(
                """UPDATE news SET title = ?, content = ?, type = ?, image_url = ?, video_url = ?, 
                   is_active = ?, display_order = ?, show_in_ticker = ?, updated_at = ? WHERE id = ?""",
                (
                    title,
                    content,
                    news_type,
                    image_url or None,
                    video_url or None,
                    1 if is_active else 0,
                    display_order,
                    show_in_ticker,
                    now,
                    news_id,
                ),
            )
        else:
        execute_query(
            """UPDATE news SET title = ?, content = ?, type = ?, image_url = ?, video_url = ?, 
               is_active = ?, display_order = ?, updated_at = ? WHERE id = ?""",
            (
                title,
                content,
                news_type,
                image_url or None,
                video_url or None,
                1 if is_active else 0,
                display_order,
                now,
                news_id,
            ),
        )

        # Sync to JSON file
        try:
            items = (
                execute_query(
                    "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
                    fetch_all=True,
                )
                or []
            )
            json_path = os.path.join(os.getcwd(), "data", "news.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"news": items, "metadata": {"last_updated": now}},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as _:
            pass

        return jsonify({"success": True, "message": "News item updated"})

    except Exception as e:
        app_logger.error(f"Update news error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to update news"}), 500


@app.route("/api/news/<int:news_id>", methods=["DELETE"])
@role_required("super_admin")
@csrf_protect
def api_delete_news(news_id):
    """Delete news item - Super admin only"""
    try:
        # Check if news exists
        existing = execute_query(
            "SELECT id FROM news WHERE id = ?", (news_id,), fetch_one=True
        )
        if not existing:
            return jsonify({"success": False, "message": "News not found"}), 404

        execute_query("DELETE FROM news WHERE id = ?", (news_id,))

        # Sync to JSON file
        try:
            items = (
                execute_query(
                    "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
                    fetch_all=True,
                )
                or []
            )
            now = get_current_time().isoformat()
            json_path = os.path.join(os.getcwd(), "data", "news.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"news": items, "metadata": {"last_updated": now}},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as _:
            pass

        return jsonify({"success": True, "message": "News item deleted"})

    except Exception as e:
        app_logger.error(f"Delete news error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to delete news"}), 500


@app.route("/api/news/admin", methods=["GET"])
@role_required("super_admin")
def api_admin_news():
    """Get all news for admin management - Super admin only"""
    try:
        # Ensure news table exists (first run safety)
        try:
            execute_query(
                """
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    type TEXT DEFAULT 'news' CHECK (type IN ('news','advertisement')),
                    is_active BOOLEAN DEFAULT 1,
                    display_order INTEGER DEFAULT 0,
                    image_url TEXT,
                    video_url TEXT,
                    show_in_ticker BOOLEAN DEFAULT 0,
                    created_by INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        except Exception:
            pass

        news_items = execute_query(
            "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
            fetch_all=True,
        )

        # Auto-import from data/news.json if DB is empty and JSON exists
        if not news_items:
            try:
                json_path = os.path.join(os.getcwd(), "data", "news.json")
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    items = raw.get("news") if isinstance(raw, dict) else raw
                    if isinstance(items, list) and items:
                        now = get_current_time().isoformat()
                        order_counter = 0
                        for it in items:
                            try:
                                title = (
                                    it.get("title") or it.get("name") or ""
                                ).strip()
                                if not title:
                                    continue
                                content = (
                                    it.get("description") or it.get("content") or ""
                                ).strip()
                                image_url = (
                                    it.get("image_url") or it.get("image") or None
                                )
                                video_url = (
                                    it.get("video_url")
                                    or it.get("video")
                                    or it.get("youtube_url")
                                    or None
                                )
                                news_type = it.get("type") or (
                                    "advertisement" if it.get("is_ad") else "news"
                                )
                                is_active = 1 if (it.get("published", True)) else 0
                                display_order = int(
                                    it.get("display_order", order_counter)
                                )
                                order_counter += 1

                                # Insert row
                                try:
                                    execute_query(
                                        """INSERT INTO news (title, content, type, image_url, video_url, is_active, display_order, created_by, created_at, updated_at)
                                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                        (
                                            title,
                                            content,
                                            (
                                                news_type
                                                if news_type
                                                in ["news", "advertisement"]
                                                else "news"
                                            ),
                                            image_url,
                                            video_url,
                                            is_active,
                                            display_order,
                                            1,
                                            now,
                                            now,
                                        ),
                                    )
                                except Exception:
                                    # If show_in_ticker exists, ignore here; default 0
                                    pass
                            except Exception:
                                continue

                        # Reload after import
                        news_items = execute_query(
                            "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
                            fetch_all=True,
                        )
            except Exception as imp_err:
                app_logger.warning(f"News JSON import skipped: {imp_err}")

        # Seed with a few defaults if still empty (first-time setup convenience)
        if not news_items:
            try:
                now = get_current_time().isoformat()
                defaults = [
                    (
                        "🎉 PRO-OBUV yangiliklari",
                        "Do'konimizda yangilanishlar!",
                        "news",
                        1,
                        0,
                        None,
                        None,
                        now,
                        now,
                    ),
                    (
                        "🔥 Chegirmalar",
                        "Ayrim mahsulotlarda chegirmalar mavjud.",
                        "advertisement",
                        1,
                        1,
                        None,
                        None,
                        now,
                        now,
                    ),
                ]
                for d in defaults:
                    try:
                        execute_query(
                            """INSERT INTO news (title, content, type, is_active, display_order, image_url, video_url, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            d,
                        )
                    except Exception:
                        continue
                news_items = execute_query(
                    "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
                    fetch_all=True,
                )
            except Exception as seed_err:
                app_logger.warning(f"News seed skipped: {seed_err}")
        return jsonify({"success": True, "news": news_items or []})
    except Exception as e:
        app_logger.error(f"Admin news API error: {str(e)}")
        return jsonify({"success": False, "message": "Failed to load news"}), 500


@app.route("/api/news/toggle/<int:news_id>", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def api_toggle_news(news_id):
    """Toggle news active status - Super admin only"""
    try:
        # Get current status
        news_item = execute_query(
            "SELECT is_active FROM news WHERE id = ?", (news_id,), fetch_one=True
        )
        if not news_item:
            return jsonify({"success": False, "message": "News not found"}), 404

        # Toggle status
        new_status = 0 if news_item["is_active"] else 1
        now = get_current_time().isoformat()
        execute_query(
            "UPDATE news SET is_active = ?, updated_at = ? WHERE id = ?",
            (new_status, now, news_id),
        )

        status_text = "activated" if new_status else "deactivated"
        return jsonify(
            {
                "success": True,
                "message": f"News item {status_text}",
                "is_active": bool(new_status),
            }
        )

    except Exception as e:
        app_logger.error(f"Toggle news error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Failed to toggle news status"}),
            500,
        )


@app.route("/admin/news")
@role_required("super_admin")
def admin_news_management():
    """Yangiliklar boshqaruvi sahifasi - Super admin only"""
    try:
        # CSRF token yaratish
        csrf_token = generate_csrf_token()
        return render_template("admin/news_management.html", csrf_token=csrf_token)
    except Exception as e:
        app_logger.error(f"News management page error: {str(e)}")
        flash("Sahifani yuklashda xatolik yuz berdi", "danger")
        return redirect(url_for("dashboard"))


@app.route("/admin/news-ticker")
@role_required("super_admin")
def admin_news_ticker_management():
    """Yangiliklar tasmasi boshqaruvi sahifasi - Super admin only"""
    try:
        csrf_token = generate_csrf_token()
        return render_template(
            "admin/news_ticker_management.html", csrf_token=csrf_token
        )
    except Exception as e:
        app_logger.error(f"News ticker management page error: {str(e)}")
        flash("Sahifani yuklashda xatolik yuz berdi", "danger")
        return redirect(url_for("super_admin_dashboard"))


@app.route("/api/news/ticker", methods=["GET"])
@role_required("super_admin")
def api_admin_news_ticker():
    """Get only items marked for ticker - Super admin only"""
    try:
        # Ensure column exists
        try:
            cols = execute_query("PRAGMA table_info(news)", fetch_all=True)
            has_show = False
            if cols:
                for c in cols:
                    name = c[1] if isinstance(c, tuple) else c.get("name")
                    if name == "show_in_ticker":
                        has_show = True
                        break
            if not has_show:
                execute_query(
                    "ALTER TABLE news ADD COLUMN show_in_ticker BOOLEAN DEFAULT 0"
                )
        except Exception:
            pass

        items = execute_query(
            "SELECT * FROM news WHERE COALESCE(show_in_ticker,0)=1 ORDER BY display_order ASC, created_at DESC",
            fetch_all=True,
        )
        return jsonify({"success": True, "news": items or []})
    except Exception as e:
        app_logger.error(f"Admin news ticker API error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Failed to load ticker items"}),
            500,
        )


@app.route("/api/news/ticker/toggle/<int:news_id>", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def api_toggle_news_ticker(news_id):
    """Toggle show_in_ticker flag - Super admin only"""
    try:
        row = execute_query(
            "SELECT show_in_ticker FROM news WHERE id = ?", (news_id,), fetch_one=True
        )
        if not row:
            return jsonify({"success": False, "message": "News not found"}), 404
        current = row[0] if isinstance(row, tuple) else row.get("show_in_ticker", 0)
        new_val = 0 if current else 1
        now = get_current_time().isoformat()
        execute_query(
            "UPDATE news SET show_in_ticker = ?, updated_at = ? WHERE id = ?",
            (new_val, now, news_id),
        )
        return jsonify(
            {
                "success": True,
                "message": "Ticker holati yangilandi",
                "show_in_ticker": bool(new_val),
            }
        )
    except Exception as e:
        app_logger.error(f"Toggle news ticker error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Failed to toggle ticker flag"}),
            500,
        )


@app.route("/admin/upload-news-media", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def upload_news_media():
    """Upload media files for news - Super admin only"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Fayl tanlanmagan"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "message": "Fayl tanlanmagan"}), 400

        # Check file type
        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm", "mov"}
        if file and "." in file.filename:
            ext = file.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Faqat rasm (PNG, JPG, JPEG, GIF, WEBP) va video (MP4, WEBM, MOV) fayllari qo'llab-quvvatlanadi",
                        }
                    ),
                    400,
                )

        # Create uploads directory if not exists
        import os

        upload_folder = os.path.join(os.getcwd(), "static", "uploads", "news")
        os.makedirs(upload_folder, exist_ok=True)

        # Generate unique filename
        import uuid
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}.{ext}"
        filepath = os.path.join(upload_folder, filename)

        # Save file
        file.save(filepath)

        # Return URL
        file_url = f"/static/uploads/news/{filename}"
        file_type = "video" if ext in {"mp4", "webm", "mov"} else "image"

        return jsonify(
            {
                "success": True,
                "file_url": file_url,
                "file_type": file_type,
                "message": "Fayl muvaffaqiyatli yuklandi",
            }
        )

    except Exception as e:
        app_logger.error(f"Upload news media error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Fayl yuklashda xatolik yuz berdi"}),
            500,
        )


@app.route("/admin/card-management")
@role_required("super_admin")
def admin_card_management():
    """Card payment management page - Super admin only"""
    try:
        return render_template("admin/card_management.html")
    except Exception as e:
        app_logger.error(f"Card management page error: {str(e)}")
        flash("Sahifani yuklashda xatolik yuz berdi", "danger")
        return redirect(url_for("super_admin_dashboard"))


@app.route("/api/card-data", methods=["GET"])
@role_required("super_admin")
def api_get_card_data():
    """Get card payment data - Super admin only"""
    try:
        # Get card data from database
        card_data = execute_query(
            "SELECT * FROM card_payment_settings WHERE id = 1", fetch_one=True
        )

        if card_data:
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "card_number": card_data.get("card_number", ""),
                        "card_name": card_data.get("card_name", ""),
                        "click_qr_url": card_data.get("click_qr_url", ""),
                        "payme_qr_url": card_data.get("payme_qr_url", ""),
                    },
                }
            )
        else:
            return jsonify({"success": True, "data": None})

    except Exception as e:
        app_logger.error(f"Get card data error: {str(e)}")
        return jsonify({"success": False, "message": "Ma'lumot yuklashda xatolik"}), 500


@app.route("/api/save-card-data", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def api_save_card_data():
    """Save card payment data - Super admin only"""
    try:
        data = request.get_json() or {}
        card_number = data.get("card_number", "").strip()
        card_name = data.get("card_name", "").strip()
        click_qr_url = data.get("click_qr_url", "").strip()
        payme_qr_url = data.get("payme_qr_url", "").strip()

        if not card_number or not card_name:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Karta raqami va egasi ismi kiritilishi shart",
                    }
                ),
                400,
            )

        # Check if record exists
        existing = execute_query(
            "SELECT id FROM card_payment_settings WHERE id = 1", fetch_one=True
        )

        now = get_current_time().isoformat()

        if existing:
            # Update existing record
            execute_query(
                """UPDATE card_payment_settings 
                   SET card_number = ?, card_name = ?, click_qr_url = ?, payme_qr_url = ?, updated_at = ? 
                   WHERE id = 1""",
                (
                    card_number,
                    card_name,
                    click_qr_url or None,
                    payme_qr_url or None,
                    now,
                ),
            )
        else:
            # Insert new record
            execute_query(
                """INSERT INTO card_payment_settings (id, card_number, card_name, click_qr_url, payme_qr_url, created_at, updated_at) 
                   VALUES (1, ?, ?, ?, ?, ?, ?)""",
                (
                    card_number,
                    card_name,
                    click_qr_url or None,
                    payme_qr_url or None,
                    now,
                    now,
                ),
            )

        return jsonify({"success": True, "message": "Karta ma'lumotlari saqlandi"})

    except Exception as e:
        app_logger.error(f"Save card data error: {str(e)}")
        return (
            jsonify({"success": False, "message": "Ma'lumotlarni saqlashda xatolik"}),
            500,
        )


@app.route("/api/upload-qr", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def api_upload_qr():
    """Upload QR code files - Super admin only"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Fayl tanlanmagan"}), 400

        file = request.files["file"]
        qr_type = request.form.get("type", "unknown")

        if file.filename == "":
            return jsonify({"success": False, "message": "Fayl tanlanmagan"}), 400

        # Check file type
        allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
        if file and "." in file.filename:
            ext = file.filename.rsplit(".", 1)[1].lower()
            if ext not in allowed_extensions:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Faqat rasm fayllari qabul qilinadi",
                        }
                    ),
                    400,
                )

        # Create uploads directory
        upload_folder = os.path.join(os.getcwd(), "static", "uploads", "qr")
        os.makedirs(upload_folder, exist_ok=True)

        # Generate unique filename
        import uuid
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{qr_type}_{timestamp}_{unique_id}.{ext}"
        filepath = os.path.join(upload_folder, filename)

        # Save file
        file.save(filepath)

        # Return URL
        file_url = f"/static/uploads/qr/{filename}"

        return jsonify(
            {
                "success": True,
                "url": file_url,
                "message": "QR kod muvaffaqiyatli yuklandi",
            }
        )

    except Exception as e:
        app_logger.error(f"Upload QR error: {str(e)}")
        return jsonify({"success": False, "message": "O'chirish xatoligi"}), 500


@app.route("/admin/360-management")
@role_required("super_admin")
def admin_360_management():
    """360 degree photos management page - Super admin only"""
    try:
        return render_template("admin/360_management.html")
    except Exception as e:
        app_logger.error(f"360 management page error: {str(e)}")
        flash("Sahifani yuklashda xatolik yuz berdi", "danger")
        return redirect(url_for("super_admin_dashboard"))


@app.route("/api/360-photos", methods=["GET"])
@role_required("super_admin")
def api_get_360_photos():
    """Get all 360 photos - Super admin only"""
    try:
        photos = execute_query(
            "SELECT * FROM photos_360 ORDER BY display_order ASC, created_at DESC",
            fetch_all=True,
        )
        return jsonify({"success": True, "photos": photos or []})
    except Exception as e:
        app_logger.error(f"Get 360 photos error: {str(e)}")
        return (
            jsonify({"success": False, "message": "360° rasmlarni yuklashda xatolik"}),
            500,
        )


@app.route("/api/upload-360-photos", methods=["POST"])
@role_required("super_admin")
def api_upload_360_photos():
    """Upload 360 photos - Super admin only"""
    try:
        if "files" not in request.files:
            return jsonify({"success": False, "message": "Fayllar tanlanmagan"}), 400

        files = request.files.getlist("files")
        if not files:
            return jsonify({"success": False, "message": "Fayllar tanlanmagan"}), 400

        # Create uploads directory
        upload_folder = os.path.join(os.getcwd(), "static", "uploads", "360")
        os.makedirs(upload_folder, exist_ok=True)

        uploaded_files = []
        now = get_current_time().isoformat()

        for file in files:
            if file.filename == "":
                continue

            # Check file type
            allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
            if file and "." in file.filename:
                ext = file.filename.rsplit(".", 1)[1].lower()
                if ext not in allowed_extensions:
                    continue

            # Generate unique filename
            import uuid
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"360_{timestamp}_{unique_id}.{ext}"
            filepath = os.path.join(upload_folder, filename)

            # Save file
            file.save(filepath)

            # Save to database
            file_url = f"/static/uploads/360/{filename}"
            title = f"360° Rasm - {datetime.now().strftime('%d.%m.%Y %H:%M')}"

            photo_id = execute_query(
                """INSERT INTO photos_360 (title, image_url, is_active, display_order, created_by, created_at, updated_at)
                   VALUES (?, ?, 0, 0, 1, ?, ?)""",
                (title, file_url, now, now),
            )

            uploaded_files.append(
                {"id": photo_id, "title": title, "image_url": file_url}
            )

        if uploaded_files:
            return jsonify(
                {
                    "success": True,
                    "message": f"{len(uploaded_files)} ta 360° rasm yuklandi",
                    "uploaded": uploaded_files,
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Hech qanday fayl yuklanmadi"}),
                400,
            )

    except Exception as e:
        app_logger.error(f"Upload 360 photos error: {str(e)}")
        return (
            jsonify({"success": False, "message": "360° rasm yuklashda xatolik"}),
            500,
        )


@app.route("/api/set-active-360-photo/<int:photo_id>", methods=["POST"])
@role_required("super_admin")
@csrf_protect
def api_set_active_360_photo(photo_id):
    """Set 360 photo as active - Super admin only"""
    try:
        # First deactivate all photos
        execute_query("UPDATE photos_360 SET is_active = 0")

        # Then activate the selected photo
        now = get_current_time().isoformat()
        execute_query(
            "UPDATE photos_360 SET is_active = 1, updated_at = ? WHERE id = ?",
            (now, photo_id),
        )

        return jsonify({"success": True, "message": "360° rasm faollashtirildi"})

    except Exception as e:
        app_logger.error(f"Set active 360 photo error: {str(e)}")
        return jsonify({"success": False, "message": "Faollashtirish xatoligi"}), 500


@app.route("/api/delete-360-photo/<int:photo_id>", methods=["DELETE"])
@role_required("super_admin")
@csrf_protect
def api_delete_360_photo(photo_id):
    """Delete 360 photo - Super admin only"""
    try:
        # Get photo info to delete file
        photo = execute_query(
            "SELECT image_url FROM photos_360 WHERE id = ?", (photo_id,), fetch_one=True
        )

        if photo:
            # Try to delete the file
            try:
                file_path = photo["image_url"].replace("/static/", "static/")
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as file_err:
                app_logger.warning(f"Could not delete 360 photo file: {file_err}")

        # Delete from database
        execute_query("DELETE FROM photos_360 WHERE id = ?", (photo_id,))

        return jsonify({"success": True, "message": "360° rasm o'chirildi"})

    except Exception as e:
        app_logger.error(f"Delete 360 photo error: {str(e)}")
        return jsonify({"success": False, "message": "O'chirish xatoligi"}), 500


@app.route("/360-room")
def user_360_room():
    """360 Room page for users - Public"""
    try:
        # Get active 360 photos
        photos_360 = execute_query(
            "SELECT id, title, image_url, is_active, created_at FROM photos_360 WHERE is_active = 1 ORDER BY created_at DESC",
            fetch_all=True,
        )

        # If no active photos, get all photos for demo
        if not photos_360:
            photos_360 = execute_query(
                "SELECT id, title, image_url, is_active, created_at FROM photos_360 ORDER BY created_at DESC LIMIT 5",
                fetch_all=True,
            )

        return render_template("360_room.html", photos_360=photos_360 or [])
    except Exception as e:
        app_logger.error(f"360 room page error: {str(e)}")
        flash("Sahifani yuklashda xatolik yuz berdi", "danger")
        return redirect(url_for("index"))


@app.route("/data/<path:filename>")
def serve_data_file(filename):
    """Serve files from data directory (for news.json etc.)"""
    try:
        from flask import send_from_directory

        return send_from_directory("data", filename)
    except Exception as e:
        app_logger.error(f"Error serving data file {filename}: {str(e)}")
        return jsonify({"error": "File not found"}), 404


# Flask app runner
if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000
    print(f"\nDastur quyidagi URLda ishga tushdi: http://{host}:{port}\n")
    app.run(debug=True, host=host, port=port)
