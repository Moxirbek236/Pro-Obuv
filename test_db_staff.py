
import sqlite3
import json

def test():
    conn = sqlite3.connect('database.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT * FROM staff")
    columns = [column[0] for column in cur.description]
    results = []
    for row in cur.fetchall():
        results.append(dict(zip(columns, row)))
    print(json.dumps(results, indent=2))
    conn.close()

if __name__ == "__main__":
    test()
