import sqlite3
import os

DB_PATH = 'd:/Safety.uz/database.db'

def list_tables():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"- {table[0]}")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
