"""
Высокопроизводительная конфигурация для Pro-Obuv
Оптимизировано для 100+ одновременных пользователей
"""

import os

class HighPerformanceConfig:
    """Высокопроизводительная конфигурация"""
    
    # ===== RATE LIMITING - ОЧЕНЬ ВЫСОКИЕ ЛИМИТЫ =====
    RATE_LIMIT_DAILY = 100000      # 100k запросов в день
    RATE_LIMIT_HOURLY = 10000      # 10k запросов в час  
    RATE_LIMIT_MINUTE = 1000       # 1k запросов в минуту
    
    # ===== DATABASE OPTIMIZATION =====
    # SQLite оптимизации для высокой нагрузки
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "check_same_thread": False,
            "timeout": 120,           # Увеличен timeout
            "isolation_level": None,   # autocommit mode
        },
        "pool_timeout": 60,
        "pool_recycle": 7200,        # 2 часа
        "pool_pre_ping": True,
        "pool_size": 50,             # Большой pool
        "max_overflow": 100,         # Много overflow соединений  
        "echo": False,               # Выключаем SQL logging для производительности
    }
    
    # ===== CACHING =====
    CACHE_TTL_SHORT = 30      # 30 секунд для API
    CACHE_TTL_MEDIUM = 300    # 5 минут для страниц
    CACHE_TTL_LONG = 1800     # 30 минут для статических данных
    
    # ===== THREADING & CONCURRENCY =====
    MAX_WORKER_THREADS = 200  # Много worker потоков
    
    # ===== SESSION OPTIMIZATION =====
    PERMANENT_SESSION_LIFETIME = 86400  # 24 часа вместо 2 часов
    
    # ===== DISABLE HEAVY FEATURES =====
    WTF_CSRF_ENABLED = False        # Отключаем CSRF для скорости (ТОЛЬКО для демо!)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False          # Быстрее JSON
    JSONIFY_PRETTYPRINT_REGULAR = False  # Компактный JSON
    
    # ===== LOGGING - MINIMAL =====
    LOG_LEVEL = "WARNING"           # Минимальные логи для производительности
    
    # ===== CUSTOM LIMITS FOR ROUTES =====
    MENU_RATE_LIMIT = 10000         # Очень высокий лимит для меню
    API_RATE_LIMIT = 5000           # Высокий лимит для API
    CART_RATE_LIMIT = 2000          # Высокий лимит для корзины
    ORDER_RATE_LIMIT = 500          # Средний лимит для заказов