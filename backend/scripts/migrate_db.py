#!/usr/bin/env python3
"""
Manual migration script to add missing columns to menu_items table
"""
import sqlite3
import os

def run_migration():
    # Database path - check multiple possible locations
    possible_paths = [
        'd:\\Safety.uz\\database.sqlite3',
        'database.sqlite3',
        'd:\\Safety.uz\\database.db',
        'database.db',
        'instance\\restaurant.db',
        'restaurant.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Database file not found in any of the expected locations!")
        print("Checked paths:", possible_paths)
        return
    
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Check if is_new column exists
        cur.execute("PRAGMA table_info(menu_items);")
        columns = [row[1] for row in cur.fetchall()]
        
        print(f"Current columns: {columns}")
        
        # Add is_new column if it doesn't exist
        if 'is_new' not in columns:
            print("Adding is_new column...")
            cur.execute("ALTER TABLE menu_items ADD COLUMN is_new BOOLEAN DEFAULT 0;")
            print("✓ is_new column added successfully")
        else:
            print("✓ is_new column already exists")
        
        # Add created_at column if it doesn't exist
        if 'created_at' not in columns:
            print("Adding created_at column...")
            cur.execute("ALTER TABLE menu_items ADD COLUMN created_at TEXT;")
            print("✓ created_at column added successfully")
        else:
            print("✓ created_at column already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Show updated table structure
        cur.execute("PRAGMA table_info(menu_items);")
        updated_columns = [row[1] for row in cur.fetchall()]
        print(f"Updated columns: {updated_columns}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()
