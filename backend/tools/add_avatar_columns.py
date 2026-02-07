"""Safe SQLite migration: add `avatar` TEXT column to users, staff, couriers if missing.
Creates a timestamped backup of database.sqlite3 before applying ALTER TABLE.
Run: python tools\add_avatar_columns.py
"""
import os
import sqlite3
import shutil
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
DB_PATH = os.path.abspath(DB_PATH)

BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

TABLES = ['users', 'staff', 'couriers']


def table_has_column(conn, table, column):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(%s)" % table)
    cols = [r[1] for r in cur.fetchall()]
    return column in cols


def add_avatar_column(conn, table):
    cur = conn.cursor()
    cur.execute(f"ALTER TABLE {table} ADD COLUMN avatar TEXT")
    conn.commit()


def main():
    if not os.path.exists(DB_PATH):
        print('Database file not found at', DB_PATH)
        return

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'database_backup_{ts}.sqlite3')
    print('Creating backup:', backup_path)
    shutil.copy2(DB_PATH, backup_path)

    conn = sqlite3.connect(DB_PATH)
    try:
        for t in TABLES:
            print('Processing table', t)
            try:
                if table_has_column(conn, t, 'avatar'):
                    print(' - already has avatar column')
                    continue
                print(' - adding avatar column')
                add_avatar_column(conn, t)
            except sqlite3.OperationalError as e:
                print(' - table missing or other error:', e)
        print('Migration complete')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
