"""
Test script to properly call the News API with CSRF protection.
This demonstrates how to get a CSRF token and use it in API requests.
"""

import requests
import re
import json

def test_news_api():
    """Test creating a news item via the API with proper CSRF token"""
    
    base_url = 'http://localhost:5000'
    
    # Step 1: Create a session (maintains cookies)
    session = requests.Session()
    
    print("Step 1: Initializing session (getting home page)...")
    res_home = session.get(f'{base_url}/')
    print(f"  Home Page Status: {res_home.status_code}")
    print(f"  Cookies after Home: {session.cookies.get_dict()}")
    
    print("Step 2: Getting CSRF token from debug endpoint...")
    response = session.get(f'{base_url}/_debug/session')
    print(f"  Debug Session Status: {response.status_code}")
    print(f"  Cookies after Debug: {session.cookies.get_dict()}")
    
    if response.status_code != 200:
        print(f"✗ Failed to get session info: {response.status_code}")
        # Fallback to home page if debug endpoint is disabled
        response = session.get(f'{base_url}/')
        match = re.search(r'<meta name="csrf-token" content="([^"]*)"', response.text)
        if not match:
            return False
        csrf_token = match.group(1)
    else:
        data = response.json()
        csrf_token = data.get('csrf_token_in_session')
        secret_key_id = data.get('secret_key_id')
        print(f"  Secret Key ID: {secret_key_id}")
    
    if not csrf_token:
        print("✗ CSRF token is empty")
        return False
    
    print(f"✓ CSRF token found: {csrf_token[:10]}...")
    print(f"  Token length: {len(csrf_token)}")
    
    # Step 3: Prepare the news data
    news_data = {
        "csrf_token": csrf_token,
        "title": "Test News from Script",
        "content": "This is a test news item created via API",
        "title_uz": "Test yangilik",
        "content_uz": "Bu API orqali yaratilgan test yangilik",
        "type": "news",
        "is_active": True,
        "display_order": 0
    }
    
    # Step 4: Make the API request with CSRF token in both header and body
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf_token
    }
    
    print("\nStep 2: Creating news item via API...")
    print(f"  URL: {base_url}/api/news")
    print(f"  Method: POST")
    print(f"  CSRF Token in header: {csrf_token[:20]}...")
    print(f"  CSRF Token in body: {csrf_token[:20]}...")
    
    response = session.post(
        f'{base_url}/api/news',
        json=news_data,
        headers=headers
    )
    
    # Step 5: Check the response
    print(f"\nStep 3: Response received")
    print(f"  Status code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"  Response body: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("\n✓ SUCCESS! News item created")
            if 'id' in response_data:
                print(f"  News ID: {response_data['id']}")
            return True
        else:
            print(f"\n✗ FAILED with status {response.status_code}")
            if 'error' in response_data:
                print(f"  Error: {response_data['error']}")
            return False
            
    except Exception as e:
        print(f"✗ Could not parse response: {e}")
        print(f"  Raw response: {response.text[:200]}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing News API with CSRF Protection")
    print("=" * 60)
    print()
    
    try:
        success = test_news_api()
        print()
        print("=" * 60)
        if success:
            print("✓ Test PASSED - API is working correctly!")
        else:
            print("✗ Test FAILED - Check the output above for details")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
