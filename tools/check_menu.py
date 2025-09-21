import sqlite3, json
con=sqlite3.connect('database.sqlite3')
cur=con.cursor()
try:
    cur.execute('SELECT COUNT(*) FROM menu_items')
    cnt=cur.fetchone()[0]
    print('COUNT', cnt)
    cur.execute('SELECT id,name,price,category FROM menu_items LIMIT 10')
    rows=cur.fetchall()
    print(json.dumps(rows, ensure_ascii=False))
except Exception as e:
    print('ERR', e)
con.close()
