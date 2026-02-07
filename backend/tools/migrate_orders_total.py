import sqlite3

def migrate():
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN total REAL DEFAULT 0")
        print("Added 'total' column to 'orders' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: total" in str(e):
            print("'total' column already exists.")
        else:
            print(f"Error adding 'total' column: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
