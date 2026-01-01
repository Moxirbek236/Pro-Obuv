import sqlite3
import json

def check():
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT id, menu_item_id, media_url FROM product_media ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    print("Recent product_media entries:")
    for r in rows:
        print(r)
    
    cur.execute("SELECT id, image_url FROM menu_items ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    print("\nRecent menu_items entries:")
    for r in rows:
        print(r)
    
    conn.close()

if __name__ == "__main__":
    check()
