import os
import sys
from dotenv import load_dotenv

# Path logic
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app import execute_query, app_logger

def final_health_check():
    print("🔍 Running Final Health Check on New Database (Neon)...")
    try:
        # 1. Test basic connection
        result = execute_query("SELECT COUNT(*) as count FROM users", fetch_one=True)
        user_count = result['count'] if result else 0
        print(f"✅ Connection successful! Found {user_count} users in 'users' table.")
        
        # 2. Test fetching products
        products = execute_query("SELECT name_uz FROM menu_items LIMIT 3", fetch_all=True)
        if products:
            print(f"✅ Successfully fetched data. Sample items: {[p['name_uz'] for p in products]}")
        else:
            print("⚠️ Database is connected but 'menu_items' table seems empty or couldn't be fetched.")
            
        print("\n✨ Database migration and verification complete!")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    final_health_check()
