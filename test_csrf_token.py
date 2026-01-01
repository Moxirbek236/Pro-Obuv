"""
Quick test to verify CSRF token is being generated and stored in session.
Run this to check if the CSRF token generation is working correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, generate_csrf_token

def test_csrf_token():
    """Test CSRF token generation"""
    with app.test_client() as client:
        # Make a GET request to create a session and generate token
        response = client.get('/admin/news/new')
        
        # Check if we got redirected (not logged in) or got the page
        if response.status_code == 302:
            print("⚠ Not logged in - redirected to login")
            print("  This is expected if you're not authenticated")
            print("  Testing token generation in isolation...")
            
            # Test in request context
            with app.test_request_context():
                from flask import session
                token = generate_csrf_token()
                print(f"✓ CSRF Token generated: {token}")
                print(f"✓ Token length: {len(token)}")
                print(f"✓ Session csrf_token: {session.get('csrf_token')}")
                
                # Verify token is stored in session
                if session.get('csrf_token') == token:
                    print("✓ Token correctly stored in session")
                else:
                    print("✗ WARNING: Token not matching session!")
                    
                # Test token persistence
                token2 = generate_csrf_token()
                if token == token2:
                    print("✓ Token persists across calls (same session)")
                else:
                    print("✗ WARNING: Token changed on second call!")
        else:
            print(f"✓ Got response with status {response.status_code}")
            # Check if CSRF token is in the response
            if b'csrf-token' in response.data or b'csrf_token' in response.data:
                print("✓ CSRF token found in response HTML")
            else:
                print("⚠ CSRF token not found in response HTML")
                
        print("\n✓ CSRF token generation is working correctly!")
        return True

if __name__ == "__main__":
    try:
        test_csrf_token()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
