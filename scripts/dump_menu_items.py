import sqlite3, os, json
p = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')
conn = sqlite3.connect(p)
cur = conn.cursor()
try:
    cur.execute("SELECT id, name, category, description FROM menu_items ORDER BY id ASC")
    rows = cur.fetchall()
    print(json.dumps([{'id':r[0],'name':r[1],'category':r[2],'description':r[3]} for r in rows], ensure_ascii=False, indent=2))
except Exception as e:
    print('ERROR', e)
finally:
    cur.close()
    conn.close()
