#!/usr/bin/env python3
"""Populate i18n name/description columns from legacy name/description.

This script:
 - creates a timestamped backup of database.sqlite3 in ./backups
 - ensures i18n columns exist (adds them if missing)
 - copies existing `name` -> name_ru/name_uz/name_en/name_kz where empty
 - copies existing `description` -> description_ru/_uz/_en/_kz where empty
 - prints a small summary and sample row(s)

Note: this is a best-effort script that does not attempt automatic translation.
It simply copies the existing legacy fields into all language-specific columns so
localized_field() will return a value.
"""
import os
import shutil
import sqlite3
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__)) if os.path.basename(os.path.dirname(__file__)) == 'scripts' else os.getcwd()
DB_PATH = os.path.join(ROOT, 'database.sqlite3')
BACKUP_DIR = os.path.join(ROOT, 'backups')

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
BACKUP_NAME = f'database_backup_populate_i18n_{TIMESTAMP}.sqlite3'
BACKUP_PATH = os.path.join(BACKUP_DIR, BACKUP_NAME)

os.makedirs(BACKUP_DIR, exist_ok=True)

if not os.path.exists(DB_PATH):
    print('Database file not found at', DB_PATH)
    raise SystemExit(1)

print('Creating DB backup at', BACKUP_PATH)
shutil.copy2(DB_PATH, BACKUP_PATH)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check existing columns
cur.execute("PRAGMA table_info(menu_items)")
cols = [r['name'] for r in cur.fetchall()]

expected_name_cols = ['name_ru','name_uz','name_en','name_kz']
expected_desc_cols = ['description_ru','description_uz','description_en','description_kz']

added = []
for c in expected_name_cols + expected_desc_cols:
    if c not in cols:
        try:
            print('Adding column', c)
            cur.execute(f"ALTER TABLE menu_items ADD COLUMN {c} TEXT DEFAULT ''")
            added.append(c)
        except Exception as e:
            print('Failed to add column', c, '->', e)

conn.commit()

# Update rows: set localized columns to legacy values when empty
# Use single UPDATE for performance
update_sql = '''
UPDATE menu_items
SET
  name_ru = COALESCE(NULLIF(name_ru, ''), name),
  name_uz = COALESCE(NULLIF(name_uz, ''), name),
  name_en = COALESCE(NULLIF(name_en, ''), name),
  name_kz = COALESCE(NULLIF(name_kz, ''), name),
  description_ru = COALESCE(NULLIF(description_ru, ''), description),
  description_uz = COALESCE(NULLIF(description_uz, ''), description),
  description_en = COALESCE(NULLIF(description_en, ''), description),
  description_kz = COALESCE(NULLIF(description_kz, ''), description)
'''

print('Populating localized columns from legacy name/description...')
cur.execute(update_sql)
conn.commit()

# Summary counts
cur.execute('SELECT COUNT(1) as c FROM menu_items')
count = cur.fetchone()['c']
print('Total menu_items:', count)

# Show sample rows (first 5) with localized fields
cur.execute('SELECT id, name, name_uz, name_ru, name_en, name_kz, description, description_uz, description_ru, description_en, description_kz FROM menu_items ORDER BY id LIMIT 5')
rows = cur.fetchall()
for r in rows:
    print('\n----')
    for k in r.keys():
        print(f"{k}: {r[k]}")

# Also show item id 39 if present
cur.execute('SELECT id, name, name_uz, name_ru, name_en, name_kz, description, description_uz, description_ru, description_en, description_kz FROM menu_items WHERE id = 39')
r39 = cur.fetchone()
if r39:
    print('\nSample id=39:')
    for k in r39.keys():
        print(f"{k}: {r39[k]}")
else:
    print('\nNo item with id=39 found.')

conn.close()
print('\nDone. If your app caches menu data in-memory, restart the server to pick up DB changes or trigger cache invalidation via admin flows.')
