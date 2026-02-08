import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
dsn = os.getenv("DATABASE_URL")
print(f"Testing DSN: {dsn[:20]}...")

try:
    conn = psycopg2.connect(dsn)
    print("Connection successful!")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("Query successful!")
    conn.close()
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error string: {str(e)}")
    print(f"Error args: {e.args}")
    if hasattr(e, 'pgcode'):
        print(f"PG Code: {e.pgcode}")
