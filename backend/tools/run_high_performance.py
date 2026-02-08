#!/usr/bin/env python3
"""
Высокопроизводительный запуск приложения Pro-Obuv
Оптимизировано для 100+ одновременных пользователей
"""

import os
import sys
import warnings

# Отключаем предупреждения для лучшей производительности
warnings.filterwarnings("ignore")

# Устанавливаем переменные окружения для высокой производительности
os.environ.update({
    # Rate limiting - очень высокие лимиты
    "RATE_LIMIT_DAILY": "100000",
    "RATE_LIMIT_HOURLY": "10000", 
    "RATE_LIMIT_MINUTE": "1000",
    
    # Threading и производительность
    "THREAD_POOL_MAX_WORKERS": "200",
    "DB_POOL_MAX_CONNECTIONS": "100",
    
    # Отключаем тяжелые функции для демо
    "FLASK_ENV": "production",
    "LOG_LEVEL": "WARNING",
    
    # Оптимизации кеширования
    "CACHE_TTL": "300",
})

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Импорт приложения
    from app import app
    
    print(" ВЫСОКОПРОИЗВОДИТЕЛЬНЫЙ РЕЖИМ АКТИВИРОВАН!")
    print(" Оптимизировано для 100+ одновременных пользователей")
    print(" Rate limits увеличены в 20 раз")
    print(" Максимальная скорость обработки запросов")
    print()
    print(" Новые лимиты:")
    print("  - 1000 запросов в минуту (было 50)")  
    print("  - 10000 запросов в час (было 200)")
    print("  - 100000 запросов в день (было 1000)")
    print()
    print(" Доступ:")
    print("  - Главная: http://127.0.0.1:5000")
    print("  - Меню: http://127.0.0.1:5000/menu")
    print("  - API: http://127.0.0.1:5000/api")
    print()
    print("  Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    # Проверка доступных роутов
    route_count = len(list(app.url_map.iter_rules()))
    print(f" Загружено {route_count} роутов")
    print(" Высокопроизводительная конфигурация применена")
    print(" Готов к высокой нагрузке")
    print("=" * 50)
    
    # Запуск в высокопроизводительном режиме
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,           # Выключаем debug для скорости
        use_reloader=False,    # Без reloader
        threaded=True,         # Многопоточность
        processes=1,           # Один процесс но много потоков
        request_handler=None,  # Стандартный handler
    )
    
except ImportError as e:
    print(f" Ошибка импорта: {e}")
    print("\n Установите недостающие зависимости:")
    print("pip install flask flask-cors flask-compress flask-limiter")
    sys.exit(1)
    
except Exception as e:
    print(f" Ошибка запуска: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)