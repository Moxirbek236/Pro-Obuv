import psycopg2
import sys
import socket

# Project details
PROJECT_REF = "hzkywrbbbykbdaapuyca"
PASSWORD = "sjtmsimram10"
USER = f"postgres.{PROJECT_REF}"

# List of all Supabase regions (collected from search and docs)
REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", 
    "ap-south-1", "ca-central-1", "eu-central-1", "eu-west-1", "eu-west-2", 
    "eu-west-3", "eu-north-1", "eu-central-2", "me-south-1", "sa-east-1",
    "ap-southeast-3", "af-south-1"
]

print(f"Scanning {len(REGIONS)} regions for project {PROJECT_REF}...")

found = False
for region in REGIONS:
    host = f"aws-0-{region}.pooler.supabase.com"
    
    # 1. DNS check first (fast)
    try:
        socket.gethostbyname(host)
    except socket.gaierror:
        # Host doesn't exist, skip
        continue

    print(f"Testing {region}...", end=" ", flush=True)
    
    dsn = f"postgresql://{USER}:{PASSWORD}@{host}:6543/postgres?sslmode=require"
    try:
        # Use short timeout
        conn = psycopg2.connect(dsn, connect_timeout=3)
        print("✅ SUCCESS!")
        print(f"\nYour DATABASE_URL for Render should be:")
        print(f"postgresql://postgres.{PROJECT_REF}:[YOUR_PASSWORD]@{host}:6543/postgres?sslmode=require")
        conn.close()
        found = True
        break
    except psycopg2.OperationalError as e:
        err = str(e)
        if "Tenant or user not found" in err:
            print("❌ Tenant not found here.")
        elif "password authentication failed" in err:
            print("⚠️ Correct Region! (But password failed)")
            print(f"Region: {region}")
            found = True
            break
        else:
            print(f"❓ Error: {err.strip()}")
    except Exception as e:
        print(f"❌ Error: {e}")

if not found:
    print("\nCould not find the region. Are you sure 'hzkywrbbbykbdaapuyca' is the project ID?")
