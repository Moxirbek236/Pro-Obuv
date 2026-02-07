
import urllib.request
import json
import time

def test_endpoint(path):
    url = f"http://127.0.0.1:5000{path}"
    print(f"Testing {url}...")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            print(f"Status: {status}")
            data = json.loads(response.read().decode())
            print(f"Response: {str(data)[:200]}...")
            return True
    except Exception as e:
        print(f"Error testing {url}: {e}")
        return False

if __name__ == "__main__":
    # Wait for server startup
    time.sleep(2)
    
    # Test root (might be HTML)
    # test_endpoint("/")
    
    # Test API endpoint (DB dependent)
    # /api/categories fetches from DB
    success = test_endpoint("/api/categories")
    
    if success:
        print("\n✅ API Test PASSED")
    else:
        print("\n❌ API Test FAILED")
