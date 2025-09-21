#!/usr/bin/env python3
"""
Database migration script to update product categories.
Updates existing 'product' category to new specific shoe categories.
"""

import sys
import os
import sqlite3
import datetime
import pytz

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_current_time():
    TASHKENT_TZ = pytz.timezone("Asia/Tashkent")
    return datetime.datetime.now(TASHKENT_TZ)

def get_db():
    """Create database connection"""
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.sqlite3")
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=60.0)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_categories():
    """Migrate existing product categories to specific shoe categories"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        print("Starting category migration...")
        
        # Get current menu items
        cur.execute("SELECT id, name, category FROM menu_items")
        items = cur.fetchall()
        
        print(f"Found {len(items)} items to process")
        
        # Category mapping based on item names
        category_mappings = {
            # Keywords -> category mapping
            'tufli': 'tufli',
            'klassik': 'tufli',
            'biznes': 'tufli',
            'formal': 'tufli',
            
            'etik': 'etik',
            'boot': 'etik',
            'qishki': 'etik',
            'ishchi': 'etik',
            
            'krosovka': 'krosovka',
            'sneaker': 'krosovka',
            'sport': 'krosovka',
            'running': 'krosovka',
            
            'mokasima': 'mokasima',
            'loafer': 'mokasima',
            'casual': 'mokasima',
            
            'botik': 'botik',
            'flat': 'botik',
            'ayol': 'botik',
            
            'tapochka': 'tapochka',
            'slipper': 'tapochka',
            'uy': 'tapochka',
            'hammom': 'tapochka',
        }
        
        updates_made = 0
        
        for item in items:
            item_id, name, current_category = item
            name_lower = name.lower()
            
            # Determine new category based on name
            new_category = None
            for keyword, category in category_mappings.items():
                if keyword in name_lower:
                    new_category = category
                    break
            
            # If no specific category found, default to 'krosovka' for general products
            if not new_category and current_category in ['product', 'men', 'women']:
                new_category = 'krosovka'
            
            # Update if category needs to change
            if new_category and new_category != current_category:
                cur.execute(
                    "UPDATE menu_items SET category = ? WHERE id = ?",
                    (new_category, item_id)
                )
                print(f"Updated '{name}': {current_category} -> {new_category}")
                updates_made += 1
        
        conn.commit()
        print(f"Migration completed! Updated {updates_made} items.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def add_sample_data():
    """Add more sample data with proper categories"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Check if we need to add more sample data
        cur.execute("SELECT COUNT(*) FROM menu_items WHERE category IN ('sandal', 'tuflya')")
        count = cur.fetchone()[0]
        
        if count == 0:
            now = get_current_time().isoformat()
            
            additional_items = [
                # Sandal kategoriyasi
                (
                    "Yozgi Sandal - Ayollar",
                    320000,
                    "sandal",
                    "Qulay yozgi sandal, issiq kunlar uchun",
                    "/static/images/summer-sandals.jpg",
                    1,
                    40,
                    15,
                    4.3,
                    10.0,
                    "35,36,37,38,39,40",
                    "jigarrang,qora,oq",
                    now,
                ),
                (
                    "Sport Sandal",
                    280000,
                    "sandal",
                    "Faol dam olish uchun sport sandal",
                    "/static/images/sport-sandals.jpg",
                    1,
                    30,
                    8,
                    4.1,
                    0.0,
                    "36,37,38,39,40,41,42",
                    "qora,kulrang,ko'k",
                    now,
                ),
                # Tuflya kategoriyasi
                (
                    "Baland Poshnali Tuflya",
                    650000,
                    "tuflya",
                    "Zamonaviy baland poshnali tuflya, maxsus tadbirlar uchun",
                    "/static/images/high-heels.jpg",
                    1,
                    25,
                    12,
                    4.4,
                    15.0,
                    "35,36,37,38,39,40",
                    "qora,qizil,jigarrang",
                    now,
                ),
                (
                    "Klassik Tuflya",
                    520000,
                    "tuflya",
                    "Klassik uslubdagi ayollar tufliyasi",
                    "/static/images/classic-heels.jpg",
                    1,
                    20,
                    6,
                    4.2,
                    0.0,
                    "35,36,37,38,39",
                    "qora,jigarrang",
                    now,
                ),
            ]
            
            cur.executemany(
                "INSERT INTO menu_items (name, price, category, description, image_url, available, stock_quantity, orders_count, rating, discount_percentage, sizes, colors, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                additional_items,
            )
            
            conn.commit()
            print(f"Added {len(additional_items)} additional sample items")
        
    except Exception as e:
        print(f"Failed to add sample data: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("=== Pro-Obuv Category Migration ===")
    
    # Run migration
    if migrate_categories():
        print("✅ Category migration successful")
        
        # Add additional sample data
        if add_sample_data():
            print("✅ Sample data added successfully")
        else:
            print("⚠️  Sample data addition failed")
    else:
        print("❌ Category migration failed")
        sys.exit(1)
    
    print("\n🎉 Migration completed successfully!")