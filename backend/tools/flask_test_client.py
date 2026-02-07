import traceback
import sys
import os

# Ensure repository root is on sys.path so 'app' module can be imported when running from tools/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from app import app

    with app.test_client() as c:
        rv = c.get('/super-admin-master-login-z9x4m')
        print('status', rv.status_code)
        print(rv.data.decode('utf-8')[:2000])
except Exception:
    print('Import or runtime error while importing app:')
    traceback.print_exc()
