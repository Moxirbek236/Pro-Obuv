import sqlite3, os
p = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
print('DB path:', p)
print('exists', os.path.exists(p), 'size', os.path.getsize(p) if os.path.exists(p) else 'N/A')
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute('PRAGMA foreign_keys=ON;')
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print('tables:', tables)
for t in ['users','menu_items','staff','couriers','news','branches']:
    cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (t,))
    print(t, cur.fetchone()[0])
cur.close()
conn.close()
