import sqlite3

DB = 'database.sqlite3'
conn = sqlite3.connect(DB)
c = conn.cursor()

print('Connected to', DB)
print('\nTables:')
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(' -', row[0])

for t in ('chat_messages','ai_knowledge','ai_unanswered'):
    print('\nPRAGMA table_info(%s):' % t)
    try:
        rows = list(c.execute(f"PRAGMA table_info({t})"))
        if not rows:
            print('  (no columns / table may not exist)')
        for r in rows:
            print('  ', r)
    except Exception as e:
        print('  ERROR:', e)

conn.close()
