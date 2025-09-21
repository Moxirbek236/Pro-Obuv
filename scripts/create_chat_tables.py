#!/usr/bin/env python3
"""
Safe helper to create compatibility chat/notification tables in database.sqlite3.
Run from project root with: python scripts\create_chat_tables.py
"""
import sqlite3
import sys

DB = 'database.sqlite3'

DDL = [
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        body TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER,
        title TEXT,
        body TEXT,
        data TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        read INTEGER DEFAULT 0
    )
    """,
]

if __name__ == '__main__':
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        for sql in DDL:
            cur.executescript(sql)
        conn.commit()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print('OK - ensured tables. Current tables:', tables)
    except Exception as e:
        print('ERROR creating tables:', e, file=sys.stderr)
        sys.exit(2)
    finally:
        try:
            conn.close()
        except Exception:
            pass
