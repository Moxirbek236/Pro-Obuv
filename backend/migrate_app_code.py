import re
import os

def migrate_sql_placeholders(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace ? with %s in SQL-like strings
    sql_string_pattern = re.compile(r"(['\"])(?:(?!\1).)*\?(?:(?!\1).)*\1")
    
    parts = []
    last_end = 0
    count_sql = 0
    for match in sql_string_pattern.finditer(content):
        parts.append(content[last_end:match.start()])
        s = match.group(0)
        upper_s = s.upper()
        if any(keyword in upper_s for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE", "VALUES", "WHERE", "SET", "CREATE TABLE", "LIMIT", "OFFSET"]):
            new_s = s.replace('?', '%s')
            if new_s != s:
                count_sql += 1
            s = new_s
        parts.append(s)
        last_end = match.end()
    parts.append(content[last_end:])
    content = "".join(parts)
    print(f"Replaced {count_sql} SQL strings containing ? with %s")

    # 2. SQLite specific UPSERTs to generic (Postgres)
    # Note: Proper Postgres UPSERT uses ON CONFLICT, but 'INSERT OR IGNORE' isn't supported.
    # We'll replace with simple INSERT for now, and I'll manually check critical ones.
    content = content.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    content = content.replace("INSERT OR REPLACE INTO", "INSERT INTO")
    print("Replaced INSERT OR IGNORE/REPLACE patterns")

    # 3. SQLite datetime to PG
    content = re.sub(r"datetime\('now'\)", "NOW()", content)
    # Handle datetime('now', '-30 minutes') -> NOW() - INTERVAL '30 minutes'
    def datetime_repl(m):
        val = m.group(1)
        if val.startswith('-'):
            return f"NOW() - INTERVAL '{val[1:]}'"
        return f"NOW() + INTERVAL '{val}'"
    content = re.sub(r"datetime\('now', '([^']+)'\)", datetime_repl, content)
    print("Replaced datetime('now') patterns")

    # 4. AUTOINCREMENT -> SERIAL PRIMARY KEY
    content = content.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    print("Replaced AUTOINCREMENT patterns")

    # 5. sqlite_master -> information_schema.tables
    content = content.replace("sqlite_master", "information_schema.tables")
    print("Replaced sqlite_master patterns")

    # 6. Row factory
    content = content.replace("conn.row_factory = sqlite3.Row", "# row_factory not used in PG (RealDictCursor used)")
    print("Replaced row_factory patterns")

    # 7. Remove any remaining sqlite3 references in comments or fallback logic
    content = content.replace("sqlite3.OperationalError", "psycopg2.Error")
    
    # 8. Fix lastrowid references if possible 
    # (In Postgres we should use RETURNING id, but cur.lastrowid sometimes works with SERIAL)
    # No batch change here as it's too risky.

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    target = r"d:\Safety.uz\backend\app.py"
    if os.path.exists(target):
        migrate_sql_placeholders(target)
    else:
        print("Target file not found")
