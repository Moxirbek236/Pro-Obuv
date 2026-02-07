import os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import app

paths = ['/', '/news/2', '/menu', '/product/1']
with app.test_client() as c:
    for p in paths:
        try:
            r = c.get(p)
            body = r.get_data(as_text=True)
            keys = set(re.findall(r"[a-z_]+\.[a-z0-9_\.]+", body))
            print('\nPATH:', p, 'status', r.status_code)
            for k in sorted(keys):
                print('  key-like:', k)
        except Exception as e:
            print('error for', p, e)
