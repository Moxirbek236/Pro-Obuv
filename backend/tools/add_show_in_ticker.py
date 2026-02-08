import sqlite3
from pathlib import Path
from datetime import datetime
import traceback

workspace_root = Path(__file__).resolve().parent.parent
db = workspace_root / 'database.sqlite3'
print('DB:', db)
if not db.exists():
    print('database.sqlite3 not found')
    raise SystemExit(1)
con = sqlite3.connect(str(db))
cur = con.cursor()
try:
    cur.execute("PRAGMA table_info(news)")
    cols = [r[1] for r in cur.fetchall()]
    print('news cols before:', cols)
    if 'show_in_ticker' not in cols:
        print('Adding show_in_ticker column to news')
        cur.execute("ALTER TABLE news ADD COLUMN show_in_ticker INTEGER DEFAULT 0")
        con.commit()
    else:
        print('show_in_ticker already exists')
    cur.execute("PRAGMA table_info(news)")
    cols = [r[1] for r in cur.fetchall()]
    print('news cols after:', cols)
    cur.execute('SELECT id, title, is_active, show_in_ticker, display_order, created_at FROM news ORDER BY display_order ASC, created_at DESC LIMIT 20')
    rows = cur.fetchall()
    print('rows count:', len(rows))
    for r in rows:
        print(r)
except Exception:
    traceback.print_exc()
finally:
    con.close()
