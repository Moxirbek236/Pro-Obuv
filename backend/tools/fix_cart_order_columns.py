import sqlite3,traceback,sys
DB=r'c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\database.sqlite3'

def cols(table):
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    rows=cur.fetchall()
    conn.close()
    return [r[1] for r in rows]

print('BEFORE cart_items:', cols('cart_items'))
print('BEFORE order_details:', cols('order_details'))

try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    # Add size and color to cart_items
    existing=[r[1] for r in cur.execute("PRAGMA table_info(cart_items);")]
    if 'size' not in existing:
        try:
            cur.execute("ALTER TABLE cart_items ADD COLUMN size TEXT;")
            conn.commit(); print('Added cart_items.size')
        except Exception as e:
            print('Failed adding cart_items.size',e)
            traceback.print_exc()
    if 'color' not in existing:
        try:
            cur.execute("ALTER TABLE cart_items ADD COLUMN color TEXT;")
            conn.commit(); print('Added cart_items.color')
        except Exception as e:
            print('Failed adding cart_items.color',e)
            traceback.print_exc()

    # Add size and color to order_details
    existing=[r[1] for r in cur.execute("PRAGMA table_info(order_details);")]
    if 'size' not in existing:
        try:
            cur.execute("ALTER TABLE order_details ADD COLUMN size TEXT;")
            conn.commit(); print('Added order_details.size')
        except Exception as e:
            print('Failed adding order_details.size',e)
            traceback.print_exc()
    if 'color' not in existing:
        try:
            cur.execute("ALTER TABLE order_details ADD COLUMN color TEXT;")
            conn.commit(); print('Added order_details.color')
        except Exception as e:
            print('Failed adding order_details.color',e)
            traceback.print_exc()

    conn.close()
except Exception as e:
    print('CONN ERROR',e)
    traceback.print_exc()

print('AFTER cart_items:', cols('cart_items'))
print('AFTER order_details:', cols('order_details'))
sys.exit(0)
