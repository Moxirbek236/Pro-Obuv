#!/usr/bin/env python3
"""Add multilingual columns to news table and populate from legacy title/content."""
import os
import shutil
import sqlite3
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, 'database.sqlite3')
BACKUP_DIR = os.path.join(ROOT, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = os.path.join(BACKUP_DIR, f'database_backup_news_i18n_{ts}.sqlite3')
print('Backing up DB to', backup)
shutil.copy2(DB_PATH, backup)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cols_needed = [
    'title_ru','title_uz','title_en','title_kz',
    'content_ru','content_uz','content_en','content_kz'
]

cur.execute("PRAGMA table_info(news)")
existing = [r[1] for r in cur.fetchall()]

for c in cols_needed:
    if c not in existing:
        try:
            print('Adding', c)
            cur.execute(f"ALTER TABLE news ADD COLUMN {c} TEXT DEFAULT ''")
        except Exception as e:
            print('Failed to add', c, e)

conn.commit()

# Populate new columns from legacy fields if empty
update_sql = '''
UPDATE news SET
 title_ru = COALESCE(NULLIF(title_ru, ''), title),
 title_uz = COALESCE(NULLIF(title_uz, ''), title),
 title_en = COALESCE(NULLIF(title_en, ''), title),
 title_kz = COALESCE(NULLIF(title_kz, ''), title),
 content_ru = COALESCE(NULLIF(content_ru, ''), content),
 content_uz = COALESCE(NULLIF(content_uz, ''), content),
 content_en = COALESCE(NULLIF(content_en, ''), content),
 content_kz = COALESCE(NULLIF(content_kz, ''), content)
'''
print('Populating news i18n columns from existing title/content...')
cur.execute(update_sql)
conn.commit()

cur.execute('SELECT id, title, title_uz, title_ru FROM news LIMIT 5')
for r in cur.fetchall():
    print(r)

conn.close()
print('Done.')
