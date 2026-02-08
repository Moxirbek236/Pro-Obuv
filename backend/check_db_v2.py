import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
dsn = os.environ.get("DATABASE_URL")

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM menu_items")
    count = cur.fetchone()[0]
    print(f"Total items in menu_items: {count}")
    
    cur.execute("SELECT id, name, is_new FROM menu_items LIMIT 5")
    rows = cur.fetchall()
    print("Sample items:")
    for r in rows:
        print(r)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
