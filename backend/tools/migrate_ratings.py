import sqlite3
import os
DB = r"c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\database.sqlite3"
if not os.path.exists(DB):
    print("DB file not found:", DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('Checking ratings schema...')
cur.execute("PRAGMA table_info(ratings);")
cols_info = cur.fetchall() or []
cols = [r[1] for r in cols_info]
print('Existing columns:', cols)
need_rebuild = False
if 'branch_id' not in cols:
    need_rebuild = True
else:
    for r in cols_info:
        if r[1] == 'menu_item_id' and r[3] == 1:
            need_rebuild = True
            break

if not need_rebuild:
    print('No migration needed for ratings table.')
    conn.close()
    raise SystemExit(0)

print('Performing ratings migration...')
try:
    cur.execute("SELECT id, user_id, menu_item_id, rating, comment, created_at FROM ratings")
    existing = cur.fetchall() or []

    cur.execute('BEGIN TRANSACTION;')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS ratings_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_item_id INTEGER,
            branch_id INTEGER,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            UNIQUE(user_id, menu_item_id, branch_id)
        );
    ''')

    for row in existing:
        rid = row['id']
        uid = row['user_id']
        mid = row['menu_item_id']
        rating_val = row['rating']
        comment = row['comment']
        created_at = row['created_at']
        cur.execute(
            "INSERT INTO ratings_new (id, user_id, menu_item_id, branch_id, rating, comment, created_at) VALUES (?, ?, ?, NULL, ?, ?, ?)",
            (rid, uid, mid, rating_val, comment, created_at)
        )

    cur.execute('DROP TABLE IF EXISTS ratings;')
    cur.execute('ALTER TABLE ratings_new RENAME TO ratings;')
    conn.commit()
    print('Ratings table migrated successfully.')
except Exception as e:
    conn.rollback()
    print('Ratings migration failed:', e)
finally:
    conn.close()
