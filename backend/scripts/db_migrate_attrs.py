import sqlite3
import os

DB_PATH = 'd:/Safety.uz/database.db'

def setup_columns():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # List of columns to add
    new_columns = [
        ('material', 'TEXT'),
        ('purpose', 'TEXT'),
        ('season', 'TEXT'),
        ('shoe_type', 'TEXT'),
        ('sole_type', 'TEXT'),
        ('height', 'TEXT'),
        ('clothing_type', 'TEXT'),
        ('thickness', 'TEXT'),
        ('weight', 'TEXT'),
        ('standard', 'TEXT'),
        ('features', 'TEXT')
    ]
    
    # Check existing columns
    cur.execute("PRAGMA table_info(menu_items)")
    existing = [col[1] for col in cur.fetchall()]
    
    for col_name, col_type in new_columns:
        if col_name not in existing:
            print(f"Adding column {col_name}...")
            try:
                cur.execute(f"ALTER TABLE menu_items ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    setup_columns()
