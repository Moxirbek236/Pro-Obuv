import sqlite3, os
p = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
print('DB path:', p)
print('exists', os.path.exists(p), 'size', os.path.getsize(p) if os.path.exists(p) else 'N/A')
conn = sqlite3.connect(p)
cur = conn.cursor()
for t in ['users','menu_items','staff','couriers','news','branches','product_media','favorites','settings']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t} rows:', cur.fetchone()[0])
    except Exception as e:
        print(f'{t} error:', e)
cur.close()
conn.close()
