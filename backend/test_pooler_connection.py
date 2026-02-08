import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Original DSN from .env (direct IPv6)
# DATABASE_URL=postgresql://postgres:sjtmsimram10@db.hzkywrbbbykbdaapuyca.supabase.co:5432/postgres?sslmode=require

# New DSN (Pooling IPv4)
# Try different regions
REGIONS = ["eu-central-1", "us-east-1", "ap-southeast-1", "ap-south-1", "eu-west-1"]

for region in REGIONS:
    POOLING_DSN = f"postgresql://postgres.hzkywrbbbykbdaapuyca:sjtmsimram10@aws-0-{region}.pooler.supabase.com:6543/postgres?sslmode=require"
    print(f"Testing connection to {region}: {POOLING_DSN}")
    try:
        conn = psycopg2.connect(POOLING_DSN)
        print(f"✅ Successfully connected via {region} Pooler!")
        conn.close()
        break
    except Exception as e:
        print(f"❌ {region} failed: {e}")
