import sqlite3
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.cloudinary_service import cloudinary_service

load_dotenv()

DB_PATH = 'database.sqlite3'
CLOUD_BASE_URL = f"https://res.cloudinary.com/{os.getenv('CLOUD_NAME', 'dpfbu9aid')}/image/upload/f_auto,q_auto"

def get_cloud_version():
     # A dummy version or current timestamp-like to ensure uniqueness if needed, but not strictly required
     return "v1"

def construct_cloudinary_url(local_path):
    """Constructs a Cloudinary URL from a local path without checking for file existence."""
    clean_path = local_path.lstrip('/')
    if clean_path.startswith('static/'):
        clean_path = clean_path.replace('static/', '', 1)
        
    public_id = ""
    if clean_path.startswith('uploads/products/'):
        public_id = f"products/{os.path.splitext(os.path.basename(clean_path))[0]}"
    elif clean_path.startswith('uploads/avatars/'):
        public_id = f"avatars/{os.path.splitext(os.path.basename(clean_path))[0]}"
    elif clean_path.startswith('news/'):
        public_id = f"news/{os.path.splitext(os.path.basename(clean_path))[0]}"
    elif clean_path.startswith('favicons/'):
        public_id = f"favicons/{os.path.splitext(os.path.basename(clean_path))[0]}"
    elif clean_path.startswith('icons/'):
        public_id = f"icons/{os.path.splitext(os.path.basename(clean_path))[0]}"
    else:
        public_id = f"static-root/{os.path.splitext(clean_path)[0]}"
        
    return f"{CLOUD_BASE_URL}/{public_id}"

def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables_cols = [
        ('menu_items', 'image_url'),
        ('product_media', 'media_url'),
        ('users', 'avatar'),
        ('staff', 'avatar'),
        ('news', 'image_url'),
        ('couriers', 'avatar')
    ]
    
    for table, col in tables_cols:
        try:
            print(f"Migrating {table}.{col}...")
            cursor.execute(f"SELECT id, {col} FROM {table} WHERE {col} LIKE '/static/%' OR {col} LIKE 'static/%'")
            rows = cursor.fetchall()
            for row_id, local_path in rows:
                if local_path:
                    new_url = construct_cloudinary_url(local_path)
                    cursor.execute(f"UPDATE {table} SET {col} = ? WHERE id = ?", (new_url, row_id))
            conn.commit()
            print(f"Updated {len(rows)} rows in {table}.")
        except Exception as e:
            print(f"Could not migrate {table}.{col}: {e}")
            
    conn.close()
    print("Database migration to Cloudinary URLs complete.")

if __name__ == "__main__":
    migrate_db()
