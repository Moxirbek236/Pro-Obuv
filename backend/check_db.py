import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
dsn = os.environ.get("DATABASE_URL")

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'menu_items'
    """)
    columns = cur.fetchall()
    print("Columns in menu_items:")
    for col in columns:
        print(f"- {col[0]} ({col[1]})")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
