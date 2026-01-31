#!/usr/bin/env python3
"""Quick test of superadmin login page rendering"""
import sys
sys.path.insert(0, '/Safety.uz')

try:
    from app import app
    
    # Create a test client
    client = app.test_client()
    
    # Request the superadmin login page
    response = client.get('/super-admin-master-login-z9x4m')
    
    print(f"Response status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content length: {len(response.data)}")
    print()
    
    # Check if <main> element is present
    content = response.get_data(as_text=True)
    if '<main' in content:
        print("✓ SUCCESS: <main> element found in response!")
        # Find the main tag
        main_idx = content.find('<main')
        print(f"\nMain element preview:")
        print(content[main_idx:main_idx+200])
    else:
        print("✗ FAILURE: <main> element NOT found")
        # Show what's in the page
        if 'login-form' in content:
            print("  BUT login-form IS found")
        print(f"\nFirst 500 chars of response:")
        print(content[:500])
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
