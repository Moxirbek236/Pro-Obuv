#!/usr/bin/env python3
import json
import sqlite3
import os
import sys
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
DB_PATH = os.path.abspath(DB_PATH)
JSON_FILE = os.path.join(os.path.dirname(__file__), '..', 'superadmin_settings.json')
JSON_FILE = os.path.abspath(JSON_FILE)


def main():
    if not os.path.exists(JSON_FILE):
        print(f"ERROR: {JSON_FILE} not found.")
        return 2

    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: failed to read JSON file: {e}")
        return 3

    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute('''
        CREATE TABLE IF NOT EXISTS superadmin_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            data TEXT,
            created_at TEXT
        )
        ''')

        username = data.get('username')
        password = data.get('password')
        cur.execute(
            'INSERT INTO superadmin_settings (username, password, data, created_at) VALUES (?,?,?,?)',
            (username, password, json.dumps(data, ensure_ascii=False), datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
        inserted_id = cur.lastrowid

        print(f"Inserted superadmin settings id={inserted_id}")

        # Show last 5 rows for verification
        print("Recent rows:")
        for row in cur.execute('SELECT id, username, created_at FROM superadmin_settings ORDER BY id DESC LIMIT 5'):
            print(row)

        conn.close()

    except Exception as e:
        print(f"ERROR: failed to write to DB: {e}")
        return 4

    # Only delete the JSON file after successful insert
    try:
        os.remove(JSON_FILE)
        print(f"Deleted {JSON_FILE}")
    except Exception as e:
        print(f"WARNING: inserted but failed to delete JSON file: {e}")
        return 5

    return 0


if __name__ == '__main__':
    sys.exit(main())
