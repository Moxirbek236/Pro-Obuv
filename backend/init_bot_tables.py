"""
Bot tables migration script.
Run this once to create bot_commands and bot_users tables.
"""
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from env
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    exit(1)

# Parse URL
url = urlparse(DATABASE_URL)
conn_params = {
    'host': url.hostname,
    'port': url.port or 5432,
    'user': url.username,
    'password': url.password,
    'database': url.path.lstrip('/').split('?')[0],
    'sslmode': 'require'
}

print(f"Connecting to database: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")

try:
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Creating bot_commands table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_commands (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            payload JSONB,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            processed_at TIMESTAMP,
            error TEXT
        )
    """)
    print("✓ bot_commands table created")
    
    print("Creating bot_users table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            last_active TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✓ bot_users table created")
    
    # Create indexes
    print("Creating indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bot_commands_status ON bot_commands(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bot_users_user_id ON bot_users(user_id)")
    print("✓ Indexes created")
    
    cur.close()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    exit(1)
