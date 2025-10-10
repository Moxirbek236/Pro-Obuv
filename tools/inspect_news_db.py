import sqlite3, traceback, os
from pathlib import Path
workspace_root = Path(__file__).resolve().parent.parent
db = workspace_root / 'database.sqlite3'
print('Workspace:', workspace_root)
print('DB path:', db)
print('DB exists:', db.exists())
if not db.exists():
    print('database.sqlite3 not found')
    raise SystemExit(1)
try:
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print('Tables (count=%d):' % len(tables))
    for t in tables:
        print(' -', t)
    print('\nPRAGMA table_info(news):')
    cur.execute("PRAGMA table_info(news)")
    cols = cur.fetchall()
    if not cols:
        print('news table does not exist or has no columns')
    for c in cols:
        print(dict(c))
    print('\nSample rows from news:')
    try:
        cur.execute('SELECT id, title, is_active, show_in_ticker, display_order, created_at FROM news ORDER BY display_order ASC, created_at DESC LIMIT 100')
        rows = cur.fetchall()
        print('rows count:', len(rows))
        for r in rows:
            print(dict(r))
    except Exception as e:
        print('Error selecting rows from news:')
        traceback.print_exc()
except Exception:
    traceback.print_exc()
finally:
    try:
        con.close()
    except Exception:
        pass
