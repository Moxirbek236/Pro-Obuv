import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
dsn = os.getenv("DATABASE_URL")
conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)
cur = conn.cursor()
cur.execute("SELECT key, value FROM site_settings WHERE key = 'use_uzum_market'")
row = cur.fetchone()
print(f"Setting: {row}")
conn.close()
