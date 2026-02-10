import os
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = "postgres://avnadmin:AVNS_6-0X49G507dF1L29940@pg-363690d7-moxirbek236-8c43.l.aivencloud.com:12555/defaultdb?sslmode=require"

def check_bot_users():
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        database=url.path.lstrip('/'),
        sslmode='require'
    )
    cur = conn.cursor()
    
    print("\n--- bot_users structure ---")
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'bot_users'")
    for row in cur.fetchall():
        print(f"Column: {row[0]}, Type: {row[1]}")
        
    print("\n--- bot_users constraints ---")
    cur.execute("SELECT conname, contype FROM pg_constraint WHERE conrelid = 'bot_users'::regclass")
    for row in cur.fetchall():
        print(f"Constraint: {row[0]}, Type: {row[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_bot_users()
