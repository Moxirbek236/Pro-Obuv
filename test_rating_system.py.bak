#!/usr/bin/env python3
"""
Test script to diagnose the rating system issues in the Flask app.
This script will:
1. Check the ratings table schema
2. Test rating submission
3. Test rating retrieval
"""

import sys
import os
import sqlite3
import json
import requests

# Add the current directory to Python path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly from app.py file
try:
    from app import app, get_db, execute_query
except ImportError:
    # If that fails, try importing from the main app module
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", "app.py")
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app = app_module.app
    get_db = app_module.get_db
    execute_query = app_module.execute_query

def check_ratings_table_schema():
    """Check the current schema of the ratings table"""
    print("=== Checking ratings table schema ===")
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get table info
        cur.execute("PRAGMA table_info(ratings);")
        columns = cur.fetchall()
        
        print("Ratings table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
        
        # Check if the table has any data
        cur.execute("SELECT COUNT(*) FROM ratings")
        count = cur.fetchone()[0]
        print(f"Current ratings count: {count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking ratings table: {str(e)}")
        return False

def check_menu_items():
    """Check available menu items for testing"""
    print("\n=== Checking menu items ===")
    try:
        rows = execute_query("SELECT id, name FROM menu_items LIMIT 5", fetch_all=True)
        print("Available menu items:")
        for row in rows:
            print(f"  - ID: {row['id']}, Name: {row['name']}")
        return rows[0]['id'] if rows else None
    except Exception as e:
        print(f"Error checking menu items: {str(e)}")
        return None

def check_users():
    """Check available users for testing"""
    print("\n=== Checking users ===")
    try:
        rows = execute_query("SELECT id, first_name, last_name FROM users LIMIT 3", fetch_all=True)
        print("Available users:")
        for row in rows:
            print(f"  - ID: {row['id']}, Name: {row['first_name']} {row['last_name']}")
        return rows[0]['id'] if rows else None
    except Exception as e:
        print(f"Error checking users: {str(e)}")
        return None

def test_rating_insert():
    """Test inserting a rating directly into database"""
    print("\n=== Testing direct rating insert ===")
    
    menu_item_id = check_menu_items()
    user_id = check_users()
    
    if not menu_item_id or not user_id:
        print("Cannot test: missing menu items or users")
        return False
        
    try:
        from datetime import datetime
        now = datetime.now().isoformat()
        
        # Try inserting a test rating
        execute_query(
            "INSERT INTO ratings (menu_item_id, branch_id, user_id, rating, comment, created_at) VALUES (?, NULL, ?, ?, ?, ?)",
            (menu_item_id, user_id, 5, "Test rating", now)
        )
        print("✓ Direct rating insert successful")
        return True
    except Exception as e:
        print(f"✗ Direct rating insert failed: {str(e)}")
        return False

def test_rating_api_with_app():
    """Test the rating API using Flask test client"""
    print("\n=== Testing rating API ===")
    
    with app.test_client() as client:
        with app.app_context():
            # First check if we have menu items
            menu_item_id = check_menu_items()
            if not menu_item_id:
                print("Cannot test API: no menu items available")
                return False
            
            # Create a test session (simulate logged in user)
            with client.session_transaction() as sess:
                sess['user_id'] = 1  # Assume user ID 1 exists
                sess['csrf_token'] = 'test_token'
            
            # Test submitting a rating
            rating_data = {
                'menu_item_id': menu_item_id,
                'rating': 4,
                'comment': 'Test API rating',
                'csrf_token': 'test_token'
            }
            
            response = client.post('/api/submit-rating', 
                                 data=json.dumps(rating_data),
                                 content_type='application/json')
            
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Data: {response.get_json()}")
            
            if response.status_code == 200:
                print("✓ Rating API test successful")
                return True
            else:
                print("✗ Rating API test failed")
                return False

def test_get_ratings_api():
    """Test the get ratings API"""
    print("\n=== Testing get ratings API ===")
    
    with app.test_client() as client:
        menu_item_id = check_menu_items()
        if not menu_item_id:
            print("Cannot test: no menu items available")
            return False
            
        response = client.get(f'/api/get-menu-ratings/{menu_item_id}')
        print(f"Get Ratings API Status: {response.status_code}")
        print(f"Get Ratings API Data: {response.get_json()}")
        
        if response.status_code == 200:
            print("✓ Get ratings API test successful")
            return True
        else:
            print("✗ Get ratings API test failed")
            return False

def main():
    print("Starting rating system diagnostics...")
    print("=" * 50)
    
    # Check database schema
    schema_ok = check_ratings_table_schema()
    
    if schema_ok:
        # Test direct database insert
        insert_ok = test_rating_insert()
        
        # Test API endpoints
        api_ok = test_rating_api_with_app()
        get_api_ok = test_get_ratings_api()
        
        print("\n" + "=" * 50)
        print("SUMMARY:")
        print(f"✓ Schema check: {'PASS' if schema_ok else 'FAIL'}")
        print(f"✓ Direct insert: {'PASS' if insert_ok else 'FAIL'}")
        print(f"✓ Submit API: {'PASS' if api_ok else 'FAIL'}")
        print(f"✓ Get ratings API: {'PASS' if get_api_ok else 'FAIL'}")
        
        if all([schema_ok, insert_ok, api_ok, get_api_ok]):
            print("\n🎉 Rating system appears to be working correctly!")
        else:
            print("\n❌ Rating system has issues that need to be fixed.")
    else:
        print("\n❌ Cannot proceed due to schema issues.")

if __name__ == '__main__':
    main()