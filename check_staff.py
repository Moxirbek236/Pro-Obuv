import sqlite3

conn = sqlite3.connect('database.sqlite3')
cur = conn.cursor()

# Check if staff table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff';")
table_exists = cur.fetchone()

if table_exists:
    # Check staff count
    cur.execute("SELECT COUNT(*) FROM staff")
    count = cur.fetchone()[0]
    print(f'Staff count: {count}')
    
    if count > 0:
        # Show staff members
        cur.execute("SELECT id, first_name, last_name, phone FROM staff LIMIT 5")
        staff = cur.fetchall()
        print('Staff members:')
        for s in staff:
            print(f'  ID: {s[0]}, Name: {s[1]} {s[2]}, Phone: {s[3]}')
    else:
        print('No staff members found. Need to create staff accounts.')
else:
    print('Staff table does not exist.')

conn.close()
