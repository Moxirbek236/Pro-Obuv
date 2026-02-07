
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.pg_utils import execute_query
from app import app

def enable_extension():
    print("Enabling pg_trgm extension...")
    try:
        with app.app_context():
            execute_query("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            print("Extension pg_trgm enabled successfully or already exists.")
            
            # Optional: Create index for faster fuzzy search on products name
            # execute_query("CREATE INDEX IF NOT EXISTS products_name_trgm_idx ON products USING GIN (name gin_trgm_ops);")
            # print("Index created.")
            
    except Exception as e:
        print(f"Error enabling extension: {e}")

if __name__ == "__main__":
    enable_extension()
