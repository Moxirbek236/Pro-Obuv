import sqlite3

def get_schema():
    conn = sqlite3.connect('database.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='menu_items'")
    print(cursor.fetchone()[0])
    conn.close()

if __name__ == "__main__":
    get_schema()
