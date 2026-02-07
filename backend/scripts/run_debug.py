#!/usr/bin/env python3
"""
Отладочный скрипт для запуска приложения Pro-Obuv
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Импорт основного приложения
    from app import app
    
    print(" Успешно импортировано приложение Flask")
    print(" Все зависимости установлены")
    
    # Проверка ключевых роутов
    print("\n Доступные роуты:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint in ['menu', 'index', 'cart', 'contact']:
            print(f"  - {rule.rule} -> {rule.endpoint}")
    
    # Запуск в режиме отладки
    print("\n Запуск приложения...")
    print(" Откройте http://127.0.0.1:5000 в браузере")
    print(" Или http://127.0.0.1:5000/menu для прямого доступа к меню")
    print("  Нажмите Ctrl+C для остановки")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,  # Избегаем дублирования процессов
        threaded=True
    )
    
except ImportError as e:
    print(f" Ошибка импорта: {e}")
    print("\n Установите недостающие зависимости:")
    print("pip install flask flask-cors flask-compress flask-limiter pandas openpyxl")
    sys.exit(1)
    
except Exception as e:
    print(f" Ошибка запуска приложения: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)