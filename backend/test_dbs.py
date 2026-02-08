import psycopg2
import sys
from dotenv import load_dotenv
import os

load_dotenv()

# Neon Connection String
NEON_URL = "postgresql://neondb_owner:npg_OquwgU9JZI8o@ep-flat-wind-aij3lx8p-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
# Supabase Connection String (from .env)
SUPABASE_URL = os.environ.get("DATABASE_URL")

def test_connection(name, url):
    print(f"Testing connection to {name}...")
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        print(f"✅ {name} connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ {name} connection failed: {e}")
        return False

print("--- Database Connection Test ---")
supabase_ok = test_connection("Supabase", SUPABASE_URL)
neon_ok = test_connection("Neon", NEON_URL)

if not supabase_ok:
    print("\n⚠️ Note: Supabase is unreachable from this environment. This might be due to IPv6 limitations.")
    print("I will check if there's a local SQLite backup to migrate from instead.")

if not neon_ok:
    print("\n❌ Neon is also unreachable. Please check the credentials.")
