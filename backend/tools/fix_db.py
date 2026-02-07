import sqlite3

def fix_database():
    try:
        conn = sqlite3.connect('database.sqlite3')
        cur = conn.cursor()
        
        # Create menu_item_media table
        print("Checking menu_item_media table...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_item_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_item_id INTEGER NOT NULL,
            media_type TEXT DEFAULT 'image',
            media_url TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id) ON DELETE CASCADE
        )
        """)
        print("Created menu_item_media table.")
        
        # Check if we need to migrate existing images
        # Check if menu_items has image_url and no entries in media
        cur.execute("SELECT count(*) FROM menu_item_media")
        count = cur.fetchone()[0]
        if count == 0:
            print("Migrating existing main images to media table...")
            cur.execute("SELECT id, image_url FROM menu_items WHERE image_url IS NOT NULL AND image_url != ''")
            items = cur.fetchall()
            for item in items:
                mid, url = item
                cur.execute("INSERT INTO menu_item_media (menu_item_id, media_type, media_url, display_order) VALUES (?, 'image', ?, 0)", (mid, url))
            print(f"Migrated {len(items)} images.")
            
        # Create ai_unanswered table
        print("Checking ai_unanswered table...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_unanswered (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            times_asked INTEGER DEFAULT 1,
            sender TEXT,
            source TEXT DEFAULT 'WEB',
            last_asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create notifications table
        print("Checking notifications table...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            body TEXT,
            recipient_type TEXT, -- 'all', 'users', 'staff', 'courier', 'single'
            recipient_id INTEGER,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create user_notifications for read status tracking if needed (simplified for now)
        
        # Create social_links table
        print("Checking social_links table...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_name TEXT,
            url TEXT,
            icon_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        print("Database fix completed successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    fix_database()
