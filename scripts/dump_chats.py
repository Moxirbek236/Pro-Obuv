import sqlite3
import json
import os

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')

out = {"db_path": DB, "exists": os.path.exists(DB)}

try:
    if not os.path.exists(DB):
        print(json.dumps(out, indent=2))
        raise SystemExit(0)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # check tables
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    out['tables'] = tables

    def fetch_all(q, params=()):
        try:
            rows = cur.execute(q, params).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            return {"error": str(e)}

    out['chats'] = fetch_all("SELECT id, name, is_group, created_at FROM chats ORDER BY id DESC LIMIT 200")
    out['chat_members_sample'] = fetch_all("SELECT chat_id, member_type, member_id FROM chat_members ORDER BY chat_id LIMIT 500")
    out['chat_messages_sample'] = fetch_all("SELECT id, chat_id, sender_type, sender_id, text, created_at FROM chat_messages ORDER BY id DESC LIMIT 500")

    # distinct member types
    try:
        dm = cur.execute("SELECT DISTINCT member_type FROM chat_members").fetchall()
        out['distinct_member_types_in_members'] = [r[0] for r in dm]
    except Exception as e:
        out['distinct_member_types_in_members'] = {'error': str(e)}

    try:
        dr = cur.execute("SELECT DISTINCT sender_type FROM chat_messages").fetchall()
        out['distinct_sender_types_in_messages'] = [r[0] for r in dr]
    except Exception as e:
        out['distinct_sender_types_in_messages'] = {'error': str(e)}

    conn.close()
except Exception as e:
    out['error'] = str(e)

print(json.dumps(out, indent=2, ensure_ascii=False))
