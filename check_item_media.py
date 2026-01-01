import sqlite3

def check(item_id):
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT id, media_url, display_order, is_main FROM product_media WHERE menu_item_id = ?", (item_id,))
    rows = cur.fetchall()
    print(f"Media for item {item_id}:")
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    check(50) # Checking item 50 which I thought had multiple earlier
    check(56) # Checking latest item
