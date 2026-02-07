import sqlite3, os
p = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
print('DB path:', p)
conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute('PRAGMA foreign_keys=OFF;')
conn.commit()

print('Creating menu_items...')
cur.execute('''
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    available BOOLEAN DEFAULT 1,
    stock_quantity INTEGER DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    discount_percentage REAL DEFAULT 0.0,
    sizes TEXT DEFAULT NULL,
    colors TEXT DEFAULT NULL,
    created_at TEXT NOT NULL
);
''')

print('Creating news...')
cur.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    type TEXT NOT NULL DEFAULT 'news',
    image_url TEXT,
    video_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_by INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
''')

print('Creating branches...')
cur.execute('''
CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    phone TEXT,
    working_hours TEXT,
    is_active BOOLEAN DEFAULT 1,
    delivery_radius REAL DEFAULT 0,
    accepts_international BOOLEAN DEFAULT 0,
    international_countries TEXT,
    created_at TEXT NOT NULL
);
''')

print('Creating favorites...')
cur.execute('''
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (menu_item_id) REFERENCES menu_items (id),
    UNIQUE(user_id, menu_item_id)
);
''')

print('Creating settings...')
cur.execute('''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT
);
''')

conn.commit()
cur.execute('PRAGMA foreign_keys=ON;')
conn.commit()
cur.close()
conn.close()
print('Done')
