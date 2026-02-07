import sqlite3

def check():
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT menu_item_id, count(id) FROM product_media GROUP BY menu_item_id ORDER BY menu_item_id DESC LIMIT 10")
    rows = cur.fetchall()
    print("Media count per item (recent 10 items):")
    for r in rows:
        print(f"Item ID {r[0]}: {r[1]} media files")
    conn.close()

if __name__ == "__main__":
    check()
