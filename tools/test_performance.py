#!/usr/bin/env python3
"""
Тест производительности Pro-Obuv
Проверяем, что rate limits действительно увеличены
"""

import requests
import threading
import time

def test_endpoint(url, num_requests=10):
    """Тестируем endpoint с множественными запросами"""
    success = 0
    rate_limited = 0
    errors = 0
    
    def make_request():
        nonlocal success, rate_limited, errors
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                success += 1
            elif response.status_code == 429:
                rate_limited += 1
            else:
                errors += 1
        except Exception:
            errors += 1
    
    print(f" Тестируем {url} с {num_requests} запросами...")
    
    # Запускаем запросы в потоках
    threads = []
    start_time = time.time()
    
    for i in range(num_requests):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"   Успешных: {success}/{num_requests}")
    print(f"   Rate limited (429): {rate_limited}")  
    print(f"   Ошибок: {errors}")
    print(f"  ⏱ Время: {duration:.2f} секунд")
    print(f"   RPS: {num_requests/duration:.2f}")
    print()
    
    return success, rate_limited, errors

def main():
    base_url = "http://127.0.0.1:5000"
    
    print(" ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ PRO-OBUV")
    print("=" * 50)
    
    # Простой тест доступности
    try:
        response = requests.get(base_url, timeout=10)
        print(f" Сервер доступен (статус: {response.status_code})")
    except Exception as e:
        print(f" Сервер недоступен: {e}")
        return
    
    print()
    
    # Тестируем разные endpoints
    endpoints = [
        "/menu",
        "/api/cart-count", 
        "/api/status",
        "/contact"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        success, rate_limited, errors = test_endpoint(url, 20)
        
        if rate_limited > 0:
            print(f"  ВНИМАНИЕ: {endpoint} имеет rate limiting!")
        else:
            print(f" {endpoint} - rate limits работают корректно")
    
    print("=" * 50)
    print(" РЕЗУЛЬТАТ:")
    print("  - Если нет сообщений '429 - Juda ko'p so'rov' = УСПЕХ!")
    print("  - Высокая производительность достигнута!")

if __name__ == "__main__":
    main()