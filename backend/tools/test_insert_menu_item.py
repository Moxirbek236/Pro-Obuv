import sqlite3,traceback
DB=r'c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\database.sqlite3'
try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    now='2025-09-13T00:00:00'
    cur.execute("INSERT INTO menu_items (name, price, category, description, sizes, colors, discount_percentage, image_url, created_at, available) VALUES (?,?,?,?,?,?,?,?,?,1)",
                ('Test Shoe', 199.99, 'footwear', 'A test shoe', '36,37,38', 'black,white', 0, '/static/test.png', now))
    conn.commit()
    print('INSERT OK, id=', cur.lastrowid)
    conn.close()
except Exception as e:
    print('INSERT ERROR', e)
    traceback.print_exc()
