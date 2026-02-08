import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
DB_PATH = os.path.abspath(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Status counts
try:
    cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
    status_counts = cur.fetchall()
except Exception as e:
    status_counts = [("error", str(e))]

# Recent orders
try:
    cur.execute("SELECT id, status, ticket_no, customer_name, created_at FROM orders ORDER BY created_at DESC LIMIT 20")
    recent = cur.fetchall()
except Exception as e:
    recent = [("error", str(e))]

print(json.dumps({"db_path": DB_PATH, "status_counts": status_counts, "recent": recent}, default=str, ensure_ascii=False))
conn.close()
