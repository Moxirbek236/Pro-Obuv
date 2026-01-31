import sqlite3
import os

db_name = 'database.sqlite3'
if not os.path.exists(db_name):
    print(f"Database {db_name} does not exist.")
    exit(1)

conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Get columns of menu_items
cursor.execute("PRAGMA table_info(menu_items)")
columns = [r[1] for r in cursor.fetchall()]

# Add missing localized name columns if they don't exist
# (User wants one name, but we keep these for compatibility)
for lang in ['uz', 'ru', 'en', 'kz']:
    col = f"name_{lang}"
    if col not in columns:
        print(f"Adding {col} to menu_items...")
        try:
            cursor.execute(f"ALTER TABLE menu_items ADD COLUMN {col} TEXT")
        except Exception as e:
            print(f"Error adding {col}: {e}")

# Add missing localized description columns
for lang in ['uz', 'ru', 'en', 'kz']:
    col = f"description_{lang}"
    if col not in columns:
        print(f"Adding {col} to menu_items...")
        try:
            cursor.execute(f"ALTER TABLE menu_items ADD COLUMN {col} TEXT")
        except Exception as e:
            print(f"Error adding {col}: {e}")

conn.commit()
conn.close()
print("Migration complete.")
