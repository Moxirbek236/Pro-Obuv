import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import init_db, fix_news_table, safe_init_database

print("=== INITIALIZING DATABASE ===")

try:
    print("1. Running safe_init_database()...")
    safe_init_database()
    print("✓ Safe init database completed")
    
    print("2. Running init_db()...")
    init_db()
    print("✓ Database initialization completed")
    
    print("3. Running fix_news_table()...")
    fix_news_table()
    print("✓ News table fix completed")
    
    print("\n=== DATABASE INITIALIZATION SUCCESS ===")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()