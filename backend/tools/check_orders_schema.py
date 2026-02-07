import sqlite3

def check_schema():
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(orders)")
    columns = cur.fetchall()
    print("Columns in 'orders' table:")
    for col in columns:
        print(col)
    conn.close()

if __name__ == "__main__":
    check_schema()
