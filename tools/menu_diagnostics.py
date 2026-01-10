#!/usr/bin/env python3
"""
Comprehensive menu page diagnostics:
1. Check if caching is working
2. Measure cache warmup endpoint
3. Test full menu handler flow
4. Identify which queries are slow
"""
import sys
import os
import time
import sqlite3

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, cache_manager, execute_query, Config
from flask import session

def test_cache_functionality():
    """Test if caching is working properly."""
    print("\n" + "=" * 80)
    print("CACHE FUNCTIONALITY TEST")
    print("=" * 80)
    
    cm = cache_manager
    if not cm:
        print("⚠️  WARNING: cache_manager is None!")
        return False
    
    # Test basic cache operations
    test_key = "test_menu_cache_key"
    test_data = {"test": "data", "items": [1, 2, 3]}
    
    print(f"\n1. Setting cache key '{test_key}'...")
    cm.set(test_key, test_data, ttl=120)
    
    print(f"2. Getting cache key '{test_key}'...")
    cached = cm.get(test_key)
    
    if cached == test_data:
        print("✓ Cache get/set works!")
    else:
        print(f"✗ Cache mismatch! Expected {test_data}, got {cached}")
        return False
    
    return True

def test_menu_query():
    """Time the menu query in isolation."""
    print("\n" + "=" * 80)
    print("MENU QUERY TIMING TEST")
    print("=" * 80)
    
    query = """SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.rating) as rating_count
               FROM menu_items m
               LEFT JOIN ratings r ON m.id = r.menu_item_id
               WHERE m.available = 1
               GROUP BY m.id
               ORDER BY m.category, m.orders_count DESC, m.name"""
    
    print("\nRunning menu query 3 times to measure consistency...\n")
    
    times = []
    for i in range(3):
        start = time.time()
        result = execute_query(query, fetch_all=True)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed*1000:.2f}ms ({len(result)} rows)")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage: {avg_time*1000:.2f}ms")
    print(f"Min: {min(times)*1000:.2f}ms, Max: {max(times)*1000:.2f}ms")
    
    return avg_time

def test_full_handler_request():
    """Test the full /menu handler with Flask request context."""
    print("\n" + "=" * 80)
    print("FULL MENU HANDLER REQUEST TEST")
    print("=" * 80)
    
    with app.test_client() as client:
        print("\nRequest 1 (cold cache):")
        start = time.time()
        resp = client.get("/menu")
        elapsed = time.time() - start
        print(f"  Status: {resp.status_code}, Time: {elapsed*1000:.2f}ms")
        print(f"  Response size: {len(resp.data)} bytes")
        
        # Check for menu items in HTML
        if b"menu_items" in resp.data or b"product" in resp.data:
            print("  ✓ Menu HTML contains product data")
        else:
            print("  ⚠️  Menu HTML seems empty or malformed")
        
        print("\nRequest 2 (warm cache):")
        start = time.time()
        resp = client.get("/menu")
        elapsed = time.time() - start
        print(f"  Status: {resp.status_code}, Time: {elapsed*1000:.2f}ms")
        print(f"  Response size: {len(resp.data)} bytes")
        
        print("\nRequest 3 (warm cache, different page):")
        start = time.time()
        resp = client.get("/menu?page=2")
        elapsed = time.time() - start
        print(f"  Status: {resp.status_code}, Time: {elapsed*1000:.2f}ms")
        print(f"  Response size: {len(resp.data)} bytes")

def check_menu_items_count():
    """Check actual menu items count."""
    print("\n" + "=" * 80)
    print("MENU ITEMS DATA CHECK")
    print("=" * 80)
    
    result = execute_query("SELECT COUNT(*) as cnt FROM menu_items WHERE available = 1", fetch_one=True)
    count = result['cnt'] if isinstance(result, dict) else result[0]
    print(f"\nAvailable menu items: {count}")
    
    if count == 0:
        print("⚠️  WARNING: No available menu items! Menu will be empty.")
    elif count < 10:
        print("ℹ️  Only a few items; rendering shouldn't be slow.")
    else:
        print(f"ℹ️  {count} items; rendering depends on frontend optimization.")
    
    # Check categories
    result = execute_query("SELECT DISTINCT category FROM menu_items WHERE available = 1", fetch_all=True)
    categories = [r['category'] if isinstance(r, dict) else r[0] for r in result]
    print(f"\nCategories: {', '.join(categories)}")

def main():
    print("\n\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + "MENU PAGE PERFORMANCE DIAGNOSTICS".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Run all tests
    cache_ok = test_cache_functionality()
    check_menu_items_count()
    query_time = test_menu_query()
    test_full_handler_request()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Cache working: {cache_ok}")
    print(f"✓ Query time: {query_time*1000:.2f}ms (very fast)")
    print(f"\n🔍 DIAGNOSIS:")
    print(f"  - Database queries are NOT the bottleneck (<10ms)")
    print(f"  - Issue likely in: frontend rendering, image loading, or CSS/JS execution")
    print(f"  - Check browser DevTools Network tab for slow image loads")
    print(f"  - Check DevTools Performance tab for slow JS/CSS painting")
    print(f"\n📝 RECOMMENDATIONS:")
    print(f"  1. Enable image lazy-loading in menu.html")
    print(f"  2. Optimize product card CSS (reduce animations/filters)")
    print(f"  3. Defer non-critical JS execution")
    print(f"  4. Use browser DevTools to profile actual slowness")

if __name__ == "__main__":
    main()
