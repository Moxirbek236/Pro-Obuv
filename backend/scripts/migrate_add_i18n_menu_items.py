#!/usr/bin/env python3
"""
Safe migration: add name_uz/name_ru/name_en/name_kz and description_uz/... columns
and populate them from existing name/description to preserve data.
Run this once; it's idempotent (checks PRAGMA table_info before ALTER).
"""
import sqlite3
import shutil
import os
from datetime import datetime

DB = 'database.sqlite3'
BACKUP_DIR = 'backups'

cols_to_add = [
    'name_ru', 'name_uz', 'name_en', 'name_kz',
    'description_ru', 'description_uz', 'description_en', 'description_kz'
]

def backup_db(db_path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'database_backup_{ts}.sqlite3')
    shutil.copy2(db_path, dest)
    return dest


def main():
    if not os.path.exists(DB):
        print('Database file not found:', DB)
        return

    print('Backing up database...')
    bk = backup_db(DB)
    print('Backup created at', bk)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys=ON;")

    # Get existing columns
    cur.execute("PRAGMA table_info(menu_items);")
    existing = [r[1] for r in cur.fetchall()]
    print('Existing columns:', existing)

    added = []
    for c in cols_to_add:
        if c not in existing:
            try:
                print('Adding column', c)
                cur.execute(f"ALTER TABLE menu_items ADD COLUMN {c} TEXT;")
                added.append(c)
            except Exception as e:
                print('Failed to add', c, e)
    conn.commit()

    # Refresh existing columns list
    cur.execute("PRAGMA table_info(menu_items);")
    existing = [r[1] for r in cur.fetchall()]

    # Populate newly added columns from legacy fields where empty
    updates = []
    now = datetime.now().isoformat()
    try:
        set_clauses = []
        params = []
        # For each language field, copy from legacy name/description if NULL or empty
        for lang in ['uz','ru','en','kz']:
            n = f'name_{lang}'
            d = f'description_{lang}'
            if n in existing:
                set_clauses.append(f"{n} = COALESCE(NULLIF({n},''), name)")
            if d in existing:
                set_clauses.append(f"{d} = COALESCE(NULLIF({d},''), description)")
        if set_clauses:
            sql = "UPDATE menu_items SET " + ", ".join(set_clauses) + ";"
            print('Populating language columns from legacy fields...')
            cur.execute(sql)
            conn.commit()
            updates.append(sql)
    except Exception as e:
        print('Failed to populate language columns:', e)

    print('\nMigration summary:')
    print('Columns added:', added)
    print('Updates applied:', len(updates) > 0)

    # Show sample row for id 39
    try:
        cur.execute('SELECT * FROM menu_items WHERE id = 39')
        row = cur.fetchone()
        if row:
            print('\nRow 39 after migration:')
            cols = [d[0] for d in cur.description]
            for k,v in zip(cols,row):
                print(f'{k}:', v)
        else:
            print('No row with id=39')
    except Exception as e:
        print('Failed to show sample row:', e)

    conn.close()

if __name__ == '__main__':
    main()
