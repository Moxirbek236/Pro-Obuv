import sqlite3
import os

databases = ['restaurant.db', 'database.sqlite3']
tables = ['orders', 'questions', 'staff', 'couriers', 'users', 'branches', 'receipts']

for db_name in databases:
    if not os.path.exists(db_name):
        print(f"Database {db_name} does not exist, skipping.")
        continue
    
    print(f"\nChecking database: {db_name}")
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [r[0] for r in cursor.fetchall()]
        
        for table in tables:
            if table not in existing_tables:
                print(f"  Table {table} does not exist in {db_name}, skipping.")
                continue
            
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [r[1] for r in cursor.fetchall()]
            
            if 'created_at' not in columns:
                print(f"  Adding 'created_at' column to table {table} in {db_name}...")
                try:
                    # Default value for TEXT created_at could be current timestamp
                    # but for migration let's just use a fixed date or empty string if allowed
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN created_at TEXT NOT NULL DEFAULT '2026-01-01 00:00:00'")
                    print(f"    Success!")
                except Exception as e:
                    print(f"    Error adding column to {table}: {e}")
            else:
                print(f"  Table {table} already has 'created_at' column.")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error connecting to {db_name}: {e}")

print("\nMigration complete.")
