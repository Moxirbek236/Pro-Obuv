import sqlite3
import os
DB = r"c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\database.sqlite3"
if not os.path.exists(DB):
    print("DB file not found:", DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

try:
    cur.execute("PRAGMA foreign_keys;")
    fk = cur.fetchone()[0]
    print("PRAGMA foreign_keys:", fk)
except Exception as e:
    print("PRAGMA foreign_keys check failed:", e)

print('\nLast 20 ratings:')
cur.execute("PRAGMA table_info(ratings);")
rating_cols = [r[1] for r in cur.fetchall() or []]

if 'branch_id' in rating_cols:
    cur.execute("SELECT id, user_id, menu_item_id, branch_id, rating, comment, created_at FROM ratings ORDER BY id DESC LIMIT 20")
else:
    cur.execute("SELECT id, user_id, menu_item_id, rating, comment, created_at FROM ratings ORDER BY id DESC LIMIT 20")
rows = cur.fetchall()
if not rows:
    print('No ratings rows found')
else:
        for r in rows:
            rid = r['id']
            uid = r['user_id']
            mid = r['menu_item_id'] if 'menu_item_id' in r.keys() else None
            bid = r['branch_id'] if 'branch_id' in r.keys() else None
            print(f"# {rid}: user_id={uid}, menu_item_id={mid}, branch_id={bid}, rating={r['rating']}, created_at={r['created_at']}")
            # check user
            cur.execute("SELECT id FROM users WHERE id = ?", (uid,))
            u = cur.fetchone()
            if not u:
                print(f"   -> MISSING user id={uid}")
            else:
                print(f"   -> user exists id={u['id']}")

            # check menu item or branch
            if bid is not None:
                cur.execute("SELECT id, name FROM branches WHERE id = ?", (bid,))
                b = cur.fetchone()
                if not b:
                    print(f"   -> MISSING branch id={bid}")
                else:
                    print(f"   -> branch exists id={b['id']}, name={b['name']}")
            elif mid is None:
                print("   -> neither menu_item_id nor branch_id set")
            else:
                cur.execute("SELECT id, name FROM menu_items WHERE id = ?", (mid,))
                m = cur.fetchone()
                if not m:
                    print(f"   -> MISSING menu_item id={mid}")
                else:
                    print(f"   -> menu_item exists id={m['id']}, name={m['name']}")

# Also scan for ratings attempted timestamps around the log time (16:11)
print('\nRatings count:', cur.execute('SELECT COUNT(*) FROM ratings').fetchone()[0])
conn.close()
