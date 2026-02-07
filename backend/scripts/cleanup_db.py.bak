import sqlite3
import os

def cleanup_database():
    """Clean up old non-footwear items from database"""
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.sqlite3")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Delete old non-footwear items
        cur.execute('DELETE FROM menu_items WHERE category IN ("food", "drink", "footwear")')
        deleted_count = cur.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleaned up {deleted_count} old non-footwear items")
        return True
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    cleanup_database()