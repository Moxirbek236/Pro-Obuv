#!/usr/bin/env python3
"""
Menu cache warmup script.
Runs once on startup or on-demand to pre-populate cache for all languages.
This ensures the first user hit gets fast response.
"""
import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(__file__))

from app import app, cache_manager, execute_query, Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGES = ['uz', 'ru', 'en', 'kz']

def warmup_menu_cache():
    """Pre-populate menu cache for all languages."""
    print("\n" + "="*80)
    print("MENU CACHE WARMUP")
    print("="*80 + "\n")
    
    # Get menu items query result (language-agnostic data)
    menu_query = """SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.rating) as rating_count
                   FROM menu_items m
                   LEFT JOIN ratings r ON m.id = r.menu_item_id
                   WHERE m.available = 1
                   GROUP BY m.id
                   ORDER BY m.category, m.orders_count DESC, m.name"""
    
    print(f"[*] Fetching menu items from database...")
    menu_items_raw = execute_query(menu_query, fetch_all=True)
    
    if not menu_items_raw:
        print("⚠️  WARNING: No available menu items found!")
        return False
    
    print(f"✓ Got {len(menu_items_raw)} menu items\n")
    
    # Convert to dicts
    menu_items = []
    for row in menu_items_raw:
        try:
            item = dict(row)
            try:
                avg = item.get("avg_rating") if "avg_rating" in item else item.get("rating")
                item["rating"] = float(avg or 0.0)
            except:
                item["rating"] = 0.0
            try:
                item["orders_count"] = int(item.get("orders_count") or 0)
            except:
                item["orders_count"] = 0
            menu_items.append(item)
        except Exception as e:
            logger.warning(f"Menu item row error: {e}")
            continue
    
    # Warmup for each language
    cm = cache_manager
    if not cm:
        print("✗ Cache manager not available!")
        return False
    
    warmup_count = 0
    for lang in LANGUAGES:
        cache_key = f"menu_items_active:{lang}"
        try:
            cm.set(cache_key, menu_items, ttl=3600)  # 1 hour TTL
            print(f"✓ Warmed cache for language '{lang}': {cache_key}")
            warmup_count += 1
        except Exception as e:
            print(f"✗ Failed to warm cache for '{lang}': {e}")
    
    print(f"\n✓ Successfully warmed {warmup_count}/{len(LANGUAGES)} language caches")
    return warmup_count == len(LANGUAGES)

def monitor_cache_hits():
    """Monitor how often each cache entry is hit (if logger available)."""
    print("\n" + "="*80)
    print("CACHE HIT MONITORING")
    print("="*80 + "\n")
    
    cm = cache_manager
    if not cm:
        print("Cache manager not available")
        return
    
    for lang in LANGUAGES:
        cache_key = f"menu_items_active:{lang}"
        try:
            data = cm.get(cache_key)
            if data:
                print(f"✓ Cache hit for '{lang}': {len(data)} items cached")
            else:
                print(f"✗ Cache miss for '{lang}': no data")
        except Exception as e:
            print(f"✗ Error checking cache for '{lang}': {e}")

if __name__ == "__main__":
    # Create app context
    with app.app_context():
        success = warmup_menu_cache()
        monitor_cache_hits()
        
        if success:
            print("\n✓ Cache warmup complete!")
            sys.exit(0)
        else:
            print("\n✗ Cache warmup incomplete or failed")
            sys.exit(1)
