
import requests

def check_dashboard():
    session = requests.Session()
    # Try to login
    login_url = "http://localhost:5000/super-admin/login"
    # Note: Need CSRF token if enabled. Let's see if we can get it.
    try:
        r = session.get(login_url)
        # Extract CSRF token if present
        import re
        csrf_match = re.search(r'name="csrf_token" value="(.*?)"', r.text)
        csrf_token = csrf_match.group(1) if csrf_match else ""
        
        data = {
            "username": "admin", # or masteradmin
            "password": "sjtmsimram10",
            "csrf_token": csrf_token
        }
        # First try admin
        r = session.post(login_url, data=data)
        if "Dashboard" not in r.text:
             # Try masteradmin
             data["username"] = "masteradmin"
             r = session.post(login_url, data=data)
        
        dashboard_url = "http://localhost:5000/super-admin/dashboard-ultimate-m4st3r"
        r = session.get(dashboard_url)
        
        print(f"Status: {r.status_code}")
        print(f"Title: {re.search(r'<title>(.*?)</title>', r.text).group(1) if re.search(r'<title>(.*?)</title>', r.text) else 'No title'}")
        print(f"Body snippet: {r.text[:500]}")
        
        if "Dashboard" in r.text:
            print("SUCCESS: Dashboard loaded")
        else:
            print("FAILURE: Dashboard content not found")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_dashboard()
