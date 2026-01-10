import sqlite3

def check_product_media():
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    # Let's see some samples of products that have multiple media
    cur.execute("SELECT menu_item_id, COUNT(*) as count FROM product_media GROUP BY menu_item_id HAVING count > 1")
    results = cur.fetchall()
    if not results:
        print("No products found with more than 1 media entry in 'product_media' table.")
        # Check total entries
        cur.execute("SELECT COUNT(*) FROM product_media")
        print(f"Total entries in 'product_media': {cur.fetchone()[0]}")
    else:
        print("Products with multiple media:")
        for res in results:
            print(f"Item ID: {res[0]}, Count: {res[1]}")
            # List them
            cur.execute("SELECT media_url, is_main FROM product_media WHERE menu_item_id = ?", (res[0],))
            for m in cur.fetchall():
                print(f"  - {m[0]} (is_main: {m[1]})")
    conn.close()

if __name__ == "__main__":
    check_product_media()
