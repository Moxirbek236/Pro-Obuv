"""Seed script to replace all menu_items with a footwear catalog (shoes).
Usage: python tools/seed_shoes.py

This script:
- backs up database.sqlite3 to backups/
- deletes all rows from menu_items
- inserts a small list of shoe products using safe columns present in the schema
"""
import os
import sqlite3
import datetime
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT, 'database.sqlite3')
BACKUP_DIR = os.path.join(ROOT, 'backups')

SAMPLE_SHOES = [
    ("Classic Sneaker", 120000.0, "footwear", "Comfortable everyday sneaker", "/static/images/shoe1.jpg", 1, 50, 0, 4.5, 0.0, "",
     "", datetime.datetime.now().isoformat()),
    ("Running Pro", 180000.0, "footwear", "Lightweight running shoe", "/static/images/shoe2.jpg", 1, 30, 0, 4.7, 0.0, "",
     "", datetime.datetime.now().isoformat()),
    ("Leather Boot", 220000.0, "footwear", "Durable leather boot", "/static/images/shoe3.jpg", 1, 20, 0, 4.6, 10.0, "",
     "", datetime.datetime.now().isoformat()),
    ("Slip-on Sandal", 70000.0, "footwear", "Easy slip-on sandal", "/static/images/shoe4.jpg", 1, 100, 0, 4.2, 0.0, "",
     "", datetime.datetime.now().isoformat()),
]

def backup_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'database_backup_{timestamp}.sqlite3')
    shutil.copy2(DB_PATH, dest)
    print('Backup created at', dest)
    return dest


def run():
    if not os.path.exists(DB_PATH):
        print('Database not found at', DB_PATH)
        return

    backup_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Delete existing items
    cur.execute('DELETE FROM menu_items;')

    # Try an insert that matches the schema if available. We use a long INSERT that
    # matches common columns. If schema differs, try a fallback minimal insert.
    try:
        cur.executemany(
            "INSERT INTO menu_items (name, price, category, description, image_url, available, stock_quantity, orders_count, rating, discount_percentage, sizes, colors, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            SAMPLE_SHOES,
        )
    except Exception as e:
        print('Insert with extended columns failed:', e)
        print('Trying minimal insert (name, price, category, created_at)')
        now = datetime.datetime.now().isoformat()
        cur.execute('DELETE FROM menu_items;')
        for name, price, category, description, image_url, available, stock_quantity, orders_count, rating, discount_percentage, sizes, colors, created_at in SAMPLE_SHOES:
            try:
                cur.execute(
                    'INSERT INTO menu_items (name, price, category, created_at) VALUES (?, ?, ?, ?)',
                    (name, price, category, now),
                )
            except Exception as ex:
                print('Row insert failed:', ex)

    conn.commit()
    conn.close()
    print('Seeding completed. Inserted', len(SAMPLE_SHOES), 'items (best-effort).')


if __name__ == '__main__':
    run()
