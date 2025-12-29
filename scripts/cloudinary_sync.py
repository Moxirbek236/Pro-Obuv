import sqlite3
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.cloudinary_service import cloudinary_service

load_dotenv()

DB_PATH = 'database.sqlite3'

def sync_table_images(table, column, folder_base="uploads"):
    """
    Syncs local images in a specific table/column to Cloudinary.
    """
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get entries with local images
    query = f"SELECT id, {column} FROM {table} WHERE {column} LIKE '/static/%' OR {column} LIKE 'static/%'"
    cursor.execute(query)
    items = cursor.fetchall()

    if not items:
        print(f"No local images found in {table}.{column}")
        conn.close()
        return

    print(f"Found {len(items)} items to process in {table}.{column}")

    for item in items:
        item_id = item['id']
        image_url = item[column]
        
        # Normalize path
        clean_path = image_url.lstrip('/')
        # Security: ensure we are looking inside static
        if not (clean_path.startswith('static/') or clean_path.startswith('favicons/') or clean_path.startswith('icons/')):
             continue
             
        local_path = os.path.join(os.getcwd(), clean_path)

        if os.path.exists(local_path):
            print(f"Uploading {local_path}...")
            
            # Determine folder based on path
            folder = folder_base
            if "icons" in clean_path:
                folder = "icons"
            elif "favicons" in clean_path:
                folder = "favicons"
            elif "products" in clean_path:
                folder = "products"
            elif "avatars" in clean_path:
                folder = "avatars"
                
            # Use filename as public_id (without extension)
            filename = os.path.basename(clean_path)
            public_id = os.path.splitext(filename)[0]
            
            with open(local_path, 'rb') as f:
                result = cloudinary_service.upload_image(f, folder=folder, public_id=public_id)
                
            if result:
                new_url = result.get('secure_url')
                print(f"Successfully uploaded: {new_url}")
                
                # Update DB with the full Cloudinary URL
                update_query = f"UPDATE {table} SET {column} = ? WHERE id = ?"
                cursor.execute(update_query, (new_url, item_id))
                conn.commit()
                print(f"Updated DB for {table} item {item_id}")
            else:
                print(f"Failed to upload {local_path}")
        else:
            print(f"Local file not found: {local_path}")

    conn.close()

def sync_all():
    print("Starting global Cloudinary migration...")
    
    # Table, Column, Default Folder
    targets = [
        ('menu_items', 'image_url', 'products'),
        ('product_media', 'media_url', 'products'),
        ('users', 'avatar', 'avatars'),
        ('staff', 'avatar', 'avatars'),
        ('news', 'image_url', 'news'),
    ]
    
    # Check couriers table
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(couriers)")
        cols = [r[1] for r in cur.fetchall()]
        if 'avatar' in cols:
            targets.append(('couriers', 'avatar', 'avatars'))
        conn.close()
    except Exception:
        pass

    for table, col, folder in targets:
        try:
            sync_table_images(table, col, folder)
        except Exception as e:
            print(f"Error syncing {table}.{col}: {e}")
            
    print("Global migration complete.")

if __name__ == "__main__":
    sync_all()
