#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')

def ensure_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute('''
        CREATE TABLE IF NOT EXISTS product_marketplaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item_id INTEGER NOT NULL,
            market_key TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(menu_item_id, market_key),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
        );
        ''')
        conn.commit()
        print('OK: product_marketplaces table ensured')
        cur.execute("PRAGMA table_info(product_marketplaces);")
        rows = cur.fetchall()
        print('Schema:')
        for r in rows:
            print(r)
    except Exception as e:
        print('ERROR:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    ensure_table()
