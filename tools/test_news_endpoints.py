# Small test that imports the Flask app and calls the /api/news and /api/news/admin endpoints
import json
from pathlib import Path
import traceback
workspace_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(workspace_root))

try:
    from app import app
except Exception:
    traceback.print_exc()
    raise

with app.test_client() as c:
    r = c.get('/api/news')
    print('/api/news status:', r.status_code)
    try:
        print(r.get_json())
    except Exception:
        print('non-json response:', r.data[:200])

    # Try admin endpoint - need to simulate super_admin session; set cookie or session directly
    # We'll bypass auth by setting session via test_request_context
    with app.test_request_context():
        from flask import session
        session['super_admin'] = True
        # Use the test client to access the admin endpoint
        r2 = c.get('/api/news/admin')
        print('/api/news/admin status:', r2.status_code)
        try:
            print(r2.get_json())
        except Exception:
            print('non-json response:', r2.data[:200])
