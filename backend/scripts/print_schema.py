import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
DB = os.path.abspath(DB)
if not os.path.exists(DB):
    print('DB not found at', DB)
    raise SystemExit(1)
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for (t,) in cur.fetchall():
    print('\nTABLE:', t)
    try:
        cur.execute(f"PRAGMA table_info('{t}')")
        for row in cur.fetchall():
            # (cid, name, type, notnull, dflt_value, pk)
            print('   ', row)
    except Exception as e:
        print('   Error:', e)
conn.close()