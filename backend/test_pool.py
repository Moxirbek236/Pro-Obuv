from psycopg2 import pool
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()
dsn = os.getenv("DATABASE_URL")
print(f"Testing Pool with DSN: {dsn[:20]}...")

try:
    p = pool.ThreadedConnectionPool(1, 10, dsn, cursor_factory=RealDictCursor)
    print("Pool initialized!")
    conn = p.getconn()
    print("Connection from pool successful!")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("Query successful!")
    p.putconn(conn)
    p.closeall()
except Exception as e:
    print(f"Error type: {type(e)}")
    print(f"Error string: {str(e)}")
    print(f"Error args: {e.args}")
