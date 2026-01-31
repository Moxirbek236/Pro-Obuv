import sqlite3

def migrate():
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute("PRAGMA table_info(menu_items)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = [
        ('weight', 'TEXT'),
        ('material', 'TEXT'),
        ('purpose', 'TEXT'),
        ('season', 'TEXT'),
        ('shoe_type', 'TEXT'),
        ('sole_type', 'TEXT'),
        ('height', 'TEXT'),
        ('clothing_type', 'TEXT'),
        ('thickness', 'TEXT'),
        ('standard', 'TEXT'),
        ('features', 'TEXT'),
        ('brand', 'TEXT')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE menu_items ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
