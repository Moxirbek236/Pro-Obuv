import sqlite3
DB = 'database.sqlite3'
print('Connecting to', DB)
conn = sqlite3.connect(DB)
cur = conn.cursor()
print('Creating ai_knowledge and ai_unanswered if missing...')
cur.executescript("""
CREATE TABLE IF NOT EXISTS ai_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_pattern TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_by TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_unanswered (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    sender TEXT DEFAULT 'web',
    times_asked INTEGER DEFAULT 1,
    last_asked_at TEXT NOT NULL
);
""")
print('Checking chat_messages columns...')
try:
    cur.execute("PRAGMA table_info('chat_messages')")
    cols = [r[1] for r in cur.fetchall() or []]
    print('chat_messages columns:', cols)
    if 'sender' not in cols and cols:
        try:
            cur.execute("ALTER TABLE chat_messages ADD COLUMN sender TEXT")
            print('Added sender column to chat_messages')
        except Exception as e:
            print('Failed to add sender column:', e)
    else:
        print('sender column already present or chat_messages missing')
except Exception as e:
    print('PRAGMA failed:', e)

conn.commit()
conn.close()
print('Done')
