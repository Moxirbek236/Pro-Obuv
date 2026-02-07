import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
dsn = os.environ.get("DATABASE_URL")

try:
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'site_settings'")
    cols = cur.fetchall()
    print("Columns in site_settings:")
    for col in cols:
        print(f"- {col[0]}: {col[1]}")
        
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'settings'")
    cols = cur.fetchall()
    if not cols:
        print("Table 'settings' NOT FOUND.")
    else:
        print("Columns in settings:")
        for col in cols:
            print(f"- {col[0]}: {col[1]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
