# Simple test script to fetch CSRF token from /settings and POST updated settings
import re
import json
import sys
import os

# Ensure the repository root (parent of tools/) is on sys.path so we can import app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import app
    from app import app as flask_app
except Exception as e:
    print('IMPORT_ERROR', e)
    sys.exit(1)

c = flask_app.test_client()

# Mark the test client as logged in (super_admin) so /settings is accessible
with c.session_transaction() as sess:
    sess['super_admin'] = True


r = c.get('/settings')
html = r.get_data(as_text=True)

m = re.search(r"CSRF_TOKEN\s*=\s*'([^']*)'", html)
if not m:
    print('NO_CSRF_TOKEN_FOUND')
    print('PAGE_SNIPPET:\n', html[:800])
    sys.exit(2)

token = m.group(1)
print('CSRF_TOKEN|' + token)

payload = {'language': 'ru', 'theme': 'dark', 'font_size': 'large'}
headers = {'X-CSRF-Token': token}

resp = c.post('/settings', json=payload, headers=headers)
print('STATUS|', resp.status_code)
print('RESPONSE_SNIPPET|', resp.get_data(as_text=True)[:1000])

# Also try without token to ensure it fails
resp2 = c.post('/settings', json=payload)

print('STATUS_NO_TOKEN|', resp2.status_code)
print('RESPONSE_NO_TOKEN|', resp2.get_data(as_text=True)[:200])
