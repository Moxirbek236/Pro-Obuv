import sqlite3
import os

DB_PATH = 'd:/Safety.uz/database.db'

def check_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Check menu_items columns
        cur.execute("PRAGMA table_info(menu_items)")
        columns = cur.fetchall()
        print("Columns in menu_items:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
            
        # Check row count
        cur.execute("SELECT COUNT(*) FROM menu_items")
        count = cur.fetchone()[0]
        print(f"\nTotal rows in menu_items: {count}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
