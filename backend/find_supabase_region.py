import psycopg2
import sys

# Project details
PROJECT_REF = "hzkywrbbbykbdaapuyca"
PASSWORD = "sjtmsimram10"
USER = f"postgres.{PROJECT_REF}"

# List of all possible Supabase regions
REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-northeast-3", "ap-south-1",
    "ca-central-1",
    "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3", "eu-north-1",
    "me-south-1", "sa-east-1", "ap-southeast-3"
]

found = False
for region in REGIONS:
    host = f"aws-0-{region}.pooler.supabase.com"
    dsn = f"postgresql://{USER}:{PASSWORD}@{host}:6543/postgres?sslmode=require"
    try:
        # Short timeout to avoid hanging
        conn = psycopg2.connect(dsn, connect_timeout=3)
        print(f"✅ SUCCESS! Region is {region}")
        print(f"Connection String: {dsn}")
        conn.close()
        found = True
        break
    except psycopg2.OperationalError as e:
        err = str(e)
        if "Tenant or user not found" in err:
            # Region is reachable but project not there
            pass
        elif "timeout" in err or "lookup" in err:
            # Host not found or not reachable
            pass
        else:
            print(f"❓ {region}: {err.strip()}")
    except Exception as e:
        print(f"❌ {region}: {e}")

if not found:
    print("\nCould not find the region automatically. Please check your Supabase dashboard.")
