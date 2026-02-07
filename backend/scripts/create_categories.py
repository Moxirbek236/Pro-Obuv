import sqlite3

conn = sqlite3.connect('restaurant.db')
cursor = conn.cursor()

# Create categories table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        display_order INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TEXT NOT NULL
    )
''')

# Insert basic categories
cursor.execute("SELECT COUNT(*) FROM categories")
if cursor.fetchone()[0] == 0:
    from datetime import datetime
    now = datetime.now().isoformat()
    
    categories = [
        ('tufli', 'Klassik va zamonaviy tufli', 1, 1, now),
        ('etik', 'Qishki va ishchi etiklari', 2, 1, now),
        ('krossovka', 'Sport va kundalik krossovkalar', 3, 1, now),
        ('sandalet', 'Yozgi sandaletlar', 4, 1, now),
        ('boshqa', 'Boshqa turdagi oyoq kiyimlar', 5, 1, now)
    ]
    
    cursor.executemany('''
        INSERT INTO categories (name, description, display_order, is_active, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', categories)

conn.commit()
conn.close()

print("Categories table created and populated successfully!")
