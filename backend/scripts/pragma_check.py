import sqlite3, os
p = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
print('DB path:', p)
conn = sqlite3.connect(p)
cur = conn.cursor()
for t in ['branches','menu_items','news','settings']:
    try:
        cur.execute(f'PRAGMA table_info({t});')
        print(t, cur.fetchall())
    except Exception as e:
        print(t, 'error', e)
cur.close()
conn.close()
