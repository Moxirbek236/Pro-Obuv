import os
import shutil
import sqlite3
import datetime
import traceback

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'database.sqlite3')

def now():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

if not os.path.exists(DB_PATH):
    print('Database file not found:', DB_PATH)
    raise SystemExit(1)

bak = DB_PATH + '.bak.' + now()
print('Backing up', DB_PATH, '->', bak)
shutil.copy2(DB_PATH, bak)

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("PRAGMA integrity_check;")
    row = cur.fetchone()
    print('PRAGMA integrity_check ->', row)
    conn.close()
except Exception as e:
    print('Error running integrity_check:', e)
    traceback.print_exc()
    conn = None

if conn is not None and row and row[0] == 'ok':
    print('Database integrity OK. No repair needed.')
    raise SystemExit(0)

# Try dump and recreate
print('Database appears corrupted. Attempting to dump and recreate...')
DUMP_SQL = DB_PATH + '.dump.sql.' + now()
FIXED_DB = DB_PATH + '.fixed.' + now()

try:
    src = sqlite3.connect(DB_PATH)
    with open(DUMP_SQL, 'w', encoding='utf-8') as f:
        for line in src.iterdump():
            f.write('%s\n' % line)
    src.close()
    print('Dumped SQL to', DUMP_SQL)

    # Create new DB and load SQL
    dst = sqlite3.connect(FIXED_DB)
    with open(DUMP_SQL, 'r', encoding='utf-8') as f:
        sql = f.read()
    dst.executescript(sql)
    dst.close()
    print('Recreated DB at', FIXED_DB)

    # Replace original with fixed
    replaced = DB_PATH + '.replaced.' + now()
    shutil.move(DB_PATH, replaced)
    shutil.move(FIXED_DB, DB_PATH)
    print('Replaced original DB. Original moved to', replaced)
    print('Repair successful. Keep the backup at', bak)
    raise SystemExit(0)
except Exception as e:
    print('Dump-and-recreate failed:', e)
    traceback.print_exc()
    print('You can try manual recovery using the sqlite3 CLI or restore from a backup.')
    raise SystemExit(2)
