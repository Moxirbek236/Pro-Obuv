import sqlite3,traceback
DB=r'c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\database.sqlite3'
try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    now='2025-09-13T00:00:00'
    cur.execute("INSERT INTO cart_items (user_id, session_id, menu_item_id, quantity, created_at, size, color) VALUES (?,?,?,?,?,?,?)",
                (1, 'test-session', 9, 2, now, '42', 'black'))
    conn.commit()
    print('INSERT OK, id=', cur.lastrowid)
    conn.close()
except Exception as e:
    print('INSERT ERROR', e)
    traceback.print_exc()
