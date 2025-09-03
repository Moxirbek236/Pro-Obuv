import time
import string
import secrets as secrets_module

# Global start time tracking
start_time = time.time()

# Cleanup function
def cleanup_resources():
    """Resource cleanup on app shutdown"""
    try:
        if 'executor' in globals():
            executor.shutdown(wait=True)
        if 'db_pool' in globals() and hasattr(db_pool, 'connections'):
            for conn in db_pool.connections:
                try:
                    conn.close()
                except:
                    pass
        if 'app_logger' in globals():
            app_logger.info("Resources cleaned up successfully")
    except Exception as e:
        if 'app_logger' in globals():
            app_logger.error(f"Cleanup error: {str(e)}")

import atexit
atexit.register(cleanup_resources)

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, datetime, json, uuid, secrets
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_compress import Compress
import pytz
import qrcode
from io import BytesIO
import base64
import requests
from functools import wraps
import threading
from contextlib import contextmanager
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib
from collections import defaultdict
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.profiler import ProfilerMiddleware
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Redis import - optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Environment variables yuklash
load_dotenv()

app = Flask(__name__)

# Universal configuration class
class Config:
    """Universal dastur konfiguratsiyasi"""

    # Environment detection
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
    IS_DEVELOPMENT = ENVIRONMENT == 'development'
    IS_PRODUCTION = ENVIRONMENT == 'production'

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database.sqlite3')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLite-specific engine options
    if DATABASE_URL.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {
                'check_same_thread': False,
                'timeout': 60
            }
        }
    else:
        # PostgreSQL options (if using PostgreSQL)
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }

    # Security configuration
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets_module.token_urlsafe(32))
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7200
    WTF_CSRF_ENABLED = True

    # File upload configuration
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # JSON configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = IS_DEVELOPMENT

    # Cache configuration
    SEND_FILE_MAX_AGE_DEFAULT = 31536000 if IS_PRODUCTION else 300
    REDIS_URL = os.environ.get('REDIS_URL', 'memory://')

    # External APIs
    YANDEX_GEOCODER_API = os.environ.get('YANDEX_GEOCODER_API', '')
    GOOGLE_MAPS_API = os.environ.get('GOOGLE_MAPS_API', '')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '1b077296f67499a12ee28ce232bb48221d29be14')

    # Localization
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'uz')
    SUPPORTED_LANGUAGES = ['uz', 'ru', 'en', 'tr', 'ar']
    DEFAULT_CURRENCY = os.environ.get('DEFAULT_CURRENCY', 'UZS')
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Tashkent')

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
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE_MAX_SIZE = int(os.environ.get('LOG_FILE_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '5'))

    # Performance
    THREAD_POOL_MAX_WORKERS = int(os.environ.get('THREAD_POOL_MAX_WORKERS', '10'))
    DB_POOL_MAX_CONNECTIONS = int(os.environ.get('DB_POOL_MAX_CONNECTIONS', '20'))

    # Admin credentials
    SUPER_ADMIN_USERNAME = os.environ.get('SUPER_ADMIN_USERNAME', 'masteradmin')
    SUPER_ADMIN_PASSWORD = os.environ.get('SUPER_ADMIN_PASSWORD', 'SuperAdmin2025!@#$%')

# Apply configuration
app.config.from_object(Config)

# Professional middleware stack
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# CORS support
CORS(app, origins=['*'], methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Compression
Compress(app)

# Rate limiting with universal configuration
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[
        f"{Config.RATE_LIMIT_DAILY} per day",
        f"{Config.RATE_LIMIT_HOURLY} per hour",
        f"{Config.RATE_LIMIT_MINUTE} per minute"
    ],
    storage_uri=Config.REDIS_URL
)

# Performance profiling (faqat debug rejimida)
if os.environ.get('FLASK_ENV') == 'development':
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

# Upload papkasini yaratish
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logs papkasini yaratish
os.makedirs('logs', exist_ok=True)

# Advanced logging konfiguratsiyasi - funksiyani oldinroq e'lon qilish
def setup_logging():
    """Professional logging setup with structured logging"""
    # Detailed formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    )

    # Simple formatter
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Rotating file handler (maksimal 10MB, 5 ta backup)
        file_handler = RotatingFileHandler('logs/restaurant.log', maxBytes=10485760, backupCount=5)
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.INFO)

        # Error file handler
        error_handler = RotatingFileHandler('logs/errors.log', maxBytes=10485760, backupCount=5)
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)

        # Console handler - faqat development uchun
        console_handler = logging.StreamHandler()
        if Config.IS_DEVELOPMENT:
            console_handler.setFormatter(simple_formatter)
            console_handler.setLevel(logging.INFO)
        else:
            console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
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
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.WARNING)

        return logging.getLogger('restaurant_app')

    except Exception as e:
        app_logger.error(f"Logging setup failed: {e}")
        # Fallback logging
        print(f"Logging setup failed: {e}")
        return logging.getLogger('restaurant_app')

# Logging ni sozlash
app_logger = setup_logging()

# Location service instance - xatolik bo'lsa fallback yaratish
try:
    from location_service import LocationService
    location_service = LocationService()
    app_logger.info("Location service muvaffaqiyatli yuklandi")
except (ImportError, Exception) as e:
    app_logger.warning(f"Location service yuklanmadi: {str(e)}")
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
        """Redis connection (agar mavjud bo'lsa)"""
        try:
            if not REDIS_AVAILABLE:
                return

            redis_url = os.environ.get('REDIS_URL')
            if redis_url and not redis_url.startswith('memory'):
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                app_logger.info("Redis cache tizimi ulandi")
        except Exception as e:
            app_logger.warning(f"Redis ulanmadi, memory cache ishlatiladi: {str(e)}")
            self.redis_client = None

    def get(self, key, default=None):
        """Cache dan ma'lumot olish"""
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
        """Cache ga ma'lumot saqlash"""
        try:
            if self.redis_client:
                self.redis_client.setex(f"restaurant:{key}", ttl, json.dumps(value, default=str))

            # Memory cache ga ham saqlash
            with self.cache_lock:
                self.memory_cache[key] = value
                self.cache_timestamps[key] = time.time()

                # Memory cache ni tozalash (maksimal 1000 ta element)
                if len(self.memory_cache) > 1000:
                    oldest_key = min(self.cache_timestamps.keys(), key=lambda k: self.cache_timestamps[k])
                    del self.memory_cache[oldest_key]
                    del self.cache_timestamps[oldest_key]
        except Exception as e:
            app_logger.error(f"Cache set error: {str(e)}")

    def delete(self, key):
        """Cache dan o'chirish"""
        try:
            if self.redis_client:
                self.redis_client.delete(f"restaurant:{key}")

            with self.cache_lock:
                self.memory_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
        except Exception as e:
            app_logger.error(f"Cache delete error: {str(e)}")

# Global cache manager
cache_manager = CacheManager()

# Rate limiting
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, identifier, max_requests=100, window=3600):
        """Rate limiting tekshiruvi"""
        current_time = time.time()

        with self.lock:
            # Eski so'rovlarni tozalash
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < window
            ]

            # Yangi so'rovni qo'shish
            if len(self.requests[identifier]) < max_requests:
                self.requests[identifier].append(current_time)
                return True

            return False

rate_limiter = RateLimiter()

# Thread pool for async operations with configurable workers
executor = ThreadPoolExecutor(max_workers=Config.THREAD_POOL_MAX_WORKERS)

# Database fayl yo'lini to'g'rilash
DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")

import logging
from logging.handlers import RotatingFileHandler, SMTPHandler



# Global error handlers
@app.errorhandler(404)
def not_found_error(error):
    app_logger.warning(f"404 Error: {request.url}")
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({"error": "Not found", "code": 404}), 404

    # Error template mavjudligini tekshirish
    try:
        return render_template('error.html', error_code=404, error_message="Sahifa topilmadi"), 404
    except:
        return f"""
        <h1>404 - Sahifa topilmadi</h1>
        <p>So'ralgan sahifa mavjud emas.</p>
        <a href="/">Bosh sahifaga qaytish</a>
        """, 404

@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"500 Error: {str(error)} - URL: {request.url}")
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error", "code": 500}), 500

    try:
        return render_template('error.html', error_code=500, error_message="Server xatoligi"), 500
    except:
        return f"""
        <h1>500 - Server xatoligi</h1>
        <p>Ichki server xatoligi yuz berdi.</p>
        <a href="/">Bosh sahifaga qaytish</a>
        """, 500

@app.errorhandler(429)
def rate_limit_error(error):
    app_logger.warning(f"Rate limit exceeded: {request.remote_addr}")
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({"error": "Rate limit exceeded", "code": 429}), 429

    try:
        return render_template('error.html', error_code=429, error_message="Juda ko'p so'rov"), 429
    except:
        return f"""
        <h1>429 - Juda ko'p so'rov</h1>
        <p>Juda ko'p so'rov yuborildi. Biroz kuting.</p>
        <a href="/">Bosh sahifaga qaytish</a>
        """, 429

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    app_logger.error(f"Unhandled exception: {str(e)} - URL: {request.url}")

    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            "error": "Unexpected error occurred",
            "code": 500,
            "details": str(e) if Config.IS_DEVELOPMENT else "Internal server error"
        }), 500

    try:
        return render_template('error.html',
                             error_code=500,
                             error_message="Kutilmagan xatolik yuz berdi"), 500
    except:
        return f"""
        <h1>Kutilmagan xatolik</h1>
        <p>Dasturda kutilmagan xatolik yuz berdi.</p>
        <a href="/">Bosh sahifaga qaytish</a>
        """, 500

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
                self.request_times.append({
                    'duration': duration,
                    'endpoint': endpoint,
                    'timestamp': time.time(),
                    'status_code': status_code
                })

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
                        req for req in self.request_times
                        if req['timestamp'] > cutoff_time
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

            durations = [req['duration'] for req in self.request_times]
            return {
                'avg_response_time': sum(durations) / len(durations),
                'max_response_time': max(durations),
                'min_response_time': min(durations),
                'total_requests': len(durations)
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
    """So'rov boshlanishida xavfsiz pre-processing"""
    try:
        # Request time tracking - g obyektiga saqlash
        g.start_time = time.time()

        # Session ni tekshirish va tuzatish
        if not session.get('session_id') or session.get('session_id') == 'None':
            session['session_id'] = get_session_id()

        # Database connection test
        if not hasattr(g, 'db_test_done'):
            try:
                test_conn = get_db()
                test_conn.execute("SELECT 1")
                test_conn.close()
                g.db_test_done = True
            except Exception as db_error:
                app_logger.error(f"Database connection test failed: {str(db_error)}")

    except Exception as e:
        app_logger.error(f"Before request error: {str(e)}")
        # Error bo'lsa ham davom ettirish

@app.after_request
def after_request(response):
    """Request tugagandan keyin ishlaydigan function"""
    try:
        end_time = time.time()
        duration = end_time - getattr(g, 'start_time', end_time)

        # Performance monitoring - xavfsiz tekshirish
        try:
            if hasattr(performance_monitor, 'record_request') and callable(performance_monitor.record_request):
                performance_monitor.record_request(duration, request.endpoint or 'unknown', response.status_code)
        except Exception:
            # Performance monitoring xatolikni e'tiborsiz qoldirish
            pass

        # Security headers qo'shish
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Cache headers faqat static files uchun emas
        if not request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        if Config.IS_PRODUCTION:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    except Exception as e:
        # Silent pass - xavfsizlik uchun
        pass

    return response



AVG_PREP_MINUTES = int(os.environ.get("AVG_PREP_MINUTES", "7"))
# o'rtacha tayyorlanish vaqti (daqiqalarda)

# Initialize SQLAlchemy only if using PostgreSQL
if Config.DATABASE_URL.startswith('postgresql'):
    db = SQLAlchemy(app)
else:
    db = None  # Use custom SQLite connection pool instead

# O'zbekiston vaqt zonasi
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

def get_current_time():
    return datetime.datetime.now(TASHKENT_TZ)

# Database connection pool
class DatabasePool:
    def __init__(self, db_path, max_connections=20):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()
        self._init_pool()

    def _init_pool(self):
        """Connection pool ni ishga tushirish"""
        for _ in range(5):  # Boshlang'ich 5 ta connection
            conn = self._create_connection()
            if conn:
                self.connections.append(conn)

    def _create_connection(self):
        """Yangi database connection yaratish"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0,
                    isolation_level=None
                )
                conn.row_factory = sqlite3.Row

                # SQLite optimallashtirish sozlamalari - xavfsiz
                try:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA cache_size=5000")
                    conn.execute("PRAGMA temp_store=MEMORY")
                    conn.execute("PRAGMA foreign_keys=ON")
                    conn.execute("PRAGMA busy_timeout=15000")
                except Exception as pragma_error:
                    app_logger.warning(f"PRAGMA settings failed: {str(pragma_error)}")

                # Connection test
                conn.execute("SELECT 1").fetchone()
                return conn

            except Exception as e:
                app_logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    app_logger.critical(f"Database connection yaratishda XATOLIK: {str(e)}")
                    return None
                time.sleep(0.5 * (attempt + 1))

    @contextmanager
    def get_connection(self):
        """Context manager orqali connection olish"""
        conn = None
        try:
            with self.lock:
                if self.connections:
                    conn = self.connections.pop()
                else:
                    conn = self._create_connection()

            if not conn:
                raise Exception("Database connection olinmadi")

            yield conn

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise e
        finally:
            if conn:
                try:
                    with self.lock:
                        if len(self.connections) < self.max_connections:
                            self.connections.append(conn)
                        else:
                            conn.close()
                except:
                    pass

# Global database pool with configurable max connections
db_pool = DatabasePool(DB_PATH, Config.DB_POOL_MAX_CONNECTIONS)

def get_db():
    """Legacy support uchun"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Optimized database operations
def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Optimizatsiya qilingan database so'rovi"""
    with db_pool.get_connection() as conn:
        try:
            cur = conn.cursor()

            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)

            if fetch_one:
                result = cur.fetchone()
                # Ensure result is a dictionary-like object for easier access
                if result and hasattr(result, 'keys'):
                    return dict(zip(result.keys(), result))
                elif result:
                    # Fallback for tuple results if row_factory is not set correctly
                    return result
                return None
            elif fetch_all:
                # fetch_all uchun alohida result olish
                all_results = cur.fetchall()
                if all_results and hasattr(all_results[0], 'keys'):
                    return [dict(zip(row.keys(), row)) for row in all_results]
                else:
                    return all_results or []
            else:
                conn.commit()
                return cur.lastrowid
        except Exception as e:
            conn.rollback()
            raise e

def execute_many(query, params_list):
    """Bulk operations uchun optimizatsiya"""
    with db_pool.get_connection() as conn:
        try:
            cur = conn.cursor()
            cur.executemany(query, params_list)
            conn.commit()
            return cur.rowcount
        except Exception as e:
            conn.rollback()
            raise e

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Foydalanuvchilar jadvali
    cur.execute("""
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
            dark_theme BOOLEAN DEFAULT 0
        );
    """)

    # Xodimlar jadvali
    cur.execute("""
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
    """)

    # Kuryerlar jadvali
    cur.execute("""
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
    """)

    # Buyurtmalar jadvali (yangilangan)
    cur.execute("""
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
    """)

    # Tikketlar hisoblagich
    cur.execute("""
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        );
    """)
    cur.execute("INSERT OR IGNORE INTO counters (name, value) VALUES ('ticket', 10000);")

    # Menyu mahsulotlari (yangilangan)
    cur.execute("""
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
            created_at TEXT NOT NULL
        );
    """)

    # Sevimlilar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id),
            UNIQUE(user_id, menu_item_id)
        );
    """)

    # Savatcha jadvali (yangilangan)
    cur.execute("""
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
    """)

    # Buyurtma tafsilotlari jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    """)

    # Baholar jadvali
    cur.execute("""
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
    """)

    # Savollar jadvali
    cur.execute("""
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
    """)

    # Cheklar jadvali
    cur.execute("""
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
    """)

    # Filiallar jadvali
    cur.execute("""
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
    """)

    # Boshlang'ich taomlar qo'shish
    cur.execute("SELECT COUNT(*) FROM menu_items")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        sample_items = [
            ('Osh', 25000, 'food', 'An\'anaviy o\'zbek taomi, guruch va go\'sht bilan', '/static/images/osh.jpg', 1, 50, 0, 4.5, 0.0, now),
            ('Manti', 20000, 'food', 'Bug\'da pishirilgan go\'shtli manti', '/static/images/manti.jpg', 1, 30, 0, 4.8, 5.0, now),
            ('Shashlik', 30000, 'food', 'Mangalda pishirilgan mazali shashlik', '/static/images/shashlik.jpg', 1, 25, 0, 4.7, 0.0, now),
            ('Lagmon', 22000, 'food', 'Qo\'l tortmasi bilan tayyorlangan lagmon', '/static/images/lagmon.jpg', 1, 40, 0, 4.6, 10.0, now),
            ('Choy', 5000, 'drink', 'Issiq qora choy', '/static/images/choy.jpg', 1, 100, 0, 4.2, 0.0, now),
            ('Qora choy', 6000, 'drink', 'O\'zbek an\'anaviy choy', '/static/images/qora_choy.jpg', 1, 80, 0, 4.3, 0.0, now),
            ('Kompot', 8000, 'drink', 'Mevali kompot', '/static/images/kompot.jpg', 1, 60, 0, 4.1, 15.0, now),
            ('Coca Cola', 10000, 'drink', 'Sovuq ichimlik', '/static/images/coca_cola.jpg', 1, 70, 0, 4.0, 0.0, now),
        ]
        cur.executemany("INSERT INTO menu_items (name, price, category, description, image_url, available, stock_quantity, orders_count, rating, discount_percentage, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_items)

    # Boshlang'ich filiallarni qo'shish
    cur.execute("SELECT COUNT(*) FROM branches")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        sample_branches = [
            ('Markaziy filial', 'Amir Temur ko\'chasi 1, Toshkent', 41.2995, 69.2401, '+998712345678', '09:00-23:00', 1, 20.0, now),
            ('Chilonzor filiali', 'Chilonzor tumani, Bunyodkor ko\'chasi 10', 41.2753, 69.2056, '+998712345679', '09:00-22:00', 1, 15.0, now),
            ('Yunusobod filiali', 'Yunusobod tumani, Shahrisabz ko\'chasi 5', 41.3506, 69.2896, '+998712345680', '08:00-22:00', 1, 18.0, now),
            ('Sergeli filiali', 'Sergeli tumani, Yangi Sergeli MFY', 41.2278, 69.2233, '+998712345681', '09:00-22:00', 1, 12.0, now),
        ]
        cur.executemany("INSERT INTO branches (name, address, latitude, longitude, phone, working_hours, is_active, delivery_radius, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_branches)

    conn.commit()
    conn.close()

def ensure_orders_columns():
    """Orders jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(orders);")
        cols = [r[1] for r in cur.fetchall()]

        if 'status' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'waiting';")
            conn.commit()

        if 'user_id' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER;")
            conn.commit()

        if 'delivery_address' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_address TEXT;")
            conn.commit()

        if 'delivery_distance' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_distance REAL DEFAULT 0;")
            conn.commit()

        if 'delivery_price' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_price REAL DEFAULT 0;")
            conn.commit()

        if 'customer_phone' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT;")
            conn.commit()

        if 'card_number' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN card_number TEXT;")
            conn.commit()

        if 'courier_id' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_id INTEGER;")
            conn.commit()

        if 'order_type' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN order_type TEXT NOT NULL DEFAULT 'dine_in';")
            conn.commit()

        if 'delivery_latitude' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_latitude REAL;")
            conn.commit()

        if 'delivery_longitude' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_longitude REAL;")
            conn.commit()

        if 'courier_delivery_time' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_delivery_time INTEGER DEFAULT 30;")
            conn.commit()

        if 'delivery_map_url' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_map_url TEXT;")
            conn.commit()

        if 'customer_note' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_note TEXT;")
            conn.commit()

        if 'courier_price' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_price REAL DEFAULT 0;")
            conn.commit()

        if 'courier_delivery_minutes' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_delivery_minutes INTEGER DEFAULT 0;")
            conn.commit()

        if 'branch_id' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN branch_id INTEGER DEFAULT 1;")
            conn.commit()

    except Exception as e:
        app_logger.error(f"Orders jadval migration xatoligi: {str(e)}")
        logging.error(f"Orders jadval migration xatoligi: {str(e)}")
    finally:
        conn.close()

def ensure_users_columns():
    """Users jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(users);")
        cols = [r[1] for r in cur.fetchall()]

        if 'address_latitude' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN address_latitude REAL;")
            conn.commit()

        if 'address_longitude' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN address_longitude REAL;")
            conn.commit()

        if 'interface_language' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN interface_language TEXT DEFAULT 'uz';")
            conn.commit()

        if 'font_size' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN font_size TEXT DEFAULT 'medium';")
            conn.commit()

        if 'dark_theme' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN dark_theme BOOLEAN DEFAULT 0;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_cart_items_columns():
    """Cart_items jadvaliga user_id ustunini qo'shadi va session_id ni optional qiladi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(cart_items);")
        cols = [r[1] for r in cur.fetchall()]
        if 'user_id' not in cols:
            cur.execute("ALTER TABLE cart_items ADD COLUMN user_id INTEGER;")
            conn.commit()

        # Eski jadval strukturasini yangilash - session_id ni NULL qilib qo'yish
        cur.execute("UPDATE cart_items SET session_id = 'temp_session' WHERE session_id IS NULL OR session_id = ''")
        conn.commit()
    except Exception as e:
        pass
    conn.close()

def ensure_staff_columns():
    """Staff jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(staff);")
        cols = [r[1] for r in cur.fetchall()]

        if 'passport_series' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN passport_series TEXT;")
            conn.commit()

        if 'passport_number' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN passport_number TEXT;")
            conn.commit()

        if 'orders_handled' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN orders_handled INTEGER DEFAULT 0;")
            conn.commit()

        if 'last_activity' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN last_activity TEXT;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_courier_columns():
    """Courier jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(couriers);")
        cols = [r[1] for r in cur.fetchall()]

        if 'passport_series' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN passport_series TEXT;")
            conn.commit()

        if 'passport_number' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN passport_number TEXT;")
            conn.commit()

        if 'total_hours' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN total_hours REAL DEFAULT 0;")
            conn.commit()

        if 'deliveries_completed' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN deliveries_completed INTEGER DEFAULT 0;")
            conn.commit()

        if 'last_activity' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN last_activity TEXT;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_menu_items_columns():
    """Menu_items jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(menu_items);")
        cols = [r[1] for r in cur.fetchall()]

        # Kerakli ustunlarni qo'shish
        columns_to_add = [
            ('description', 'TEXT'),
            ('image_url', 'TEXT'),
            ('available', 'BOOLEAN DEFAULT 1'),
            ('stock_quantity', 'INTEGER DEFAULT 0'),
            ('orders_count', 'INTEGER DEFAULT 0'),
            ('rating', 'REAL DEFAULT 0.0'),
            ('discount_percentage', 'REAL DEFAULT 0.0'),
            ('created_at', 'TEXT')
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in cols:
                try:
                    cur.execute(f"ALTER TABLE menu_items ADD COLUMN {col_name} {col_type};")
                    conn.commit()
                    app_logger.info(f"Menu_items jadvaliga {col_name} ustuni qo'shildi")
                except Exception as col_error:
                    app_logger.warning(f"Menu_items jadvaliga {col_name} ustunini qo'shishda xatolik: {str(col_error)}")

    except Exception as e:
        app_logger.error(f"Menu items migration xatoligi: {str(e)}")
    finally:
        if conn:
            conn.close()

def cleanup_expired_orders():
    """Waiting holatidagi, 30 daqiqadan oshgan buyurtmalarni cancelled ga o'tkazadi."""
    conn = get_db()
    cur = conn.cursor()
    cutoff = (get_current_time() - datetime.timedelta(minutes=30)).isoformat()
    try:
        cur.execute("UPDATE orders SET status='cancelled' WHERE status='waiting' AND created_at < ?", (cutoff,))
        conn.commit()
    except Exception as e:
        pass
    conn.close()

def safe_init_database():
    """Xavfsiz ma'lumotlar bazasini ishga tushirish"""
    try:
        app_logger.info("Ma'lumotlar bazasini ishga tushirish boshlandi...")
        init_db()
        app_logger.info("Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")
        return True
    except Exception as e:
        app_logger.error(f"Ma'lumotlar bazasini ishga tushirishda xatolik: {str(e)}")
        try:
            # Fallback - basic initialization
            conn = sqlite3.connect(DB_PATH)
            conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
            conn.close()
            app_logger.warning("Ma'lumotlar bazasi qisman ishga tushirildi")
            return False
        except Exception as fallback_error:
            app_logger.critical(f"Ma'lumotlar bazasi fallback ham ishlamadi: {str(fallback_error)}")
            return False

def create_minimal_app():
    """Minimal Flask app yaratish (emergency fallback)"""
    from flask import Flask as MinimalFlask

    minimal_app = MinimalFlask(__name__)
    minimal_app.secret_key = 'emergency-fallback-key'

    @minimal_app.route('/')
    def emergency_home():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Restaurant System - Emergency Mode</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                .error { color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .info { color: #1976d2; background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
                h1 { color: #333; }
                .btn { background: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🆘 Restaurant System - Emergency Mode</h1>
                <div class="error">
                    <strong>Server xatoligi:</strong> Asosiy tizim ishga tushmadi.
                </div>
                <div class="info">
                    <strong>Status:</strong> Emergency fallback server ishlayapti.
                </div>
                <p>Iltimos, quyidagi amallarni bajaring:</p>
                <ul>
                    <li>Server loglarini tekshiring</li>
                    <li>Dependencies o'rnatilganligini tekshiring</li>
                    <li>Database fayli mavjudligini tekshiring</li>
                    <li>Replit console da xatolarni ko'ring</li>
                </ul>
                <a href="/" class="btn">Qayta urinish</a>
            </div>
        </body>
        </html>
        """

    @minimal_app.route('/health')
    def emergency_health():
        return {"status": "emergency", "message": "Minimal fallback server"}

    return minimal_app

# Ensure columns exist on startup
ensure_orders_columns()
ensure_cart_items_columns()
ensure_staff_columns()
ensure_courier_columns()
ensure_menu_items_columns()
ensure_users_columns()


# Database ni xavfsiz ishga tushirish
with app.app_context():
    try:
        safe_init_database()
    except Exception as init_error:
        app_logger.error(f"App context da database initialization xatoligi: {str(init_error)}")

# ---------- Helpers ----------

def next_ticket_no(conn):
    cur = conn.cursor()
    cur.execute("UPDATE counters SET value = value + 1 WHERE name = 'ticket';")
    cur.execute("SELECT value FROM counters WHERE name = 'ticket';")
    return cur.fetchone()[0]

def waiting_position(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting';")
    return cur.fetchone()[0]

def calc_eta_minutes(conn):
    # navbatdagi pozitsiya bo'yicha ETA ni hisoblash
    position = waiting_position(conn)  # sizdan oldingi kutayotganlar soni
    eta_minutes = (position + 1) * AVG_PREP_MINUTES
    return eta_minutes

def get_user_queue_position(conn, ticket_no):
    # Foydalanuvchining navbatdagi o'rni
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM orders
        WHERE status='waiting' AND created_at < (
            SELECT created_at FROM orders WHERE ticket_no=? AND status='waiting'
        )
    """, (ticket_no,))
    result = cur.fetchone()
    return result[0] + 1 if result else 0

def fmt_time(dt):
    return dt.strftime("%H:%M")

def search_location_with_serper(query, gl="uz", hl="uz"):
    """Serper API orqali joylashuvlarni qidirish"""
    try:
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': Config.SERPER_API_KEY, # Config dan API kalitini olish
            'Content-Type': 'application/json'
        }
        data = {
            "q": query,
            "gl": gl,
            "hl": hl
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            app_logger.error(f"Serper API search error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        app_logger.error(f"Serper API xatoligi: {e}")
        return None

def get_places_with_serper(query, gl="uz", hl="uz"):
    """Serper API orqali Google Places ma'lumotlarini olish"""
    try:
        url = "https://google.serper.dev/places"
        headers = {
            'X-API-KEY': Config.SERPER_API_KEY, # Config dan API kalitini olish
            'Content-Type': 'application/json'
        }
        data = {
            "q": query,
            "gl": gl,
            "hl": hl
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            app_logger.error(f"Serper API places error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        app_logger.error(f"Serper Places API xatoligi: {e}")
        return None

def validate_delivery_address(address):
    """Yetkazib berish manzilini tekshirish Yandex API orqali"""
    if not address:
        return False, "Manzil kiritilmagan"

    # Yandex API kaliti mavjudligini tekshirish
    if not app.config['YANDEX_GEOCODER_API']:
        app_logger.warning("Yandex Geocoding API kaliti belgilanmagan. Manzil tekshiruvi cheklangan.")
        # Agar API kaliti bo'lmasa, oddiy tekshiruv
        if len(address) > 5 and any(word in address.lower() for word in ['ko\'cha', 'mahalla', 'tuman', 'shoh', 'yo\'l']):
            return True, "Manzil qabul qilindi (API kaliti yo'q)"
        else:
            return False, "Manzilni to'liqroq kiriting (API kaliti yo'q)"

    try:
        # Yandex Geocoding API orqali manzilni tekshirish
        geocoding_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'apikey': app.config['YANDEX_GEOCODER_API'],
            'geocode': f"{address}, Toshkent, O'zbekiston",
            'format': 'json',
            'results': 1
        }

        response = requests.get(geocoding_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Natijalarni tekshirish
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

            if geo_objects:
                return True, "Manzil topildi"
            else:
                return False, "Manzil topilmadi"
        else:
            app_logger.error(f"Yandex Geocoding API error: {response.status_code} - {response.text}")
            # API ishlamasa, oddiy tekshirish
            if len(address) > 5 and any(word in address.lower() for word in ['ko\'cha', 'mahalla', 'tuman', 'shoh', 'yo\'l']):
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
    """Yetkazib berish masofasini hisoblash Yandex API orqali"""
    # Yandex API kaliti mavjudligini tekshirish
    if not app.config['YANDEX_GEOCODER_API']:
        app_logger.warning("Yandex Geocoding API kaliti belgilanmagan. Masofa hisoblash cheklangan.")
        # Agar API kaliti bo'lmasa, taxminiy masofa
        return calculate_distance_fallback(address)

    try:
        # Restoran koordinatalari (Toshkent markazi)
        restaurant_coords = [41.2995, 69.2401]

        # Yandex Geocoding API orqali manzilni manzilga o'tkazish
        geocoding_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'apikey': app.config['YANDEX_GEOCODER_API'],
            'geocode': f"{address}, Toshkent, O'zbekiston",
            'format': 'json',
            'results': 1
        }

        response = requests.get(geocoding_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

            if geo_objects:
                # Koordinatalarni olish
                point = geo_objects[0]['GeoObject']['Point']['pos'].split()
                dest_coords = [float(point[1]), float(point[0])]  # lat, lng formatida

                # To'g'ri chiziq bo'yicha masofa hisoblash (Haversine formula)
                import math

                lat1, lng1 = math.radians(restaurant_coords[0]), math.radians(restaurant_coords[1])
                lat2, lng2 = math.radians(dest_coords[0]), math.radians(dest_coords[1])

                dlat = lat2 - lat1
                dlng = lng2 - lng1

                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
                c = 2 * math.asin(math.sqrt(a))
                distance_km = 6371 * c  # Yer radiusi 6371 km

                return round(min(50, max(0.5, distance_km)), 1)
            else:
                # Agar Yandex API manzilni topa olmasa, fallback
                return calculate_distance_fallback(address)

        else:
            app_logger.error(f"Yandex Geocoding API distance error: {response.status_code} - {response.text}")
            return calculate_distance_fallback(address) # Agar API xato bersa, fallback

    except Exception as e:
        app_logger.error(f"Masofa hisoblashda umumiy xatolik: {str(e)}")
        return calculate_distance_fallback(address) # Umumiy xatolikda fallback

def calculate_distance_fallback(address):
    """Masofa hisoblash uchun fallback funksiyasi"""
    address_lower = address.lower()
    if 'toshkent' in address_lower or 'алмазар' in address_lower or 'olmazor' in address_lower:
        if any(word in address_lower for word in ['chilonzor', 'olmazor', 'shayxontohur']):
            return 8.0
        elif any(word in address_lower for word in ['yunusobod', 'yashnobod']):
            return 12.0
        elif any(word in address_lower for word in ['sergeli', 'bektemir']):
            return 15.0
        else:
            return 5.0
    elif 'sirdaryo' in address_lower or 'jizzax' in address_lower:
        return 20.0
    elif 'samarqand' in address_lower:
        return 30.0
    else:
        return 7.0 # Umumiy taxminiy qiymat


def find_nearest_branch(user_latitude, user_longitude):
    """Foydalanuvchiga eng yaqin filialni topish"""
    import math

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM branches WHERE is_active = 1")
    branches_raw = cur.fetchall() or [] # Ensure branches_raw is a list
    conn.close()

    if not branches_raw:
        return None

    nearest_branch = None
    min_distance = float('inf')

    for branch_row in branches_raw:
        try:
            # Safe access to branch data, assuming branch_row is a dictionary-like object from fetchall
            branch = dict(branch_row)

            # Ensure coordinates and radius are valid numbers
            branch_lat = float(branch.get('latitude', 0)) if branch.get('latitude') is not None else 0
            branch_lng = float(branch.get('longitude', 0)) if branch.get('longitude') is not None else 0
            delivery_radius = float(branch.get('delivery_radius', 15.0)) if branch.get('delivery_radius') is not None else 15.0

            if not branch_lat or not branch_lng:
                continue # Skip if coordinates are missing or invalid

            # Haversine formula bilan masofa hisoblash
            lat1, lng1 = math.radians(user_latitude), math.radians(user_longitude)
            lat2, lng2 = math.radians(branch_lat), math.radians(branch_lng)

            dlat = lat2 - lat1
            dlng = lng2 - lng1

            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = 6371 * c  # Yer radiusi 6371 km

            if distance < min_distance and distance <= delivery_radius:
                min_distance = distance
                nearest_branch = {
                    'branch': branch,
                    'distance': round(distance, 2)
                }
        except (ValueError, TypeError, KeyError, IndexError) as e:
            app_logger.warning(f"Filial ma'lumotlarini qayta ishlashda xatolik (ID: {branch_row.get('id', 'N/A')}): {str(e)}")
            continue # Skip this branch if error occurs

    return nearest_branch

def calculate_delivery_cost_and_time(distance_km):
    """Masofa bo'yicha yetkazib berish narxi va vaqtini hisoblash"""
    # 1 km uchun 10000 so'm, 2 km uchun 20000 so'm
    base_price = 10000
    price = distance_km * base_price

    # 1 km taxminan 10 daqiqada
    delivery_time_minutes = max(10, int(distance_km * 10))

    return round(price), delivery_time_minutes

def auto_calculate_courier_delivery_price(distance_km):
    """Kuryer uchun avtomatik yetkazish narxini hisoblash"""
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
    """Filial uchun o'rtacha bahoni hisoblash"""
    try:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Filial uchun berilgan baholarni olish (menu_item_id = -branch_id)
            cur.execute("""
                SELECT AVG(CAST(rating AS REAL)) as avg_rating, COUNT(*) as total_ratings
                FROM ratings
                WHERE menu_item_id = ?
            """, (-branch_id,))

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
                    'average_rating': round(avg_rating, 1),
                    'total_ratings': total_ratings
                }

        return {
            'average_rating': 0.0,
            'total_ratings': 0
        }

    except Exception as e:
        app_logger.error(f"Filial bahosini hisoblashda xatolik: {str(e)}")
        return {
            'average_rating': 0.0,
            'total_ratings': 0
        }

def generate_qr_code(receipt_data):
    """Chek uchun QR kod yaratish"""
    # Soliq.uz uchun chek ma'lumotlari
    qr_data = {
        "receipt_number": receipt_data.get('receipt_number', 'N/A'),
        "total_amount": receipt_data.get('total_amount', 0.0),
        "cashback_amount": receipt_data.get('cashback_amount', 0.0),
        "date": receipt_data.get('receipt_created', '')[:10],
        "time": receipt_data.get('receipt_created', '')[11:19],
        "restaurant": "O'zbek Milliy Taomlar Restorani",
        "inn": "123456789",  # Restoran INN raqami
        "cashback_percent": receipt_data.get('cashback_percentage', 1.0)
    }

    # JSON formatda ma'lumotlarni tayyorlash
    qr_text = json.dumps(qr_data, ensure_ascii=False)

    # QR kod yaratish
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    # QR kod rasmini yaratish
    img = qr.make_image(fill_color="black", back_color="white")

    # Base64 formatga o'tkazish
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str

def get_session_id():
    """Session ID yaratish yoki olish - yaxshilangan versiya"""
    try:
        # Session mavjudligini tekshirish
        if not session or 'session_id' not in session or not session['session_id'] or session['session_id'] == 'None':
            import uuid as uuid_module
            session_id = str(uuid_module.uuid4())
            session['session_id'] = session_id
            session.permanent = True  # Session ni permanent qilish

            # Session timeout belgilash
            session.permanent_session_lifetime = datetime.timedelta(days=30)

            app_logger.info(f"Yangi session yaratildi: {session_id[:8]}...")
            return session_id

        # Mavjud session ID ni validatsiya qilish
        session_id = session['session_id']
        if len(session_id) < 10:  # UUID minimal uzunlik tekshiruvi
            import uuid as uuid_module
            new_session_id = str(uuid_module.uuid4())
            session['session_id'] = new_session_id
            app_logger.warning(f"Noto'g'ri session ID tuzatildi: {session_id} -> {new_session_id[:8]}...")
            return new_session_id

        return session_id

    except Exception as e:
        app_logger.error(f"Session ID yaratishda xatolik: {str(e)}")
        # Fallback - oddiy UUID
        import uuid as uuid_module
        fallback_id = str(uuid_module.uuid4())
        try:
            session['session_id'] = fallback_id
            session.permanent = True
        except:
            pass  # Agar session ishlamasa ham davom etish
        return fallback_id

def get_cart_items(conn, session_id, user_id=None):
    """Savatchadagi mahsulotlarni olish - xavfsizligi yuqori"""
    if not conn:
        app_logger.error("Database connection not available in get_cart_items")
        return []

    cur = conn.cursor()

    try:
        # Parametrlarni tekshirish
        if not session_id and not user_id:
            app_logger.warning("Neither session_id nor user_id provided to get_cart_items")
            return []

        if user_id:
            # Asosiy so'rov
            cur.execute("""
                SELECT ci.id, ci.menu_item_id, mi.name, mi.price, ci.quantity,
                       COALESCE(mi.discount_percentage, 0) as discount_percentage,
                       CASE
                           WHEN COALESCE(mi.discount_percentage, 0) > 0
                           THEN (mi.price * (100 - COALESCE(mi.discount_percentage, 0)) / 100) * ci.quantity
                           ELSE mi.price * ci.quantity
                       END as total
                FROM cart_items ci
                JOIN menu_items mi ON ci.menu_item_id = mi.id
                WHERE ci.user_id = ? AND mi.available = 1
                ORDER BY ci.created_at DESC
            """, (user_id,))
        else:
            cur.execute("""
                SELECT ci.id, ci.menu_item_id, mi.name, mi.price, ci.quantity,
                       COALESCE(mi.discount_percentage, 0) as discount_percentage,
                       CASE
                           WHEN COALESCE(mi.discount_percentage, 0) > 0
                           THEN (mi.price * (100 - COALESCE(mi.discount_percentage, 0)) / 100) * ci.quantity
                           ELSE mi.price * ci.quantity
                       END as total
                FROM cart_items ci
                JOIN menu_items mi ON ci.menu_item_id = mi.id
                WHERE ci.session_id = ? AND mi.available = 1
                ORDER BY ci.created_at DESC
            """, (session_id,))

        results = cur.fetchall()

        # Agar natijalar bo'lmasa, bo'sh list qaytarish
        if not results:
            return []

        # Row obyektlarini dict formatiga o'tkazish
        cart_items = []
        for row in results:
            try:
                # SQLite Row obyektini dict ga o'tkazish
                if hasattr(row, 'keys'):
                    item_dict = dict(zip(row.keys(), row))
                else:
                    # Tuple holatida bo'lsa
                    item_dict = {
                        'id': row[0],
                        'menu_item_id': row[1],
                        'name': row[2],
                        'price': row[3],
                        'quantity': row[4],
                        'discount_percentage': row[5] if row[5] is not None else 0,
                        'total': row[6] if len(row) > 6 else row[3] * row[4]
                    }

                # discount_percentage ni tekshirish va None bo'lsa 0 qilib qo'yish
                if item_dict.get('discount_percentage') is None:
                    item_dict['discount_percentage'] = 0

                cart_items.append(item_dict)
            except Exception as row_error:
                app_logger.error(f"Savatcha element o'qishda xatolik: {str(row_error)}")
                continue

        return cart_items

    except Exception as e:
        app_logger.error(f"Savatcha ma'lumotlarini olishda xatolik: {str(e)}")
        return []

def get_cart_total(conn, session_id, user_id=None):
    """Savatchaning umumiy summasini hisoblash"""
    cur = conn.cursor()
    if user_id:
        cur.execute("""
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
        """, (user_id,))
    else:
        cur.execute("""
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
        """, (session_id,))
    result = cur.fetchone()[0]
    return result if result else 0

def clear_cart(conn, session_id, user_id=None):
    """Savatchani tozalash"""
    cur = conn.cursor()
    if user_id:
        cur.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    else:
        cur.execute("DELETE FROM cart_items WHERE session_id = ?", (session_id,))
    conn.commit()

def save_user_to_json(name, ticket_no, order_time, order_items):
    """Foydalanuvchi ma'lumotlarini users.json fayliga saqlash"""
    users_file = 'users.json'

    # Yangi foydalanuvchi ma'lumotlari
    user_data = {
        'ism': name,
        'buyurtma_raqami': ticket_no,
        'buyurtma_vaqti': order_time.strftime("%Y-%m-%d %H:%M:%S"),
        'buyurtma_mahsulotlari': order_items
    }

    # Mavjud ma'lumotlarni o'qish
    users_list = []
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            users_list = []

    # Yangi ma'lumotni qo'shish
    users_list.append(user_data)

    # Faylga saqlash
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, ensure_ascii=False, indent=2)

def save_staff_to_json(first_name, last_name, birth_date, phone, staff_id, register_time):
    """Xodim ma'lumotlarini employees.json fayliga saqlash"""
    employees_file = 'employees.json'

    # Yangi xodim ma'lumotlari
    employee_data = {
        'id': staff_id,
        'ism': first_name,
        'familiya': last_name,
        'tugulgan_sana': birth_date,
        'telefon': phone,
        'royxatdan_otgan_vaqti': register_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Mavjud ma'lumotlarni o'qish
    employees_list = []
    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            employees_list = []

    # Yangi ma'lumotni qo'shish
    employees_list.append(employee_data)

    # Faylga saqlash
    with open(employees_file, 'w', encoding='utf-8') as f:
        json.dump(employees_list, f, ensure_ascii=False, indent=2)

# ---------- Routes ----------

@app.route("/")
def index():
    """Bosh sahifa - xavfsiz error handling bilan"""
    try:
        # Session ID ni olish va tekshirish
        session_id = get_session_id()

        # Asosiy sahifani render qilish
        return render_template("index.html")
    except Exception as e:
        app_logger.error(f"Index sahifasida xatolik: {str(e)}")
        # Emergency fallback
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Restaurant</title></head>
        <body>
            <h1>O'zbek Milliy Taomlar Restorani</h1>
            <p>Sahifa yuklashda xatolik yuz berdi.</p>
            <a href="/menu">Menyu</a>
        </body>
        </html>
        """, 500

@app.route("/system-management-panel-x8k2m")
def admin_index():
    # Super admin yoki staff kirgan bo'lishi kerak
    if not session.get("super_admin") and not session.get("staff_id"):
        flash("Bu sahifaga kirish uchun admin huquqi kerak.", "error")
        return redirect(url_for("index"))
    return render_template("admin_index.html")

@app.route("/display-monitor-tv-screen-z9p4n")
def admin_monitor():
    # Super admin yoki staff kirgan bo'lishi kerak
    if not session.get("super_admin") and not session.get("staff_id"):
        flash("Bu sahifaga kirish uchun admin huquqi kerak.", "error")
        return redirect(url_for("index"))

    cleanup_expired_orders()

    try:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Waiting orders - kutayotgan buyurtmalar
            cur.execute("""SELECT o.*,
                       GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
                FROM orders o
                LEFT JOIN order_details od ON o.id = od.order_id
                LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
                WHERE o.status='waiting'
                GROUP BY o.id
                ORDER BY o.eta_time ASC
            """)
            waiting = cur.fetchall() or []

            # Ready orders - tayyor buyurtmalar
            cur.execute("""SELECT o.*,
                       GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
                FROM orders o
                LEFT JOIN order_details od ON o.id = od.order_id
                LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
                WHERE o.status='ready'
                GROUP BY o.id
                ORDER BY o.eta_time ASC
            """)
            ready = cur.fetchall() or []

            # Served orders in last 5 minutes - so'nggi 5 daqiqada berilgan buyurtmalar
            five_min_ago = (get_current_time() - datetime.timedelta(minutes=5)).isoformat()
            cur.execute("""SELECT o.*,
                       GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
                FROM orders o
                LEFT JOIN order_details od ON o.id = od.order_id
                LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
                WHERE o.status='served' AND o.created_at >= ?
                GROUP BY o.id
                ORDER BY o.created_at DESC
            """, (five_min_ago,))
            served_recent = cur.fetchall() or []

            return render_template('admin_monitor.html',
                                 waiting=[dict(w) for w in waiting],
                                 ready=[dict(r) for r in ready],
                                 served_recent=[dict(s) for s in served_recent])

    except Exception as e:
        app_logger.error(f"Monitor sahifasida xatolik: {str(e)}")
        return render_template('admin_monitor.html',
                             waiting=[],
                             ready=[],
                             served_recent=[])

# Advanced decorators
def login_required(f):
    """Enhanced login decorator"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("super_admin") and not session.get("staff_id"):
            if request.is_json:
                return jsonify({"error": "Authorization required"}), 401
            return redirect(url_for("staff_login"))
        return f(*args, **kwargs)
    return wrapper

def rate_limit(max_requests=100, window=3600):
    """Rate limiting decorator"""
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
    """Result caching decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Cache key yaratish
            cache_key = f"{f.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"

            # Cache dan olishga harakat qilish
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Yangi natija hisoblash va cache ga saqlash
            result = f(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

def async_task(f):
    """Asynchronous task decorator"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return executor.submit(f, *args, **kwargs)
    return wrapper

def validate_json(required_fields=None):
    """JSON validation decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "JSON format required"}), 400

            data = request.get_json()
            if not data:
                return jsonify({"error": "Empty JSON"}), 400

            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({"error": f"Missing fields: {missing_fields}"}), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator

# Performance monitoring decorator ni olib tashlaymiz - conflict keltiryapti

# ---- MENU ----
@app.route("/menu")
@rate_limit(max_requests=500, window=60)
@cache_result(ttl=120)
def menu():
    """Optimized menu endpoint"""
    try:
        # Cache dan menu ma'lumotlarini olish
        cached_menu = cache_manager.get("menu_items_active")

        if not cached_menu:
            menu_items = execute_query(
                """SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.rating) as rating_count
                   FROM menu_items m
                   LEFT JOIN ratings r ON m.id = r.menu_item_id
                   WHERE m.available = 1
                   GROUP BY m.id
                   ORDER BY m.category, m.orders_count DESC, m.name""",
                fetch_all=True
            )

            # Cache ga saqlash
            cache_manager.set("menu_items_active", menu_items, 120)
        else:
            menu_items = cached_menu

        # Kategoriyalar bo'yicha ajratish
        foods = [item for item in menu_items if item['category'] == 'food']
        drinks = [item for item in menu_items if item['category'] == 'drink']

        # Foydalanuvchi sevimlilarini olish
        favorites = []
        if session.get('user_id'):
            favorites_raw = execute_query(
                "SELECT menu_item_id FROM favorites WHERE user_id = ?",
                (session['user_id'],),
                fetch_all=True
            )
            favorites = [fav['menu_item_id'] for fav in favorites_raw] if favorites_raw else []


        return render_template("menu.html",
                             foods=foods,
                             drinks=drinks,
                             favorites=favorites,
                             current_page='menu')

    except Exception as e:
        app_logger.error(f"Menu endpoint error: {str(e)}")
        # Fallback - oddiy menu
        try:
            menu_items = execute_query(
                "SELECT * FROM menu_items WHERE available = 1 ORDER BY category, name",
                fetch_all=True
            )
            foods = [item for item in menu_items if item['category'] == 'food']
            drinks = [item for item in menu_items if item['category'] == 'drink']
            return render_template("menu.html", foods=foods, drinks=drinks, current_page='menu')
        except:
            flash("Menu yuklashda xatolik yuz berdi.", "error")
            return redirect(url_for("index"))

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    try:
        menu_item_id = request.form.get("menu_item_id")
        quantity = int(request.form.get("quantity", 1))

        if not menu_item_id:
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({"success": False, "message": "Mahsulot tanlanmadi"})
            flash("Mahsulot tanlanmadi.", "error")
            return redirect(url_for("menu"))

        session_id = get_session_id()
        user_id = session.get("user_id")

        # Cache dan savatchani tozalash
        cache_manager.delete(f"cart_count_{user_id}_{session_id}")

        conn = get_db()
        cur = conn.cursor()

        # Mavjudligini tekshirish
        if user_id:
            cur.execute("SELECT * FROM cart_items WHERE user_id = ? AND menu_item_id = ?", (user_id, menu_item_id))
        else:
            cur.execute("SELECT * FROM cart_items WHERE session_id = ? AND menu_item_id = ?", (session_id, menu_item_id))

        existing = cur.fetchone()
        now = get_current_time().isoformat()

        if existing:
            # Mavjud bo'lsa miqdorni oshirish - SQLite Row obyektini xavfsiz dict ga aylantirish
            try:
                if hasattr(existing, 'keys'):
                    existing_dict = dict(existing)
                elif isinstance(existing, (tuple, list)) and len(existing) > 0:
                    existing_dict = {'id': existing[0]}
                else:
                    existing_dict = {'id': 1}  # Fallback

                cur.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (quantity, existing_dict['id']))
            except Exception as cart_error:
                app_logger.error(f"Cart update error: {str(cart_error)}")
                # Yangi element qo'shish
                if user_id:
                    cur.execute("INSERT INTO cart_items (user_id, session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?, ?)",
                               (user_id, session_id, menu_item_id, quantity, now))
                else:
                    cur.execute("INSERT INTO cart_items (session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?)",
                               (session_id, menu_item_id, quantity, now))
        else:
            # Yangi qo'shish - har doim session_id ni ham berish
            if user_id:
                cur.execute("INSERT INTO cart_items (user_id, session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?, ?)",
                           (user_id, session_id, menu_item_id, quantity, now))
            else:
                cur.execute("INSERT INTO cart_items (session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?)",
                           (session_id, menu_item_id, quantity, now))

        conn.commit()

        # Yangi cart count ni olish
        if user_id:
            cur.execute("SELECT COALESCE(SUM(quantity), 0) as total_count FROM cart_items WHERE user_id = ?", (user_id,))
        else:
            cur.execute("SELECT COALESCE(SUM(quantity), 0) as total_count FROM cart_items WHERE session_id = ?", (session_id,))

        cart_result = cur.fetchone()
        if hasattr(cart_result, 'keys'):
            cart_count = cart_result['total_count']
        else:
            cart_count = cart_result[0] if cart_result else 0
        conn.close()

        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({"success": True, "message": "Mahsulot qo'shildi", "cart_count": cart_count})

        flash("Mahsulot savatchaga qo'shildi!", "success")
        return redirect(url_for("menu"))

    except Exception as e:
        app_logger.error(f"Add to cart error: {str(e)}")
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({"success": False, "message": "Xatolik yuz berdi"})
        flash("Savatchaga qo'shishda xatolik yuz berdi.", "error")
        return redirect(url_for("menu"))

@app.route("/cart")
def cart():
    session_id = get_session_id()
    user_id = session.get("user_id")
    conn = get_db()

    try:
        # Foydalanuvchi ma'lumotlarini olish va session ga yuklash
        if user_id:
            cur = conn.cursor()
            cur.execute("SELECT phone, address, address_latitude, address_longitude, first_name, last_name FROM users WHERE id = ?", (user_id,))
            user_profile = cur.fetchone()

            if user_profile:
                session['user_phone'] = user_profile['phone'] or ''
                session['user_address'] = user_profile['address'] or ''
                session['user_address_latitude'] = user_profile['address_latitude'] or ''
                session['user_address_longitude'] = user_profile['address_longitude'] or ''
                session['user_first_name'] = user_profile['first_name'] or ''
                session['user_last_name'] = user_profile['last_name'] or ''

        # Savatcha ma'lumotlarini olish
        cart_items = get_cart_items(conn, session_id, user_id)
        total = get_cart_total(conn, session_id, user_id)

        conn.close()
        return render_template("cart.html", cart_items=cart_items or [], total=total or 0)

    except Exception as e:
        app_logger.error(f"Cart sahifasida xatolik: {str(e)}")
        conn.close()
        return render_template("cart.html", cart_items=[], total=0)

@app.route("/remove_from_cart/<int:cart_item_id>", methods=["POST"])
def remove_from_cart(cart_item_id):
    session_id = get_session_id()
    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()

    if user_id:
        cur.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?", (cart_item_id, user_id))
    else:
        cur.execute("DELETE FROM cart_items WHERE id = ? AND session_id = ?", (cart_item_id, session_id))

    conn.commit()
    conn.close()
    flash("Mahsulot savatchadan olib tashlandi.", "success")
    return redirect(url_for("cart"))

@app.route("/favorites")
@login_required
def favorites():
    """Foydalanuvchi sevimli mahsulotlari"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            flash("Sevimlilar ro'yxatini ko'rish uchun tizimga kiring.", "warning")
            return redirect(url_for("login_page"))
        
        conn = get_db()
        cur = conn.cursor()
        
        # Sevimli mahsulotlarni olish
        cur.execute("""
            SELECT m.*, f.created_at as favorite_added
            FROM menu_items m
            JOIN favorites f ON m.id = f.menu_item_id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
        """, (user_id,))
        
        favorite_items = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return render_template("favorites.html", favorites=favorite_items, current_page='favorites')
        
    except Exception as e:
        app_logger.error(f"Favorites sahifasida xatolik: {str(e)}")
        flash("Sevimlilar ro'yxatini yuklashda xatolik yuz berdi.", "error")
        return redirect(url_for("index"))

@app.route("/add-to-favorites/<int:menu_item_id>", methods=["POST"])
@login_required  
def add_to_favorites(menu_item_id):
    """Mahsulotni sevimlilarga qo'shish"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "message": "Tizimga kiring"})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Allaqachon sevimli emasligini tekshirish
        cur.execute("SELECT id FROM favorites WHERE user_id = ? AND menu_item_id = ?", (user_id, menu_item_id))
        if cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Bu mahsulot allaqachon sevimlilarda"})
        
        # Sevimlilarga qo'shish
        now = get_current_time().isoformat()
        cur.execute("INSERT INTO favorites (user_id, menu_item_id, created_at) VALUES (?, ?, ?)", 
                   (user_id, menu_item_id, now))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Sevimlilar ro'yxatiga qo'shildi"})
        
    except Exception as e:
        app_logger.error(f"Add to favorites error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})

@app.route("/remove-from-favorites/<int:menu_item_id>", methods=["POST"])
@login_required
def remove_from_favorites(menu_item_id):
    """Mahsulotni sevimlilardan olib tashlash"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "message": "Tizimga kiring"})
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM favorites WHERE user_id = ? AND menu_item_id = ?", (user_id, menu_item_id))
        conn.commit()
        conn.close()
        
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

        conn = get_db()
        cur = conn.cursor()

        # Email mavjudligini tekshirish
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            flash("Bu email allaqachon ro'yxatdan o'tgan.", "error")
            conn.close()
            return redirect(url_for("register"))

        # Xarita koordinatalari
        address_latitude = request.form.get("address_latitude", "")
        address_longitude = request.form.get("address_longitude", "")

        # Yangi foydalanuvchi yaratish
        password_hash = generate_password_hash(password)
        now = get_current_time().isoformat()

        cur.execute("""
            INSERT INTO users (first_name, last_name, email, phone, address, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, address, password_hash, now))

        conn.commit()
        user_id = cur.lastrowid
        conn.close()

        # Avtomatik tizimga kiritish
        session["user_id"] = user_id
        session["user_name"] = f"{first_name} {last_name}"
        session["user_email"] = email
        session['interface_language'] = 'uz'  # Default til
        session['font_size'] = 'medium'       # Default font size
        session['dark_theme'] = False         # Default theme

        flash(f"Muvaffaqiyatli ro'yxatdan o'tdingiz! Xush kelibsiz, {first_name}!", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Profilni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()

    try:
        # Foydalanuvchi ma'lumotlarini olish
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()

        if not user:
            conn.close()
            flash("Foydalanuvchi ma'lumotlari topilmadi.", "error")
            return redirect(url_for("logout"))

        # Foydalanuvchi buyurtmalar tarixi va umumiy summa
        cur.execute("""
            SELECT o.*,
                   COALESCE(r.total_amount, 0) as total_amount,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN receipts r ON o.id = r.order_id
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE o.user_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 10
        """, (user_id,))
        orders = cur.fetchall()

        conn.close()

        return render_template("profile.html", user=user, orders=orders)

    except Exception as e:
        conn.close()
        logging.error(f"Profile sahifasida xatolik: {str(e)}")
        flash("Profilni yuklashda xatolik yuz berdi.", "error")
        return redirect(url_for("index"))

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not all([first_name, last_name, email]):
        flash("Ism, familiya va email majburiy.", "error")
        return redirect(url_for("profile"))

    conn = get_db()
    cur = conn.cursor()

    # Email takrorlanishini tekshirish
    cur.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
    if cur.fetchone():
        flash("Bu email allaqachon ishlatilmoqda.", "error")
        conn.close()
        return redirect(url_for("profile"))

    # Ma'lumotlarni yangilash
    cur.execute("""
        UPDATE users
        SET first_name = ?, last_name = ?, email = ?, phone = ?
        WHERE id = ?
    """, (first_name, last_name, email, phone, user_id))

    conn.commit()
    conn.close()

    # Session ma'lumotlarini yangilash
    session["user_name"] = f"{first_name} {last_name}"
    session["user_email"] = email

    flash("Profil muvaffaqiyatli yangilandi!", "success")
    return redirect(url_for("profile"))

@app.route("/update_address", methods=["POST"])
def update_address():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    address = request.form.get("address", "").strip()
    address_latitude = request.form.get("address_latitude", "")
    address_longitude = request.form.get("address_longitude", "")

    if not address:
        flash("Manzilni xaritadan tanlang.", "error")
        return redirect(url_for("profile"))

    conn = get_db()
    cur = conn.cursor()

    # Manzilni yangilash
    cur.execute("""
        UPDATE users
        SET address = ?, address_latitude = ?, address_longitude = ?
        WHERE id = ?
    """, (address, address_latitude if address_latitude else None,
          address_longitude if address_longitude else None, user_id))

    conn.commit()
    conn.close()

    flash("Manzil muvaffaqiyatli yangilandi!", "success")
    return redirect(url_for("profile"))

@app.route("/change_password", methods=["POST"])
def change_password():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
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

    conn = get_db()
    cur = conn.cursor()

    # Joriy parolni tekshirish
    cur.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    user_hash = cur.fetchone()

    if not user_hash or not check_password_hash(user_hash["password_hash"], current_password):
        flash("Joriy parol noto'g'ri.", "error")
        conn.close()
        return redirect(url_for("profile_settings"))

    # Yangi parolni saqlash
    new_password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))

    conn.commit()
    conn.close()

    flash("Parol muvaffaqiyatli o'zgartirildi!", "success")
    return redirect(url_for("profile_settings"))

@app.route("/profile/settings")
def profile_settings():
    # Har qanday turdagi foydalanuvchi (user, staff, courier, super_admin) kirishi mumkin
    if not (session.get("user_id") or session.get("staff_id") or session.get("courier_id") or session.get("super_admin")):
        flash("Profil sozlamalarini ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    return render_template("profile_settings.html")

@app.route("/settings")
def general_settings():
    # Har qanday turdagi foydalanuvchi (user, staff, courier, super_admin) kirishi mumkin
    if not (session.get("user_id") or session.get("staff_id") or session.get("courier_id") or session.get("super_admin")):
        flash("Umumi sozlamalarni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    return render_template("general_settings.html")

@app.route("/logout")
def logout():
    user_name = session.get("user_name", "")
    session.clear()
    flash(f"Tizimdan chiqdingiz. Xayr, {user_name}!", "info")
    return redirect(url_for("index"))

# ---- PLACE ORDER ----
@app.route("/place_order", methods=["POST"])
def place_order():
    """Buyurtma berish funksiyasi - to'liq qayta ishlangan"""
    try:
        # Rate limiting
        identifier = request.remote_addr
        if not rate_limiter.is_allowed(identifier, 20, 300):
            flash("Juda ko'p buyurtma. 5 daqiqa kuting.", "error")
            return redirect(url_for("cart"))

        # Foydalanuvchi session'dan ismni olish
        if not session.get("user_id"):
            flash("Buyurtma berish uchun avval tizimga kiring.", "error")
            return redirect(url_for("login"))

        name = session.get("user_name", "")
        user_id = session.get("user_id")

        if not name:
            flash("Foydalanuvchi ma'lumotlari topilmadi.", "error")
            return redirect(url_for("login"))

        # Ma'lumotlar bazasi bilan ishash
        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Foydalanuvchi profilidan ma'lumotlarni olish
            cur.execute("SELECT phone, address, card_number FROM users WHERE id = ?", (user_id,))
            user_profile = cur.fetchone()

            # Session ga profil ma'lumotlarini saqlash
            if user_profile:
                session['user_phone'] = user_profile['phone'] or ''
                session['user_address'] = user_profile['address'] or ''
                session['user_card_number'] = user_profile['card_number'] or ''

            session_id = get_session_id()

            # Savatchani tekshirish
            cart_items = get_cart_items(conn, session_id, user_id)

            if not cart_items or len(cart_items) == 0:
                flash("Savatchangiz bo'sh. Avval taom tanlang.", "error")
                return redirect(url_for("menu"))

            # Formdan ma'lumotlarni xavfsiz olish
            order_type = request.form.get("order_type", "dine_in")
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
                if not session.get('user_phone') and not customer_phone_new:
                    flash("Telefon raqamingizni kiriting!", "error")
                    return redirect(url_for("cart"))

            # Foydalanuvchi profilini yangilash
            if home_address:
                cur.execute("UPDATE users SET address = ? WHERE id = ?", (home_address, user_id))
                session['user_address'] = home_address
            if customer_phone_new:
                cur.execute("UPDATE users SET phone = ? WHERE id = ?", (customer_phone_new, user_id))
                session['user_phone'] = customer_phone_new
            if card_number_new:
                cur.execute("UPDATE users SET card_number = ? WHERE id = ?", (card_number_new, user_id))
                session['user_card_number'] = card_number_new

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
            customer_phone = session.get('user_phone', '') or customer_phone_new
            card_number = session.get('user_card_number', '') or card_number_new

            # Masofa va vaqtni xavfsiz aylantirish
            try:
                delivery_distance = float(delivery_distance) if delivery_distance else 0
            except (ValueError, TypeError):
                delivery_distance = 0

            # Delivery uchun ETA ni qayta hisoblash
            if order_type == "delivery":
                courier_delivery_time = 30
                eta_time = now + datetime.timedelta(minutes=eta_minutes + courier_delivery_time)

            # Branch ID ni xavfsiz olish
            branch_id = 1
            try:
                branch_id = int(request.form.get("branch_id", 1))
            except (ValueError, TypeError):
                branch_id = 1

            # Buyurtma yaratish
            cur.execute("""
                INSERT INTO orders (user_id, customer_name, ticket_no, order_type, status, delivery_address, delivery_distance, delivery_latitude, delivery_longitude, delivery_map_url, customer_note, customer_phone, card_number, branch_id, created_at, eta_time)
                VALUES (?, ?, ?, ?, 'waiting', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (user_id, name, tno, order_type, delivery_address, delivery_distance, delivery_latitude, delivery_longitude, delivery_map_url, customer_note, customer_phone, card_number, branch_id, now.isoformat(), eta_time.isoformat()))

            order_id = cur.lastrowid

            # Savatchadagi mahsulotlarni order_details ga ko'chirish
            order_items_for_json = []
            total_amount = 0

            for item in cart_items:
                # Skidka narxini hisoblash
                discount_percentage = item.get('discount_percentage', 0) or 0
                final_price = item['price']
                if discount_percentage > 0:
                    final_price = item['price'] * (100 - discount_percentage) / 100

                item_total = final_price * item['quantity']
                total_amount += item_total

                cur.execute("""
                    INSERT INTO order_details (order_id, menu_item_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                """, (order_id, item['menu_item_id'], item['quantity'], final_price))

                # JSON uchun mahsulot ma'lumotlarini to'plash
                order_items_for_json.append({
                    'nomi': item['name'],
                    'miqdori': item['quantity'],
                    'asl_narxi': item['price'],
                    'skidka_foizi': discount_percentage,
                    'yakuniy_narxi': final_price,
                    'jami': item_total
                })

            # Chek yaratish
            receipt_number = f"R{tno}{now.strftime('%H%M%S')}"
            cashback_percentage = 1.0
            cashback_amount = total_amount * (cashback_percentage / 100)

            cur.execute("""
                INSERT INTO receipts (order_id, receipt_number, total_amount, cashback_amount, cashback_percentage, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (order_id, receipt_number, total_amount, cashback_amount, cashback_percentage, now.isoformat()))

            # Savatchani tozalash
            clear_cart(conn, session_id, user_id)

            # Cache ni tozalash
            cache_manager.delete(f"cart_count_{user_id}_{session_id}")

            # Foydalanuvchini JSON fayliga saqlash
            executor.submit(save_user_to_json, name, tno, now, order_items_for_json)

            flash("Buyurtma muvaffaqiyatli berildi!", "success")
            return redirect(url_for("user_success", ticket_no=tno))

    except Exception as e:
        app_logger.error(f"Buyurtma berishda xatolik: {str(e)}")
        flash("Buyurtma berishda xatolik yuz berdi. Qaytadan urinib ko'ring.", "error")
        return redirect(url_for("cart"))

@app.route("/user", methods=["GET", "POST"])
def user_page():
    # Eski user route ni redirect qilish
    if request.method == "POST":
        return place_order()
    return redirect(url_for("menu"))

@app.route("/user/success/<int:ticket_no>")
def user_success(ticket_no):
    conn = get_db()
    cur = conn.cursor()

    # Buyurtma ma'lumotlarini olish
    cur.execute("SELECT * FROM orders WHERE ticket_no=? ORDER BY id DESC LIMIT 1;", (ticket_no,))
    order = cur.fetchone()

    if not order:
        conn.close()
        flash("Buyurtma topilmadi.", "error")
        return redirect(url_for("menu"))

    # Buyurtma tafsilotlarini olish
    cur.execute("""
        SELECT od.*, mi.name
        FROM order_details od
        JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE od.order_id = ?
    """, (order['id'],))
    order_items = cur.fetchall()

    conn.close()

    # ETA vaqtini formatlash
    eta_time = datetime.datetime.fromisoformat(order["eta_time"])

    return render_template("user_success.html",
                         order=order,
                         order_items=order_items,
                         eta_hhmm=eta_time.strftime("%H:%M"))

# ---- COURIER AUTH ----
@app.route("/courier-secure-login-k4m7p", methods=["GET", "POST"])
def courier_login():
    if request.method == "POST":
        courier_id = request.form.get("courier_id", "").strip()
        password = request.form.get("password", "")
        if not courier_id or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("courier_login"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM couriers WHERE id=?;", (courier_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            # Faollik vaqtini yangilash va ishchi soatlarini hisoblash
            now = get_current_time().isoformat()

            # Yangi connection yaratish
            conn_update = get_db()
            cur_update = conn_update.cursor()

            # Row obyektini dict ga aylantirish
            try:
                if hasattr(row, 'keys'):
                    row_dict = dict(row)
                else:
                    columns = ['id', 'first_name', 'last_name', 'birth_date', 'phone', 'passport_series', 'passport_number', 'password_hash', 'total_hours', 'deliveries_completed', 'last_activity', 'created_at']
                    row_dict = {columns[i]: row[i] if i < len(row) else None for i in range(len(columns))}
                
                # Agar avvalgi faollik vaqti mavjud bo'lsa, ishchi soatlarni yangilash
                if row_dict.get("last_activity"):
                    try:
                        last_activity = datetime.datetime.fromisoformat(row_dict["last_activity"])
                        current_time = get_current_time()
                        time_diff = current_time - last_activity

                        # Agar 8 soatdan kam bo'lsa, ishchi vaqtga qo'shish
                        if time_diff.total_seconds() < 28800:  # 8 soat
                            additional_hours = time_diff.total_seconds() / 3600
                            cur_update.execute("UPDATE couriers SET total_hours = COALESCE(total_hours, 0) + ?, last_activity = ? WHERE id = ?",
                                       (additional_hours, now, courier_id))
                        else:
                            cur_update.execute("UPDATE couriers SET last_activity = ? WHERE id = ?", (now, courier_id))
                    except:
                        cur_update.execute("UPDATE couriers SET last_activity = ? WHERE id = ?", (now, courier_id))
                else:
                    cur_update.execute("UPDATE couriers SET last_activity = ? WHERE id = ?", (now, courier_id))
            except Exception as dict_error:
                app_logger.error(f"Courier row dict conversion error: {str(dict_error)}")
                row_dict = None

            conn_update.commit()
            conn_update.close()

        conn.close()
        if row:
            # SQLite Row obyektini xavfsiz dict ga aylantirish
            try:
                if hasattr(row, 'keys'):
                    row_dict = dict(row)
                else:
                    # Tuple format uchun manual dict yaratish
                    columns = ['id', 'first_name', 'last_name', 'birth_date', 'phone', 'passport_series', 'passport_number', 'password_hash', 'total_hours', 'deliveries_completed', 'last_activity', 'created_at']
                    row_dict = {columns[i]: row[i] if i < len(row) else None for i in range(len(columns))}
            except Exception as dict_error:
                app_logger.error(f"Courier row dict conversion error: {str(dict_error)}")
                conn.close()
                flash("Database xatoligi yuz berdi.", "error")
                return redirect(url_for("courier_login"))

            if check_password_hash(row_dict.get("password_hash", ""), password):
                # Login muvaffaqiyatli
                pass
            else:
                conn.close()
                flash("Noto'g'ri ID yoki parol.", "error")
                return redirect(url_for("courier_login"))
        else:
            conn.close()
            flash("Kuryer topilmadi.", "error")
            return redirect(url_for("courier_login"))

        session["courier_id"] = row_dict["id"]
        session["courier_name"] = f"{row_dict['first_name']} {row_dict['last_name']}"
        return redirect(url_for("courier_dashboard"))
    return render_template("courier_login.html")

@app.route("/courier-register-secure-p8x3m", methods=["GET", "POST"])
def courier_register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        passport_series = request.form.get("passport_series", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        password = request.form.get("password", "")

        if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("courier_register"))

        conn = get_db()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        now = get_current_time()
        try:
            cur.execute("""
                INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))
        except sqlite3.OperationalError:
            # Agar birth_date ustuni mavjud bo'lmasa, uni qo'shish
            cur.execute("ALTER TABLE couriers ADD COLUMN birth_date TEXT;")
            cur.execute("""
                INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

        new_id = cur.lastrowid
        # ID kamida 5 ta raqamdan iborat bo'lishi uchun
        if new_id < 10000:
            cur.execute("UPDATE couriers SET id = ? WHERE id = ?", (10000 + new_id, new_id))
            new_id = 10000 + new_id

        conn.commit()
        conn.close()

        flash(f"Kuryer sifatida ro'yxatdan o'tdingiz. Sizning ID raqamingiz: {new_id}", "success")
        return redirect(url_for("courier_login"))

    return render_template("courier_register.html")

@app.route("/courier/dashboard")
def courier_dashboard():
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    conn = get_db()
    cur = conn.cursor()
    courier_id = session.get("courier_id")

    # Barcha ready delivery buyurtmalar va kuryerga tegishli buyurtmalarni olish
    cur.execute("""
        SELECT o.*,
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE (o.order_type = 'delivery' AND o.status = 'ready')
           OR (o.courier_id = ? AND o.status IN ('on_way', 'delivered'))
        GROUP BY o.id
        ORDER BY
            CASE
                WHEN o.status = 'ready' THEN 1
                WHEN o.status = 'on_way' THEN 2
                WHEN o.status = 'delivered' THEN 3
                ELSE 4
            END,
            o.created_at ASC
    """, (courier_id,))
    delivery_orders = cur.fetchall()

    # Kuryer statistikasini olish
    cur.execute("SELECT deliveries_completed, total_hours FROM couriers WHERE id = ?", (courier_id,))
    courier_stats = cur.fetchone()

    # Faol buyurtmalar sonini olish
    cur.execute("SELECT COUNT(*) FROM orders WHERE courier_id = ? AND status = 'on_way'", (courier_id,))
    active_orders = cur.fetchone()[0]

    # Session ga statistikani saqlash
    if courier_stats:
        try:
            # courier_stats tuple yoki Row obyekti bo'lishi mumkin
            if hasattr(courier_stats, '__getitem__'):
                session['courier_deliveries'] = courier_stats[0] or 0
                session['courier_hours'] = round(courier_stats[1] or 0, 1) if courier_stats[1] else 0
            else:
                session['courier_deliveries'] = getattr(courier_stats, 'deliveries_completed', 0) or 0
                session['courier_hours'] = round(getattr(courier_stats, 'total_hours', 0) or 0, 1)
        except (TypeError, IndexError) as e:
            logging.error(f"Kuryer statistikasini o'qishda xatolik: {str(e)}")
            session['courier_deliveries'] = 0
            session['courier_hours'] = 0
    else:
        session['courier_deliveries'] = 0
        session['courier_hours'] = 0
    session['courier_active_orders'] = active_orders

    conn.close()
    return render_template("courier_dashboard.html", orders=delivery_orders)

@app.route("/courier/order/<int:order_id>/take", methods=["POST"])
def courier_take_order(order_id):
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    courier_id = session.get("courier_id")

    try:
        with db_pool.get_connection() as conn:
            cur = conn.cursor()

            # Buyurtma ma'lumotlarini olish
            cur.execute("SELECT * FROM orders WHERE id=? AND status='ready' AND order_type='delivery'", (order_id,))
            order = cur.fetchone()

            if order:
                # Avtomatik narx va vaqt hisoblash
                distance = float(order['delivery_distance']) if order['delivery_distance'] else 5.0
                auto_price, auto_delivery_time = auto_calculate_courier_delivery_price(distance)

                # Buyurtmani yangilash
                cur.execute("""
                    UPDATE orders
                    SET status='on_way', courier_id=?, courier_price=?, courier_delivery_minutes=?, delivery_price=?
                    WHERE id=? AND status='ready'
                """, (courier_id, auto_price, auto_delivery_time, auto_price, order_id))

                flash(f"Buyurtma olib ketildi! Avtomatik narx: {auto_price:,} so'm, Vaqt: {auto_delivery_time} daqiqa", "success")
            else:
                flash("Buyurtma topilmadi yoki allaqachon olingan!", "error")

    except Exception as e:
        app_logger.error(f"Courier take order error: {str(e)}")
        flash("Buyurtmani olishda xatolik yuz berdi.", "error")

    return redirect(url_for("courier_dashboard"))

@app.route("/courier/order/<int:order_id>/delivered", methods=["POST"])
def courier_mark_delivered(order_id):
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    courier_id = session.get("courier_id")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE orders SET status='delivered' WHERE id=? AND courier_id=?", (order_id, courier_id))

    # Kuryerning yetkazib bergan buyurtmalar sonini oshirish
    cur.execute("UPDATE couriers SET deliveries_completed = COALESCE(deliveries_completed, 0) + 1 WHERE id = ?", (courier_id,))

    conn.commit()
    conn.close()
    flash("Buyurtma yetkazib berildi!", "success")
    return redirect(url_for("courier_dashboard"))

@app.route("/courier/set-price-time", methods=["POST"])
def courier_set_price_time():
    if "courier_id" not in session:
        return jsonify({"success": False, "message": "Kuryer tizimga kirmagan"}), 401

    data = request.get_json()
    order_id = data.get("order_id")
    price = data.get("price")
    delivery_time = data.get("delivery_time")

    if not all([order_id, price, delivery_time]):
        return jsonify({"success": False, "message": "Barcha maydonlarni to'ldiring"})

    try:
        price = float(price)
        delivery_time = int(delivery_time)

        if price <= 0 or delivery_time <= 0:
            return jsonify({"success": False, "message": "Narx va vaqt musbat bo'lishi kerak"})

        conn = get_db()
        cur = conn.cursor()

        # Buyurtma mavjudligini va statusini tekshirish
        cur.execute("SELECT * FROM orders WHERE id = ? AND status = 'ready'", (order_id,))
        order = cur.fetchone()

        if not order:
            conn.close()
            return jsonify({"success": False, "message": "Buyurtma topilmadi yoki tayyor emas"})

        # Narx va vaqtni yangilash
        cur.execute("""
            UPDATE orders
            SET courier_price = ?, courier_delivery_minutes = ?, delivery_price = ?
            WHERE id = ?
        """, (price, delivery_time, price, order_id))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Narx va vaqt belgilandi"})

    except Exception as e:
        logging.error(f"Kuryer narx belgilashda xatolik: {str(e)}")
        return jsonify({"success": False, "message": "Server xatoligi"}), 500

@app.route("/courier/logout")
def courier_logout():
    session.pop("courier_id", None)
    session.pop("courier_name", None)
    return redirect(url_for("index"))

@app.route("/api/cart-count")
def api_cart_count():
    """Savatchadagi mahsulotlar sonini qaytarish - API endpoint"""
    try:
        session_id = get_session_id()
        user_id = session.get("user_id")
        
        conn = get_db()
        cur = conn.cursor()
        
        if user_id:
            cur.execute("SELECT COALESCE(SUM(quantity), 0) as total_count FROM cart_items WHERE user_id = ?", (user_id,))
        else:
            cur.execute("SELECT COALESCE(SUM(quantity), 0) as total_count FROM cart_items WHERE session_id = ?", (session_id,))
        
        result = cur.fetchone()
        cart_count = result[0] if result else 0
        conn.close()
        
        return jsonify({"cart_count": cart_count})
        
    except Exception as e:
        app_logger.error(f"Cart count API error: {str(e)}")
        return jsonify({"cart_count": 0})

# Cart count endpoint moved to top priority section

# ---- STATIC FILE HANDLING ----
@app.route('/static/<path:filename>')
def static_files(filename):
    """Static fayllar uchun xavfsiz route"""
    try:
        return app.send_static_file(filename)
    except Exception as e:
        app_logger.error(f"Static file error for {filename}: {str(e)}")
        return "File not found", 404

# ---- LOGIN ROUTES ----
@app.route("/login")
def login():
    """Login route - login_page ga yo'naltirish"""
    return redirect(url_for("login_page"))

@app.route("/login_page", methods=["GET", "POST"])
def login_page():
    # URL dan role parametrini tekshirish
    role_param = request.args.get('role')

    if role_param == 'staff':
        return redirect(url_for("staff_login"))
    elif role_param == 'courier':
        return redirect(url_for("courier_login"))
    elif role_param == 'admin':
        return redirect(url_for("super_admin_login"))
    else:
        # Regular user login
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email va parolni kiriting.", "error")
                return redirect(url_for("login_page"))

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cur.fetchone()
            conn.close()

            if user:
                try:
                    # SQLite Row obyektini xavfsiz dict ga aylantirish
                    if hasattr(user, 'keys'):
                        user_dict = dict(user)
                    elif isinstance(user, (tuple, list)) and len(user) >= 4:
                        # Tuple format uchun manual dict yaratish
                        columns = ['id', 'first_name', 'last_name', 'email', 'phone', 'password_hash', 'address', 'card_number', 'card_expiry', 'created_at', 'address_latitude', 'address_longitude', 'interface_language', 'font_size', 'dark_theme']
                        user_dict = {columns[i]: user[i] if i < len(user) else None for i in range(len(columns))}
                    else:
                        flash("Foydalanuvchi ma'lumotlari noto'g'ri formatda.", "error")
                        return redirect(url_for("login_page"))

                    if check_password_hash(user_dict.get("password_hash", ""), password):
                        # User ma'lumotlarini alohida o'zgaruvchilarga saqlash
                        user_id = user_dict.get("id")
                        user_first_name = user_dict.get("first_name", "")
                        user_last_name = user_dict.get("last_name", "")
                        user_email = user_dict.get("email", "")

                        session["user_id"] = user_id
                        session["user_name"] = f"{user_first_name} {user_last_name}".strip()
                        session["user_email"] = user_email
                        session['interface_language'] = user_dict.get('interface_language') or 'uz'
                        session['font_size'] = user_dict.get('font_size') or 'medium'
                        session['dark_theme'] = bool(user_dict.get('dark_theme', 0))
                        flash(f"Xush kelibsiz, {user_first_name}!", "success")
                        return redirect(url_for("index"))
                    else:
                        flash("Noto'g'ri email yoki parol.", "error")
                        return redirect(url_for("login_page"))
                except Exception as login_error:
                    app_logger.error(f"User login processing error: {str(login_error)}")
                    flash("Login jarayonida xatolik yuz berdi.", "error")
                    return redirect(url_for("login_page"))
            else:
                flash("Foydalanuvchi topilmadi.", "error")
                return redirect(url_for("login_page"))

        return render_template("login.html")

# ---- STAFF AUTH ----
@app.route('/staff-secure-login-w7m2k', methods=["GET", "POST"])
def staff_login():
    """Xodim kirish sahifasi"""
    if request.method == "POST":
        staff_id = request.form.get("staff_id", "").strip()
        password = request.form.get("password", "")

        if not staff_id or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("staff_login"))

        # ID raqam ekanligini tekshirish
        try:
            staff_id_int = int(staff_id)
        except ValueError:
            flash("ID raqam bo'lishi kerak.", "error")
            return redirect(url_for("staff_login"))

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM staff WHERE id=?", (staff_id_int,))
            row = cur.fetchone()

            if row:
                # SQLite Row obyektini xavfsiz dict ga aylantirish
                try:
                    if hasattr(row, 'keys'):
                        row_dict = dict(row)
                    else:
                        # Tuple format uchun manual dict yaratish
                        columns = ['id', 'first_name', 'last_name', 'birth_date', 'phone', 'passport_series', 'passport_number', 'password_hash', 'total_hours', 'orders_handled', 'last_activity', 'created_at']
                        row_dict = {columns[i]: row[i] if i < len(row) else None for i in range(len(columns))}

                    # Password hash ni tekshirish
                    password_hash = row_dict.get("password_hash", "")

                    # Debug uchun
                    app_logger.info(f"Staff login attempt: ID={staff_id_int}, has_hash={bool(password_hash)}")

                    if password_hash and check_password_hash(password_hash, password):
                        # Faollik vaqtini yangilash
                        now = get_current_time()
                        now_iso = now.isoformat()

                        try:
                            cur.execute("UPDATE staff SET last_activity = ? WHERE id = ?", (now_iso, staff_id_int))
                            conn.commit()
                        except Exception as update_error:
                            app_logger.warning(f"Staff faollik yangilashda xatolik: {str(update_error)}")

                        # Session ma'lumotlarini saqlash
                        session["staff_id"] = row_dict["id"]
                        session["staff_name"] = f"{row_dict['first_name']} {row_dict['last_name']}"

                        conn.close()
                        flash(f"Xush kelibsiz, {row_dict['first_name']}!", "success")
                        return redirect(url_for("staff_dashboard"))
                    else:
                        conn.close()
                        flash("Noto'g'ri ID yoki parol.", "error")
                        app_logger.warning(f"Failed login attempt for staff ID: {staff_id_int}")
                        return redirect(url_for("staff_login"))

                except Exception as dict_error:
                    app_logger.error(f"Staff row processing error: {str(dict_error)}")
                    conn.close()
                    flash("Ma'lumotlarni qayta ishlashda xatolik.", "error")
                    return redirect(url_for("staff_login"))
            else:
                conn.close()
                flash("Noto'g'ri ID yoki parol.", "error")
                app_logger.warning(f"Staff not found for ID: {staff_id_int}")
                return redirect(url_for("staff_login"))

        except Exception as e:
            if 'conn' in locals():
                conn.close()
            app_logger.error(f"Staff login error: {str(e)}")
            flash("Tizimda xatolik yuz berdi.", "error")
            return redirect(url_for("staff_login"))

    return render_template("staff_login.html")

@app.route('/staff-register-secure-x9n5k', methods=["GET", "POST"])
def staff_register():
    """Xodim ro'yxatdan o'tish sahifasi"""
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        passport_series = request.form.get("passport_series", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        password = request.form.get("password", "")

        if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("staff_register"))

        conn = get_db()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        now = get_current_time()
        
        try:
            cur.execute("""
                INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

            new_id = cur.lastrowid
            # ID kamida 5 ta raqamdan iborat bo'lishi uchun
            if new_id < 10000:
                cur.execute("UPDATE staff SET id = ? WHERE id = ?", (10000 + new_id, new_id))
                new_id = 10000 + new_id

            conn.commit()
            conn.close()

            flash(f"Xodim sifatida ro'yxatdan o'tdingiz. Sizning ID raqamingiz: {new_id}", "success")
            return redirect(url_for("staff_login"))
            
        except Exception as e:
            conn.close()
            app_logger.error(f"Staff register error: {str(e)}")
            flash("Ro'yxatdan o'tishda xatolik yuz berdi.", "error")
            return redirect(url_for("staff_register"))
    
    try:
        return render_template('staff_register.html')
    except Exception as e:
        app_logger.error(f"Staff register error: {str(e)}")
        return render_template('error.html', error="Sahifa yuklanmadi"), 500

@app.route("/admin/logout")
def staff_logout():
    # Super admin bo'lsa, super admin sessionni saqlash
    is_super_admin = session.get("super_admin", False)
    session.clear()
    if is_super_admin:
        session["super_admin"] = True
        flash("Staff sessiondan chiqildi, super admin sessioni saqlandi.", "info")
    return redirect(url_for("index"))

# ---- STAFF DASHBOARD ----

@app.route("/admin/dashboard")
@login_required
def staff_dashboard():
    cleanup_expired_orders()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*,
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        GROUP BY o.id
        ORDER BY
            CASE
                WHEN o.status = 'ready' THEN 1
                WHEN o.status = 'waiting' THEN 2
                WHEN o.status = 'served' THEN 3
                WHEN o.status = 'cancelled' THEN 4
                ELSE 5
            END,
            o.eta_time ASC,
            o.created_at ASC
    """)
    orders = cur.fetchall()
    conn.close()
    return render_template("staff_dashboard.html", orders=orders, staff_name=session.get("staff_name"))

@app.route("/admin/menu")
@login_required
def staff_menu():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu_items ORDER BY category, name")
    menu_items = cur.fetchall()
    conn.close()
    return render_template("staff_menu.html", menu_items=menu_items, staff_name=session.get("staff_name"))

@app.route("/admin/add_menu_item", methods=["POST"])
@login_required
def add_menu_item():
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "")
    category = request.form.get("category", "")
    description = request.form.get("description", "").strip()

    if not all([name, price, category]):
        flash("Barcha majburiy maydonlarni to'ldiring.", "error")
        return redirect(url_for("staff_menu"))

    try:
        price = float(price)
    except ValueError:
        flash("Narx raqam bo'lishi kerak.", "error")
        return redirect(url_for("staff_menu"))

    # Rasm yuklash
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            # Rasm faylini saqlash
            import uuid
            from werkzeug.utils import secure_filename

            # Static/images papkasini yaratish
            images_dir = os.path.join('static', 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            # Fayl nomini xavfsiz qilish
            filename = secure_filename(file.filename)
            # Unikal nom yaratish
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(images_dir, unique_filename)

            try:
                file.save(file_path)
                image_url = f"/static/images/{unique_filename}"
            except Exception as e:
                flash("Rasmni yuklashda xatolik yuz berdi.", "error")
                return redirect(url_for("staff_menu"))

    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()

    # Jadval tuzilishini tekshirish va kerakli ustunlarni qo'shish
    cur.execute("PRAGMA table_info(menu_items);")
    columns = [col[1] for col in cur.fetchall()]

    if 'description' not in columns:
        cur.execute("ALTER TABLE menu_items ADD COLUMN description TEXT;")

    if 'image_url' not in columns:
        cur.execute("ALTER TABLE menu_items ADD COLUMN image_url TEXT;")

    # Ma'lumotni kiritish
    cur.execute("INSERT INTO menu_items (name, price, category, description, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
               (name, price, category, description, image_url, now))

    conn.commit()
    conn.close()
    flash("Yangi mahsulot qo'shildi!", "success")
    return redirect(url_for("staff_menu"))

@app.route("/admin/toggle_menu_item/<int:item_id>", methods=["POST"])
@login_required
def toggle_menu_item(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE menu_items SET available = NOT available WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Mahsulot holati o'zgartirildi.", "success")
    return redirect(url_for("staff_menu"))

@app.route("/admin/edit_menu_item/<int:item_id>", methods=["POST"])
@login_required
def edit_menu_item(item_id):
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "")
    description = request.form.get("description", "").strip()
    discount_percentage = request.form.get("discount_percentage", "0")

    if not all([name, price]):
        flash("Nom va narx majburiy.", "error")
        return redirect(url_for("staff_menu"))

    try:
        price = float(price)
        discount_percentage = float(discount_percentage)
        if discount_percentage < 0 or discount_percentage > 100:
            flash("Skidka 0 dan 100 gacha bo'lishi kerak.", "error")
            return redirect(url_for("staff_menu"))
    except ValueError:
        flash("Narx va skidka raqam bo'lishi kerak.", "error")
        return redirect(url_for("staff_menu"))

    # Rasm yuklash
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            import uuid
            from werkzeug.utils import secure_filename

            images_dir = os.path.join('static', 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(images_dir, unique_filename)

            try:
                file.save(file_path)
                image_url = f"/static/images/{unique_filename}"
            except Exception as e:
                flash("Rasmni yuklashda xatolik yuz berdi.", "error")
                return redirect(url_for("staff_menu"))

    conn = get_db()
    cur = conn.cursor()

    if image_url:
        cur.execute("""
            UPDATE menu_items
            SET name = ?, price = ?, description = ?, discount_percentage = ?, image_url = ?
            WHERE id = ?
        """, (name, price, description, discount_percentage, image_url, item_id))
    else:
        cur.execute("""
            UPDATE menu_items
            SET name = ?, price = ?, description = ?, discount_percentage = ?
            WHERE id = ?
        """, (name, price, description, discount_percentage, item_id))

    conn.commit()
    conn.close()
    flash("Mahsulot tahrirlandi!", "success")
    return redirect(url_for("staff_menu"))

@app.route("/admin/order/<int:order_id>/served", methods=["POST"])
@login_required
def staff_mark_served(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='served' WHERE id=?;", (order_id,))

    # Xodimning bajargan buyurtmalar sonini oshirish
    staff_id = session.get("staff_id")
    if staff_id:
        cur.execute("UPDATE staff SET orders_handled = COALESCE(orders_handled, 0) + 1 WHERE id = ?", (staff_id,))

    conn.commit()
    conn.close()
    flash("Buyurtma foydalanuvchiga berildi sifatida belgilandi.", "success")
    return redirect(url_for("staff_dashboard"))

@app.route("/admin/order/<int:order_id>/ready", methods=["POST"])
@login_required
def staff_mark_ready(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='ready' WHERE id=?;", (order_id,))

    # Xodimning bajargan buyurtmalar sonini oshirish
    staff_id = session.get("staff_id")
    if staff_id:
        cur.execute("UPDATE staff SET orders_handled = COALESCE(orders_handled, 0) + 1 WHERE id = ?", (staff_id,))

    conn.commit()
    conn.close()
    flash("Buyurtma 'tayyor' deb belgilandi.", "success")
    return redirect(url_for("staff_dashboard"))

@app.route("/admin/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def staff_mark_cancel(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='cancelled' WHERE id=?;", (order_id,))
    conn.commit()
    conn.close()
    flash("Buyurtma bekor qilindi.", "warning")
    return redirect(url_for("staff_dashboard"))



@app.route("/user/cancel/<int:ticket_no>", methods=["POST"])
def user_cancel(ticket_no):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE ticket_no=? ORDER BY id DESC LIMIT 1", (ticket_no,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return jsonify({"ok": False, "msg": "Buyurtma topilmadi"}), 404
    if order['status'] in ('served', 'ready'):
        conn.close()
        return jsonify({"ok": False, "msg": "Buyurtma allaqachon tayyor yoki berilgan, bekor qilib bo'lmaydi"}), 400
    cur.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order['id'],))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "msg": "Buyurtma bekor qilindi"})
@app.route("/admin/orders.json")
@login_required
def staff_orders_json():
    """Super admin uchun barcha buyurtmalar JSON formatida"""
    try:
        cleanup_expired_orders()
        orders = execute_query("""
            SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            GROUP BY o.id
            ORDER BY created_at ASC
        """, fetch_all=True)
        return jsonify([dict(order) for order in orders])
    except Exception as e:
        app_logger.error(f"Staff orders.json error: {str(e)}")
        return jsonify([]), 500

@app.route("/admin/employees")
@login_required
def staff_employees():
    """Xodimlar ro'yxatini ko'rish"""
    employees_file = 'employees.json'
    employees = []

    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            employees = []

    return render_template("staff_employees.html", employees=employees, staff_name=session.get("staff_name"))

# ---- SUPER ADMIN ----
# Super admin kredentsiallari - universal konfiguratsiyadan
SUPER_ADMIN_USERNAME = Config.SUPER_ADMIN_USERNAME
SUPER_ADMIN_PASSWORD = Config.SUPER_ADMIN_PASSWORD

@app.route("/super-admin-control-panel-master-z8x9k", methods=["GET", "POST"])
def super_admin_login():
    if request.method == "GET":
        return render_template("super_admin_login.html")

    # POST method
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
        session["super_admin"] = True
        flash("Super admin paneliga kirish muvaffaqiyatli!", "success")
        return redirect(url_for("super_admin_dashboard"))
    else:
        flash("Noto'g'ri login yoki parol!", "error")
        return render_template("super_admin_login.html")

@app.route("/super-admin-dashboard-ultimate-m4st3r")
def super_admin_dashboard():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()

        # Xodimlar ma'lumotlari - xavfsiz olish va dict ga aylantirish
        staff_db = []
        try:
            cur.execute("SELECT * FROM staff ORDER BY created_at DESC")
            staff_raw = cur.fetchall() or []
            for staff in staff_raw:
                try:
                    # SQLite Row obyektini xavfsiz dict ga aylantirish
                    if hasattr(staff, 'keys'):
                        staff_dict = dict(staff)
                    else:
                        # Tuple format uchun manual dict yaratish
                        staff_dict = {
                            'id': int(staff[0]) if staff[0] is not None else 0,
                            'first_name': str(staff[1]) if len(staff) > 1 and staff[1] is not None else '',
                            'last_name': str(staff[2]) if len(staff) > 2 and staff[2] is not None else '',
                            'birth_date': str(staff[3]) if len(staff) > 3 and staff[3] is not None else '',
                            'phone': str(staff[4]) if len(staff) > 4 and staff[4] is not None else '',
                            'passport_series': str(staff[5]) if len(staff) > 5 and staff[5] is not None else '',
                            'passport_number': str(staff[6]) if len(staff) > 6 and staff[6] is not None else '',
                            'password_hash': str(staff[7]) if len(staff) > 7 and staff[7] is not None else '',
                            'total_hours': float(staff[8]) if len(staff) > 8 and staff[8] is not None else 0.0,
                            'orders_handled': int(staff[9]) if len(staff) > 9 and staff[9] is not None else 0,
                            'last_activity': str(staff[10]) if len(staff) > 10 and staff[10] is not None else '',
                            'created_at': str(staff[11]) if len(staff) > 11 and staff[11] is not None else ''
                        }

                    # Xavfsiz total_hours va orders_handled konversiyasi
                    try:
                        if 'total_hours' in staff_dict:
                            total_hours_val = staff_dict['total_hours']
                            if isinstance(total_hours_val, str):
                                if total_hours_val.replace('.', '').replace(',', '').isdigit():
                                    staff_dict['total_hours'] = float(total_hours_val.replace(',', '.'))
                                else:
                                    staff_dict['total_hours'] = 0.0
                            elif total_hours_val is None:
                                staff_dict['total_hours'] = 0.0
                            else:
                                staff_dict['total_hours'] = float(total_hours_val)
                    except (ValueError, TypeError):
                        staff_dict['total_hours'] = 0.0

                    try:
                        if 'orders_handled' in staff_dict:
                            orders_val = staff_dict['orders_handled']
                            if isinstance(orders_val, str):
                                if orders_val.isdigit():
                                    staff_dict['orders_handled'] = int(orders_val)
                                else:
                                    staff_dict['orders_handled'] = 0
                            elif orders_val is None:
                                staff_dict['orders_handled'] = 0
                            else:
                                staff_dict['orders_handled'] = int(orders_val)
                    except (ValueError, TypeError):
                        staff_dict['orders_handled'] = 0

                    staff_db.append(staff_dict)

                except Exception as staff_error:
                    app_logger.error(f"Staff {staff[0] if staff and len(staff) > 0 else 'N/A'} qayta ishlashda xatolik: {str(staff_error)}")
                    # Xatolik bo'lsa ham minimal ma'lumot bilan davom etish
                    try:
                        staff_db.append({
                            'id': int(staff[0]) if staff and len(staff) > 0 and staff[0] is not None else 0,
                            'first_name': str(staff[1]) if staff and len(staff) > 1 and staff[1] is not None else 'N/A',
                            'last_name': str(staff[2]) if staff and len(staff) > 2 and staff[2] is not None else 'N/A',
                            'birth_date': str(staff[3]) if staff and len(staff) > 3 and staff[3] is not None else 'N/A',
                            'phone': str(staff[4]) if staff and len(staff) > 4 and staff[4] is not None else 'N/A',
                            'passport_series': 'N/A',
                            'passport_number': 'N/A',
                            'password_hash': '',
                            'total_hours': 0.0,
                            'orders_handled': 0,
                            'last_activity': '',
                            'created_at': str(staff[11]) if staff and len(staff) > 11 and staff[11] is not None else ''
                        })
                    except:
                        continue

        except Exception as e:
            app_logger.error(f"Staff ma'lumotlarini olishda xatolik: {str(e)}")
            staff_db = []  # Bo'sh list bilan davom etish

        # Kuryerlar ma'lumotlari - xavfsiz olish va dict ga aylantirish
        couriers_db = []
        try:
            cur.execute("SELECT * FROM couriers ORDER BY created_at DESC")
            couriers_raw = cur.fetchall() or []
            for courier in couriers_raw:
                try:
                    # SQLite Row obyektini xavfsiz dict ga aylantirish
                    if hasattr(courier, 'keys'):
                        courier_dict = dict(courier)
                    else:
                        # Tuple format uchun manual dict yaratish
                        courier_dict = {
                            'id': int(courier[0]) if courier[0] is not None else 0,
                            'first_name': str(courier[1]) if len(courier) > 1 and courier[1] is not None else '',
                            'last_name': str(courier[2]) if len(courier) > 2 and courier[2] is not None else '',
                            'birth_date': str(courier[3]) if len(courier) > 3 and courier[3] is not None else '',
                            'phone': str(courier[4]) if len(courier) > 4 and courier[4] is not None else '',
                            'passport_series': str(courier[5]) if len(courier) > 5 and courier[5] is not None else '',
                            'passport_number': str(courier[6]) if len(courier) > 6 and courier[6] is not None else '',
                            'password_hash': str(courier[7]) if len(courier) > 7 and courier[7] is not None else '',
                            'total_hours': float(courier[8]) if len(courier) > 8 and courier[8] is not None else 0.0,
                            'deliveries_completed': int(courier[9]) if len(courier) > 9 and courier[9] is not None else 0,
                            'last_activity': str(courier[10]) if len(courier) > 10 and courier[10] is not None else '',
                            'created_at': str(courier[11]) if len(courier) > 11 and courier[11] is not None else ''
                        }

                    # Xavfsiz total_hours va deliveries_completed konversiyasi
                    try:
                        if 'total_hours' in courier_dict:
                            total_hours_val = courier_dict['total_hours']
                            if isinstance(total_hours_val, str):
                                if total_hours_val.replace('.', '').replace(',', '').isdigit():
                                    courier_dict['total_hours'] = float(total_hours_val.replace(',', '.'))
                                else:
                                    courier_dict['total_hours'] = 0.0
                            elif total_hours_val is None:
                                courier_dict['total_hours'] = 0.0
                            else:
                                courier_dict['total_hours'] = float(total_hours_val)
                    except (ValueError, TypeError):
                        courier_dict['total_hours'] = 0.0

                    try:
                        if 'deliveries_completed' in courier_dict:
                            deliveries_val = courier_dict['deliveries_completed']
                            if isinstance(deliveries_val, str):
                                if deliveries_val.isdigit():
                                    courier_dict['deliveries_completed'] = int(deliveries_val)
                                else:
                                    courier_dict['deliveries_completed'] = 0
                            elif deliveries_val is None:
                                courier_dict['deliveries_completed'] = 0
                            else:
                                courier_dict['deliveries_completed'] = int(deliveries_val)
                    except (ValueError, TypeError):
                        courier_dict['deliveries_completed'] = 0

                    couriers_db.append(courier_dict)

                except Exception as courier_error:
                    app_logger.error(f"Courier {courier[0] if courier and len(courier) > 0 else 'N/A'} qayta ishlashda xatolik: {str(courier_error)}")
                    # Xatolik bo'lsa ham minimal ma'lumot bilan davom etish
                    try:
                        couriers_db.append({
                            'id': int(courier[0]) if courier and len(courier) > 0 and courier[0] is not None else 0,
                            'first_name': str(courier[1]) if courier and len(courier) > 1 and courier[1] is not None else 'N/A',
                            'last_name': str(courier[2]) if courier and len(courier) > 2 and courier[2] is not None else 'N/A',
                            'birth_date': str(courier[3]) if courier and len(courier) > 3 and courier[3] is not None else 'N/A',
                            'phone': str(courier[4]) if courier and len(courier) > 4 and courier[4] is not None else 'N/A',
                            'passport_series': 'N/A',
                            'passport_number': 'N/A',
                            'password_hash': '',
                            'total_hours': 0.0,
                            'deliveries_completed': 0,
                            'last_activity': '',
                            'created_at': str(courier[11]) if courier and len(courier) > 11 and courier[11] is not None else ''
                        })
                    except:
                        continue

        except Exception as e:
            app_logger.error(f"Couriers ma'lumotlarini olishda xatolik: {str(e)}")
            couriers_db = []  # Bo'sh list bilan davom etish

        # Foydalanuvchilarni olish - xavfsiz va dict ga aylantirish
        users_db = []
        try:
            cur.execute("SELECT * FROM users ORDER BY created_at DESC")
            users_raw = cur.fetchall() or []
            for user in users_raw:
                try:
                    # SQLite Row obyektini xavfsiz dict ga aylantirish
                    if hasattr(user, 'keys'):
                        user_dict = dict(user)
                    else:
                        # Tuple format uchun manual dict yaratish
                        user_dict = {
                            'id': int(user[0]) if user[0] is not None else 0,
                            'first_name': str(user[1]) if len(user) > 1 and user[1] is not None else '',
                            'last_name': str(user[2]) if len(user) > 2 and user[2] is not None else '',
                            'email': str(user[3]) if len(user) > 3 and user[3] is not None else '',
                            'phone': str(user[4]) if len(user) > 4 and user[4] is not None else '',
                            'password_hash': str(user[5]) if len(user) > 5 and user[5] is not None else '',
                            'address': str(user[6]) if len(user) > 6 and user[6] is not None else '',
                            'card_number': str(user[7]) if len(user) > 7 and user[7] is not None else '',
                            'card_expiry': str(user[8]) if len(user) > 8 and user[8] is not None else '',
                            'created_at': str(user[9]) if len(user) > 9 and user[9] is not None else ''
                        }

                    users_db.append(user_dict)

                except Exception as user_error:
                    app_logger.error(f"User {user[0] if user and len(user) > 0 else 'N/A'} qayta ishlashda xatolik: {str(user_error)}")
                    # Xatolik bo'lsa ham minimal ma'lumot bilan davom etish
                    try:
                        users_db.append({
                            'id': int(user[0]) if user and len(user) > 0 and user[0] is not None else 0,
                            'first_name': str(user[1]) if user and len(user) > 1 and user[1] is not None else 'N/A',
                            'last_name': str(user[2]) if user and len(user) > 2 and user[2] is not None else 'N/A',
                            'email': str(user[3]) if user and len(user) > 3 and user[3] is not None else 'N/A',
                            'phone': 'N/A',
                            'password_hash': '',
                            'address': 'N/A',
                            'card_number': 'N/A',
                            'card_expiry': 'N/A',
                            'created_at': str(user[9]) if user and len(user) > 9 and user[9] is not None else ''
                        })
                    except:
                        continue

        except Exception as e:
            app_logger.error(f"Users ma'lumotlarini olishda xatolik: {str(e)}")
            users_db = []  # Bo'sh list bilan davom etish

        # JSON fayldan foydalanuvchilarni olish - xavfsiz
        users_json = []
        users_file = 'users.json'
        if os.path.exists(users_file):
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_json = json.load(f) or []
            except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                app_logger.warning(f"Users JSON faylini o'qishda xatolik: {str(e)}")
                users_json = []

        # Savollarni olish - xavfsiz
        try:
            cur.execute("SELECT * FROM questions ORDER BY created_at DESC")
            questions = cur.fetchall() or []
        except Exception as e:
            app_logger.error(f"Questions ma'lumotlarini olishda xatolik: {str(e)}")
            questions = []

        # Filiallarni olish - xavfsiz va baho qo'shish
        branches = []
        try:
            cur.execute("SELECT * FROM branches ORDER BY created_at DESC")
            branches_raw = cur.fetchall() or []

            for branch_row in branches_raw:
                try:
                    # Safe access to branch data, assuming branch_row is a dictionary-like object from fetchall
                    if hasattr(branch_row, 'keys'):
                        branch_dict = dict(zip(branch_row.keys(), branch_row))
                    else:
                        # Tuple format uchun manual dict yaratish
                        branch_dict = {
                            'id': int(branch_row[0]) if len(branch_row) > 0 and branch_row[0] is not None else 0,
                            'name': str(branch_row[1]) if len(branch_row) > 1 and branch_row[1] is not None else 'N/A',
                            'address': str(branch_row[2]) if len(branch_row) > 2 and branch_row[2] is not None else 'N/A',
                            'latitude': 0.0,
                            'longitude': 0.0,
                            'phone': str(branch_row[5]) if len(branch_row) > 5 and branch_row[5] is not None else 'N/A',
                            'working_hours': str(branch_row[6]) if len(branch_row) > 6 and branch_row[6] is not None else '09:00-22:00',
                            'is_active': int(branch_row[7]) if len(branch_row) > 7 and branch_row[7] is not None else 1,
                            'delivery_radius': 15.0,
                            'created_at': str(branch_row[9]) if len(branch_row) > 9 and branch_row[9] is not None else ''
                        }

                        # Safe coordinate conversion
                        try:
                            if len(branch_row) > 3 and branch_row[3] is not None:
                                lat_val = branch_row[3]
                                try:
                                    if isinstance(lat_val, str):
                                        # String bo'lsa, raqamga aylantirish
                                        clean_lat = str(lat_val).replace(',', '.').strip()
                                        if clean_lat and clean_lat.replace('.', '').replace('-', '').isdigit():
                                            branch_dict['latitude'] = float(clean_lat)
                                        else:
                                            branch_dict['latitude'] = 41.2995  # Default Toshkent koordinatasi
                                    elif isinstance(lat_val, (int, float)):
                                        branch_dict['latitude'] = float(lat_val)
                                    else:
                                        branch_dict['latitude'] = 41.2995
                                except (ValueError, TypeError) as coord_error:
                                    app_logger.warning(f"Latitude conversion error: {str(coord_error)}")
                                    branch_dict['latitude'] = 41.2995
                            else:
                                branch_dict['latitude'] = 41.2995
                        except Exception as lat_error:
                            app_logger.error(f"Latitude processing error: {str(lat_error)}")
                            branch_dict['latitude'] = 41.2995

                        try:
                            if len(branch_row) > 4 and branch_row[4] is not None:
                                lng_val = branch_row[4]
                                if isinstance(lng_val, (int, float)):
                                    branch_dict['longitude'] = float(lng_val)
                                elif isinstance(lng_val, str) and lng_val.replace(',', '.').strip():
                                    # String dan float ga xavfsiz aylantirish
                                    clean_lng = lng_val.replace(',', '.').strip()
                                    if clean_lng and clean_lng != '':
                                        try:
                                            branch_dict['longitude'] = float(clean_lng)
                                        except (ValueError, TypeError):
                                            branch_dict['longitude'] = 0.0
                                    else:
                                        branch_dict['longitude'] = 0.0
                                else:
                                    branch_dict['longitude'] = 0.0
                            else:
                                branch_dict['longitude'] = 0.0
                        except (ValueError, TypeError):
                            branch_dict['longitude'] = 0.0

                        try:
                            if len(branch_row) > 8 and branch_row[8] is not None:
                                radius_val = branch_row[8]
                                if isinstance(radius_val, (int, float)):
                                    branch_dict['delivery_radius'] = float(radius_val)
                                elif isinstance(radius_val, str) and radius_val.replace('.', '').isdigit():
                                    branch_dict['delivery_radius'] = float(radius_val)
                                else:
                                    branch_dict['delivery_radius'] = 15.0
                            else:
                                branch_dict['delivery_radius'] = 15.0
                        except (ValueError, TypeError):
                            branch_dict['delivery_radius'] = 15.0


                    # Baho ma'lumotlarini xavfsiz olish
                    try:
                        rating_data = get_branch_average_rating(int(branch_dict['id']))
                        branch_dict['average_rating'] = float(rating_data.get('average_rating', 0.0))
                        branch_dict['total_ratings'] = int(rating_data.get('total_ratings', 0))
                    except Exception as rating_error:
                        app_logger.warning(f"Branch {branch_dict['id']} bahosini olishda xatolik: {str(rating_error)}")
                        branch_dict['average_rating'] = 0.0
                        branch_dict['total_ratings'] = 0

                    branches.append(branch_dict)

                except Exception as branch_error:
                    app_logger.error(f"Branch ma'lumotini qayta ishlashda xatolik: {str(branch_error)}")
                    continue

        except Exception as e:
            app_logger.error(f"Branches ma'lumotlarini olishda xatolik: {str(e)}")
            branches = []

        # Buyurtmalar statistikasi - xavfsiz hisoblash
        stats = {
            'total_orders': 0,
            'waiting_orders': 0,
            'ready_orders': 0,
            'served_orders': 0,
            'month_orders': 0,
            'total_staff': len(staff_db),
            'total_couriers': len(couriers_db),
            'total_users': len(users_db),
            'total_users_json': len(users_json)
        }

        try:
            # Jami buyurtmalar
            cur.execute("SELECT COUNT(*) FROM orders")
            result = cur.fetchone()
            stats['total_orders'] = result[0] if result else 0

            # Status bo'yicha statistika
            status_queries = [
                ('waiting_orders', "SELECT COUNT(*) FROM orders WHERE status='waiting'"),
                ('ready_orders', "SELECT COUNT(*) FROM orders WHERE status='ready'"),
                ('served_orders', "SELECT COUNT(*) FROM orders WHERE status='served'")
            ]

            for stat_key, query in status_queries:
                try:
                    cur.execute(query)
                    result = cur.fetchone()
                    stats[stat_key] = result[0] if result else 0
                except Exception as e:
                    app_logger.warning(f"{stat_key} statistikasini olishda xatolik: {str(e)}")
                    stats[stat_key] = 0

            # Bu oylik statistika
            try:
                current_month = get_current_time().strftime("%Y-%m")
                cur.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (f"{current_month}%",))
                result = cur.fetchone()
                stats['month_orders'] = result[0] if result else 0
            except Exception as e:
                app_logger.warning(f"Oylik statistikani olishda xatolik: {str(e)}")
                stats['month_orders'] = 0

        except Exception as e:
            app_logger.error(f"Statistikalarni hisoblashda xatolik: {str(e)}")

        if conn:
            conn.close()

        return render_template("super_admin_dashboard.html",
                             staff_db=staff_db or [],
                             couriers_db=couriers_db or [],
                             users_db=users_db or [],
                             users_json=users_json or [],
                             questions=questions or [],
                             branches=branches or [],
                             stats=stats)

    except Exception as e:
        app_logger.error(f"Super admin dashboard xatoligi: {str(e)}")
        if conn:
            try:
                conn.close()
            except:
                pass

        # Emergency fallback
        try:
            return render_template("super_admin_dashboard.html",
                                 staff_db=[],
                                 couriers_db=[],
                                 users_db=[],
                                 users_json=[],
                                 questions=[],
                                 branches=[],
                                 stats={'total_orders': 0, 'waiting_orders': 0, 'ready_orders': 0,
                                       'served_orders': 0, 'month_orders': 0, 'total_staff': 0,
                                       'total_couriers': 0, 'total_users': 0, 'total_users_json': 0})
        except Exception as template_error:
            app_logger.critical(f"Template render ham ishlamadi: {str(template_error)}")
            return f"""
            <h1>Super Admin Dashboard</h1>
            <p>Dashboard yuklashda xatolik: {str(e)}</p>
            <a href="{url_for('super_admin_login')}">Login sahifasiga qaytish</a>
            """, 500

@app.route("/super-admin/delete-staff/<int:staff_id>", methods=["POST"])
def super_admin_delete_staff(staff_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    conn.commit()
    conn.close()

    # JSON fayldan ham o'chirish
    employees_file = 'employees.json'
    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)

            employees = [emp for emp in employees if emp.get('id') != staff_id]

            with open(employees_file, 'w', encoding='utf-8') as f:
                json.dump(employees, f, ensure_ascii=False, indent=2)
        except:
            pass

    flash(f"Xodim #{staff_id} o'chirildi.", "success")
    return redirect(url_for("super_admin_dashboard"))

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

    if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)
    now = get_current_time()
    cur.execute("""
        INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

    new_id = cur.lastrowid
    # ID kamida 5 ta raqamdan iborat bo'lishi uchun
    if new_id < 10000:
        cur.execute("UPDATE staff SET id = ? WHERE id = ?", (10000 + new_id, new_id))
        new_id = 10000 + new_id

    conn.commit()
    conn.close()

    # JSON fayliga ham saqlash
    save_staff_to_json(first_name, last_name, birth_date, phone, new_id, now)

    flash(f"Yangi xodim qo'shildi. ID: {new_id}", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/add-menu-item", methods=["POST"])
def super_admin_add_menu_item():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    name = request.form.get("name", "").strip()
    price = request.form.get("price", "")
    category = request.form.get("category", "")
    description = request.form.get("description", "").strip()

    if not all([name, price, category]):
        flash("Barcha majburiy maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        price = float(price)
    except ValueError:
        flash("Narx raqam bo'lishi kerak.", "error")
        return redirect(url_for("super_admin_dashboard"))

    # Rasm yuklash
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            import uuid
            from werkzeug.utils import secure_filename

            images_dir = os.path.join('static', 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(images_dir, unique_filename)

            try:
                file.save(file_path)
                image_url = f"/static/images/{unique_filename}"
            except Exception as e:
                flash("Rasmni yuklashda xatolik yuz berdi.", "error")
                return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()

    cur.execute("INSERT INTO menu_items (name, price, category, description, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
               (name, price, category, description, image_url, now))

    conn.commit()
    conn.close()
    flash("Yangi mahsulot qo'shildi!", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/add-branch", methods=["POST"])
def super_admin_add_branch():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    name = request.form.get("name", "").strip()
    address = request.form.get("address", "").strip()
    latitude = request.form.get("latitude", "")
    longitude = request.form.get("longitude", "")
    phone = request.form.get("phone", "").strip()
    working_hours = request.form.get("working_hours", "09:00-22:00")
    delivery_radius = request.form.get("delivery_radius", "15")

    if not all([name, address, latitude, longitude]):
        flash("Barcha majburiy maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        delivery_radius = float(delivery_radius)
    except ValueError:
        flash("Koordinatalar va yetkazish radiusi raqam bo'lishi kerak.", "error")
        return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()

    cur.execute("""
        INSERT INTO branches (name, address, latitude, longitude, phone, working_hours, delivery_radius, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, address, latitude, longitude, phone, working_hours, delivery_radius, now))

    conn.commit()
    conn.close()
    flash("Yangi filial qo'shildi!", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/delete-branch/<int:branch_id>", methods=["POST"])
def super_admin_delete_branch(branch_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM branches WHERE id = ?", (branch_id,))
    conn.commit()
    conn.close()

    flash(f"Filial #{branch_id} o'chirildi.", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/logout")
def super_admin_logout():
    """Super admin panelidan chiqish"""
    session.pop("super_admin", None)
    flash("Super admin panelidan chiqdingiz.", "info")
    return redirect(url_for("index"))

@app.route("/api/dashboard-stats")
@login_required
def api_dashboard_stats():
    """Dashboard statistikalarini JSON formatida qaytarish"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Asosiy statistikalar
        stats = {}
        
        # Jami buyurtmalar
        cur.execute("SELECT COUNT(*) FROM orders")
        stats['total_orders'] = cur.fetchone()[0]
        
        # Status bo'yicha statistika
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting'")
        stats['waiting_orders'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='ready'")
        stats['ready_orders'] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='served'")
        stats['served_orders'] = cur.fetchone()[0]
        
        # Bu oylik statistika
        current_month = get_current_time().strftime("%Y-%m")
        cur.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (f"{current_month}%",))
        stats['month_orders'] = cur.fetchone()[0]
        
        conn.close()
        return jsonify(stats)
        
    except Exception as e:
        app_logger.error(f"Dashboard stats API error: {str(e)}")
        return jsonify({"error": "Statistikalarni olishda xatolik"}), 500

@app.route("/contact")
def contact():
    """Aloqa sahifasi"""
    return render_template("contact.html", current_page='contact')

@app.route("/about")
def about():
    """Biz haqimizda sahifasi"""
    return render_template("about.html", current_page='about')

@app.route("/downloads")
def downloads():
    """Yuklab olish sahifasi"""
    return render_template("downloads.html", current_page='downloads')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# Missing super admin routes
@app.route("/super-admin/analytics")
def super_admin_analytics():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))
    return render_template("super_admin_analytics.html")

@app.route("/super-admin/reports")
def super_admin_reports():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))
    return render_template("super_admin_reports.html")

@app.route("/super-admin/system")
def super_admin_system():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))
    return render_template("super_admin_system.html")

@app.route("/super-admin/logs")
def super_admin_logs():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))
    return render_template("super_admin_logs.html")

@app.route("/super-admin/get-orders")
def super_admin_get_orders():
    if not session.get("super_admin"):
        return jsonify([]), 401
    
    try:
        orders = execute_query("""
            SELECT o.*,
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """, fetch_all=True)
        return jsonify([dict(order) for order in orders])
    except Exception as e:
        app_logger.error(f"Get orders error: {str(e)}")
        return jsonify([]), 500

@app.route("/super-admin/get-menu")
def super_admin_get_menu():
    if not session.get("super_admin"):
        return jsonify([]), 401
    
    try:
        menu_items = execute_query("SELECT * FROM menu_items ORDER BY category, name", fetch_all=True)
        return jsonify([dict(item) for item in menu_items])
    except Exception as e:
        app_logger.error(f"Get menu error: {str(e)}")
        return jsonify([]), 500

@app.route("/super-admin/get-receipts")
def super_admin_get_receipts():
    if not session.get("super_admin"):
        return jsonify([]), 401
    
    try:
        receipts = execute_query("SELECT * FROM receipts ORDER BY created_at DESC", fetch_all=True)
        return jsonify([dict(receipt) for receipt in receipts])
    except Exception as e:
        app_logger.error(f"Get receipts error: {str(e)}")
        return jsonify([]), 500

@app.route("/super-admin/get-ratings")
def super_admin_get_ratings():
    if not session.get("super_admin"):
        return jsonify({"menu_ratings": [], "branch_ratings": []}), 401
    
    try:
        # Mahsulot baholari
        menu_ratings = execute_query("""
            SELECT r.*, u.first_name || ' ' || u.last_name as user_name, m.name as menu_item_name
            FROM ratings r
            JOIN users u ON r.user_id = u.id
            JOIN menu_items m ON r.menu_item_id = m.id
            WHERE r.menu_item_id > 0
            ORDER BY r.created_at DESC
        """, fetch_all=True)
        
        # Filial baholari (menu_item_id manfiy bo'lganlar)
        branch_ratings = execute_query("""
            SELECT r.*, u.first_name || ' ' || u.last_name as user_name, b.name as branch_name
            FROM ratings r
            JOIN users u ON r.user_id = u.id
            JOIN branches b ON b.id = ABS(r.menu_item_id)
            WHERE r.menu_item_id < 0
            ORDER BY r.created_at DESC
        """, fetch_all=True)
        
        return jsonify({
            "menu_ratings": [dict(rating) for rating in menu_ratings],
            "branch_ratings": [dict(rating) for rating in branch_ratings]
        })
    except Exception as e:
        app_logger.error(f"Get ratings error: {str(e)}")
        return jsonify({"menu_ratings": [], "branch_ratings": []}), 500

@app.route("/super-admin/delete-courier/<int:courier_id>", methods=["POST"])
def super_admin_delete_courier(courier_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        execute_query("DELETE FROM couriers WHERE id = ?", (courier_id,))
        flash(f"Kuryer #{courier_id} o'chirildi.", "success")
    except Exception as e:
        app_logger.error(f"Delete courier error: {str(e)}")
        flash("Kuryerni o'chirishda xatolik yuz berdi.", "error")
    
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

    if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        password_hash = generate_password_hash(password)
        now = get_current_time().isoformat()
        
        new_id = execute_query("""
            INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now))

        # ID kamida 5 ta raqamdan iborat bo'lishi uchun
        if new_id < 10000:
            execute_query("UPDATE couriers SET id = ? WHERE id = ?", (10000 + new_id, new_id))
            new_id = 10000 + new_id

        flash(f"Yangi kuryer qo'shildi. ID: {new_id}", "success")
    except Exception as e:
        app_logger.error(f"Add courier error: {str(e)}")
        flash("Kuryer qo'shishda xatolik yuz berdi.", "error")
    
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/delete-user-db/<int:user_id>", methods=["POST"])
def super_admin_delete_user_db(user_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        execute_query("DELETE FROM users WHERE id = ?", (user_id,))
        flash(f"Foydalanuvchi #{user_id} o'chirildi.", "success")
    except Exception as e:
        app_logger.error(f"Delete user error: {str(e)}")
        flash("Foydalanuvchini o'chirishda xatolik yuz berdi.", "error")
    
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/delete-user", methods=["POST"])
def super_admin_delete_user():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    ticket_no = request.form.get("ticket_no")
    if not ticket_no:
        flash("Ticket raqami topilmadi.", "error")
        return redirect(url_for("super_admin_dashboard"))

    # JSON fayldan o'chirish
    users_file = 'users.json'
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)

            users = [user for user in users if str(user.get('buyurtma_raqami')) != str(ticket_no)]

            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
                
            flash(f"Buyurtma #{ticket_no} o'chirildi.", "success")
        except Exception as e:
            app_logger.error(f"Delete user JSON error: {str(e)}")
            flash("Buyurtmani o'chirishda xatolik yuz berdi.", "error")
    
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/toggle-branch/<int:branch_id>", methods=["POST"])
def super_admin_toggle_branch(branch_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    try:
        execute_query("UPDATE branches SET is_active = NOT is_active WHERE id = ?", (branch_id,))
        flash(f"Filial #{branch_id} holati o'zgartirildi.", "success")
    except Exception as e:
        app_logger.error(f"Toggle branch error: {str(e)}")
        flash("Filial holatini o'zgartirishda xatolik yuz berdi.", "error")
    
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/reset-staff-password", methods=["POST"])
def super_admin_reset_staff_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    staff_id = data.get("staff_id")
    new_password = data.get("new_password")

    if not staff_id or not new_password:
        return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

    try:
        password_hash = generate_password_hash(new_password)
        execute_query("UPDATE staff SET password_hash = ? WHERE id = ?", (password_hash, staff_id))
        return jsonify({"success": True, "message": "Parol yangilandi"})
    except Exception as e:
        app_logger.error(f"Reset staff password error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})

@app.route("/super-admin/reset-courier-password", methods=["POST"])
def super_admin_reset_courier_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    courier_id = data.get("courier_id")
    new_password = data.get("new_password")

    if not courier_id or not new_password:
        return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

    try:
        password_hash = generate_password_hash(new_password)
        execute_query("UPDATE couriers SET password_hash = ? WHERE id = ?", (password_hash, courier_id))
        return jsonify({"success": True, "message": "Parol yangilandi"})
    except Exception as e:
        app_logger.error(f"Reset courier password error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})

@app.route("/super-admin/reset-user-password", methods=["POST"])
def super_admin_reset_user_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json()
    user_id = data.get("user_id")
    new_password = data.get("new_password")

    if not user_id or not new_password:
        return jsonify({"success": False, "message": "Ma'lumotlar to'liq emas"})

    try:
        password_hash = generate_password_hash(new_password)
        execute_query("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        return jsonify({"success": True, "message": "Parol yangilandi"})
    except Exception as e:
        app_logger.error(f"Reset user password error: {str(e)}")
        return jsonify({"success": False, "message": "Xatolik yuz berdi"})

@app.route("/api/super-admin/dashboard-stats")
def api_super_admin_dashboard_stats():
    """Super admin dashboard statistikalari"""
    if not session.get("super_admin"):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Asosiy statistikalar
        stats = {}
        
        # Jami buyurtmalar
        result = execute_query("SELECT COUNT(*) FROM orders", fetch_one=True)
        stats['total_orders'] = result[0] if result else 0
        
        # Status bo'yicha statistika
        result = execute_query("SELECT COUNT(*) FROM orders WHERE status='waiting'", fetch_one=True)
        stats['waiting_orders'] = result[0] if result else 0
        
        result = execute_query("SELECT COUNT(*) FROM orders WHERE status='ready'", fetch_one=True)
        stats['ready_orders'] = result[0] if result else 0
        
        result = execute_query("SELECT COUNT(*) FROM orders WHERE status='served'", fetch_one=True)
        stats['served_orders'] = result[0] if result else 0
        
        # Bu oylik statistika
        current_month = get_current_time().strftime("%Y-%m")
        result = execute_query("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (f"{current_month}%",), fetch_one=True)
        stats['month_orders'] = result[0] if result else 0
        
        # Xodimlar statistikasi
        result = execute_query("SELECT COUNT(*) FROM staff", fetch_one=True)
        stats['total_staff'] = result[0] if result else 0
        
        result = execute_query("SELECT COUNT(*) FROM couriers", fetch_one=True)
        stats['total_couriers'] = result[0] if result else 0
        
        result = execute_query("SELECT COUNT(*) FROM users", fetch_one=True)
        stats['total_users'] = result[0] if result else 0
        
        return jsonify({"stats": stats})
        
    except Exception as e:
        app_logger.error(f"Super admin dashboard stats error: {str(e)}")
        return jsonify({"error": "Statistikalarni olishda xatolik"}), 500

