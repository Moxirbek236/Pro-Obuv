import sqlite3
import os

conn = sqlite3.connect('database.sqlite3')
cursor = conn.cursor()

# Get all menu items with image URLs
cursor.execute('SELECT id, name, image_url FROM menu_items WHERE image_url IS NOT NULL AND image_url != ""')
rows = cursor.fetchall()

updates = []
for row in rows:
    item_id, name, image_url = row
    if image_url and '/static/uploads/products/' in image_url:
        # Extract filename without extension
        filename = os.path.basename(image_url)
        base_name = os.path.splitext(filename)[0]

        # Check if .webp version exists
        webp_path = f'static/uploads/products/{base_name}.webp'
        if os.path.exists(webp_path):
            new_url = f'/static/uploads/products/{base_name}.webp'
            updates.append((new_url, item_id))
            print(f'Will update {item_id}: {image_url} -> {new_url}')

print(f'Found {len(updates)} items to update')

# Update the database
for new_url, item_id in updates:
    cursor.execute('UPDATE menu_items SET image_url = ? WHERE id = ?', (new_url, item_id))

conn.commit()
conn.close()
print('Database updated successfully')