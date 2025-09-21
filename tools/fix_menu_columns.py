import sqlite3,traceback,sys
DB=r'c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\database.sqlite3'

def cols():
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute('PRAGMA table_info(menu_items);')
    rows=cur.fetchall()
    conn.close()
    return [r[1] for r in rows]

print('COLUMNS BEFORE:', cols())

try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    try:
        cur.execute('ALTER TABLE menu_items ADD COLUMN sizes TEXT;')
        conn.commit()
        print('ALTER sizes: OK')
    except Exception as e:
        print('ALTER sizes: ERROR', e)
        traceback.print_exc()
    try:
        cur.execute('ALTER TABLE menu_items ADD COLUMN colors TEXT;')
        conn.commit()
        print('ALTER colors: OK')
    except Exception as e:
        print('ALTER colors: ERROR', e)
        traceback.print_exc()
    conn.close()
except Exception as e:
    print('CONN ERROR', e)
    traceback.print_exc()

print('COLUMNS AFTER:', cols())
sys.exit(0)
