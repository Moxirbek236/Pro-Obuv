import urllib.request

try:
    response = urllib.request.urlopen('http://localhost:5000/super-admin-master-login-z9x4m')
    status = response.status
    content = response.read().decode('utf-8')
    
    print(f"Status: {status}")
    print(f"Has <main>: {'<main' in content}")
    print(f"Has login-form: {'login-form' in content}")
    print(f"Content length: {len(content)} bytes")
    
    if '<main' in content:
        print("\n✓ SUCCESS! The super admin login page is now loading correctly!")
    else:
        print("\n✗ PROBLEM: Page loaded but <main> element not found")
        
except Exception as e:
    print(f"Error: {e}")
    print("Make sure Flask is running at http://localhost:5000")
