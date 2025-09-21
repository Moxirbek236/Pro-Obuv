import os, sqlite3
p = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
p = os.path.abspath(p)
print('DB path:', p)
print('exists', os.path.exists(p))
if os.path.exists(p):
    print('size', os.path.getsize(p))
    try:
        conn = sqlite3.connect(p)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        print('tables:', cur.fetchall())
        conn.close()
    except Exception as e:
        print('sqlite error:', e)
