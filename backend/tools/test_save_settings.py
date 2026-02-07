# Minimal test using Flask test client to POST settings JSON and check response
import os, sys, json
sys.path.insert(0, r'c:\Users\Moxir_Coder\OneDrive\Desktop\v3\retourant')
os.environ['SKIP_DB_INIT'] = '1'
from app import app

with app.test_client() as client:
    # Ensure session cookie created by performing a GET to /settings (requires login normally) - bypass by setting session using client.session_transaction
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'

    # First GET /settings so server generates and stores CSRF token in session
    get_resp = client.get('/settings')
    print('GET /settings status', get_resp.status_code)

    with client.session_transaction() as sess:
        token = sess.get('csrf_token')
        print('session csrf_token (from server):', token)

    payload = {
        'theme': 'dark',
        'font_size': 'large',
        'language': 'ru',
        'csrf_token': token
    }

    resp = client.post('/settings', json=payload, headers={'X-Requested-With': 'XMLHttpRequest', 'X-CSRF-Token': token})
    print('STATUS:', resp.status_code)
    try:
        data = resp.get_json()
    except Exception as e:
        data = None
    print('JSON:', data)

    # Fetch session after request
    with client.session_transaction() as sess:
        print('session dark_theme:', sess.get('dark_theme'))
        print('session font_size:', sess.get('font_size'))
        print('session interface_language:', sess.get('interface_language'))
