#!/usr/bin/env python3
"""
Enable `show_in_ticker` for all active news rows in the SQLite DB.
Run from repository root: `python scripts/enable_ticker.py`
"""
import sqlite3
import os

DB = os.path.join(os.getcwd(), 'database.sqlite3')
if not os.path.exists(DB):
    print('Database not found at', DB)
    raise SystemExit(1)

con = sqlite3.connect(DB)
cur = con.cursor()

# Ensure column exists
cur.execute("PRAGMA table_info(news)")
cols = [r[1] for r in cur.fetchall()]
if 'show_in_ticker' not in cols:
    try:
        cur.execute("ALTER TABLE news ADD COLUMN show_in_ticker BOOLEAN DEFAULT 0")
        print('Added show_in_ticker column')
    except Exception as e:
        print('Could not add show_in_ticker column:', e)

# Set ticker flag for active news
try:
    cur.execute("UPDATE news SET show_in_ticker = 1 WHERE is_active = 1")
    con.commit()
    cur.execute("SELECT COUNT(*) FROM news WHERE show_in_ticker = 1")
    cnt = cur.fetchone()[0]
    print('Updated show_in_ticker for', cnt, 'rows')
except Exception as e:
    print('Failed to update rows:', e)
finally:
    con.close()
