
import sqlite3
import datetime

DB_NAME = 'database.sqlite3'

def update_schema():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    print("Checking for site_settings table...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if we need to insert default values
    defaults = {
        'site_phone': '+998 90 123 45 67',
        'site_email': 'info@safety.uz',
        'site_telegram': 'https://t.me/proobuvLLC',
        'site_telegram_username': '@proobuvLLC',
        'site_address': 'Toshkent sh, Chilonzor tumani'
    }
    
    for key, val in defaults.items():
        c.execute('SELECT key FROM site_settings WHERE key = ?', (key,))
        if not c.fetchone():
            c.execute('INSERT INTO site_settings (key, value) VALUES (?, ?)', (key, val))
            print(f"Inserted default setting: {key}")

    print("Checking for social_links table...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            url TEXT,
            icon TEXT,
            active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Default social links
    default_links = [
        ('Telegram', 'https://t.me/proobuvLLC', 'bi bi-telegram', 1, 10),
        ('Instagram', 'https://instagram.com/safety_uz', 'bi bi-instagram', 1, 20),
        ('Facebook', 'https://facebook.com/safety_uz', 'bi bi-facebook', 1, 30),
        ('YouTube', 'https://youtube.com/@safety_uz', 'bi bi-youtube', 1, 40)
    ]
    
    c.execute('SELECT count(*) FROM social_links')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO social_links (platform, url, icon, active, sort_order) VALUES (?, ?, ?, ?, ?)', default_links)
        print("Inserted default social links")

    conn.commit()
    conn.close()
    print("Schema update for settings completed.")

if __name__ == '__main__':
    update_schema()
