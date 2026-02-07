import sqlite3

conn = sqlite3.connect('restaurant.db')
cursor = conn.cursor()

# Check tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', [t[0] for t in tables])

# Check categories table specifically
if 'categories' in [t[0] for t in tables]:
    cursor.execute('PRAGMA table_info(categories)')
    columns = cursor.fetchall()
    print('Categories columns:', [col[1] for col in columns])
else:
    print('Categories table does not exist')

conn.close()
