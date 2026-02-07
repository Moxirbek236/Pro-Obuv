import sqlite3, json, os

db = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
db = os.path.abspath(db)
if not os.path.exists(db):
    print('DB not found:', db)
    raise SystemExit(1)

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, menu_item_id, media_type, media_url, display_order, is_main FROM product_media ORDER BY menu_item_id, display_order")
rows = cur.fetchall()
out = [dict(r) for r in rows]
print(json.dumps({'count': len(rows), 'sample_count': min(50, len(rows)), 'sample': out[:50]}, ensure_ascii=False, indent=2))
conn.close()
