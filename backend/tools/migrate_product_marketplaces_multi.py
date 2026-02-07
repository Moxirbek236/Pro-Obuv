#!/usr/bin/env python3
"""
Idempotent migration: allow multiple marketplace URLs per product by removing UNIQUE(menu_item_id, market_key)
If table already has no unique constraint, script will be a no-op.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
DB = os.path.abspath(DB)

print('DB path:', DB)
conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    # Check existing schema
    cur.execute("PRAGMA table_info(product_marketplaces);")
    cols = cur.fetchall()
    if not cols:
        print('product_marketplaces table not found, creating new table')
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS product_marketplaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_item_id INTEGER NOT NULL,
                market_key TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
            );
        ''')
        conn.commit()
        print('Created table product_marketplaces')
    else:
        # Inspect create statement to see if UNIQUE exists
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='product_marketplaces'")
        row = cur.fetchone()
        create_sql = row[0] if row else ''
        if 'UNIQUE' in (create_sql or '').upper():
            print('Found UNIQUE constraint, performing safe rebuild to remove it')
            cur.executescript('''
                BEGIN TRANSACTION;
                CREATE TABLE IF NOT EXISTS product_marketplaces_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    menu_item_id INTEGER NOT NULL,
                    market_key TEXT NOT NULL,
                    url TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
                );
                INSERT INTO product_marketplaces_new (menu_item_id, market_key, url, created_at)
                SELECT menu_item_id, market_key, url, created_at FROM product_marketplaces;
                DROP TABLE product_marketplaces;
                ALTER TABLE product_marketplaces_new RENAME TO product_marketplaces;
                COMMIT;
            ''')
            print('Migration completed: UNIQUE constraint removed')
        else:
            print('No UNIQUE constraint found; nothing to do')
    conn.commit()
except Exception as e:
    print('Migration error:', e)
    try:
        conn.rollback()
    except:
        pass
finally:
    conn.close()

print('Done')
