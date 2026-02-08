import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database.sqlite3')
print(f'Database path: {db_path}')
print(f'Exists: {os.path.exists(db_path)}')

if not os.path.exists(db_path):
    print('Database file not found!')
    exit(1)
    
size = os.path.getsize(db_path)
print(f'Size: {size} bytes')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print('=== ALL TABLES ===')
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cur.fetchall()
for table in tables:
    print(f'- {table[0]}')

print('\n=== CHECKING NEWS TABLE ===')
try:
    cur.execute('SELECT COUNT(*) FROM news')
    count = cur.fetchone()[0]
    print(f'News table exists with {count} items')
except sqlite3.OperationalError as e:
    print(f'News table error: {e}')

conn.close()