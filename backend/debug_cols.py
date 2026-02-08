
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def test_db():
    try:
        print(f"Connecting to: {DATABASE_URL.split('@')[-1]}") # Print host only for safety
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Check Tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [t['table_name'] for t in cur.fetchall()]
        print(f"\nTables found ({len(tables)}):")
        print(", ".join(tables))
        
        # 2. Check menu_items content
        if 'menu_items' in tables:
            cur.execute("SELECT COUNT(*) FROM menu_items")
            count = cur.fetchone()['count']
            print(f"\nRow count in 'menu_items': {count}")
            
            if count > 0:
                cur.execute("SELECT id, name, available FROM menu_items LIMIT 5")
                rows = cur.fetchall()
                print("\nSample items:")
                for r in rows:
                    print(f"- ID: {r['id']}, Name: {r['name']}, Available: {r['available']}")
            else:
                print("\nWARNING: 'menu_items' table is EMPTY. That is why no data is showing.")
        else:
            print("\nERROR: 'menu_items' table NOT FOUND in database.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_db()
