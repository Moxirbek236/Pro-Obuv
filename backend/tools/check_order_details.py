import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
DB_PATH = os.path.abspath(DB_PATH)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT id, ticket_no, status FROM orders ORDER BY created_at DESC LIMIT 20")
orders = cur.fetchall()

results = []
for o in orders:
    oid = o[0]
    ticket = o[1]
    status = o[2]
    try:
        cur.execute('SELECT COUNT(*) FROM order_details WHERE order_id = ?', (oid,))
        cnt = cur.fetchone()[0]
    except Exception as e:
        cnt = f'error: {e}'
    results.append({'id': oid, 'ticket_no': ticket, 'status': status, 'order_details_count': cnt})

print(json.dumps({'db_path': DB_PATH, 'recent_orders_details': results}, ensure_ascii=False))
conn.close()
