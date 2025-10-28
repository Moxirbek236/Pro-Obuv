import sys
import time
import os

email = "moxirbekmoxirbek29@gmail.com"
new_password = "TestNewPass123!"

print("Starting forgot-flow test for:", email)

# Ensure project root is on sys.path so we can import app
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

try:
    # Import app and helpers
    from app import app, check_password_hash, execute_query
except Exception as e:
    print("Failed to import app:", e)
    sys.exit(2)

with app.test_client() as client:
    # 1) Request code via email
    resp = client.post('/forgot', data={'method': 'email', 'email': email}, follow_redirects=True)
    print('\nPOST /forgot ->', resp.status_code)
    print('Response snippet:', resp.get_data(as_text=True)[:400])

    # Inspect session cookie for code
    with client.session_transaction() as sess:
        code = sess.get('forgot_code')
        user_id = sess.get('forgot_user_id')
        expires = sess.get('forgot_expires')
        method = sess.get('forgot_method')
        verified = sess.get('forgot_verified')

    print('\nSession values:')
    print('  code=', code)
    print('  user_id=', user_id)
    print('  expires=', expires, '(now=', time.time(), ')')
    print('  method=', method)
    print('  verified=', verified)

    if not code:
        print('\nNo code was generated - aborting test')
        sys.exit(1)

    # 2) Verify code
    resp2 = client.post('/forgot', data={'action': 'verify', 'code': code}, follow_redirects=True)
    print('\nPOST /forgot (verify) ->', resp2.status_code)
    print('Response snippet:', resp2.get_data(as_text=True)[:400])

    with client.session_transaction() as sess:
        verified = sess.get('forgot_verified')
    print('Verified flag after verify:', verified)

    if not verified:
        print('\nVerification failed - cannot continue to reset')
        sys.exit(1)

    # 3) Reset password
    resp3 = client.post('/forgot', data={'action': 'reset', 'password': new_password, 'password_confirm': new_password}, follow_redirects=True)
    print('\nPOST /forgot (reset) ->', resp3.status_code)
    print('Response snippet:', resp3.get_data(as_text=True)[:400])

    # 4) Confirm in DB
    user_row = execute_query('SELECT id, password_hash, email FROM users WHERE email = ?', (email,), fetch_one=True)
    if user_row:
        try:
            ph = user_row[1]
        except Exception:
            ph = None
        ok = False
        if ph:
            try:
                ok = check_password_hash(ph, new_password)
            except Exception:
                ok = False
        print('\nDB check: password hash present?', bool(ph))
        print('Password verification OK?', ok)
        if ok:
            print('Success: the user password was updated.')
        else:
            print('Either password was not updated or hashing mismatch.')
    else:
        print('\nUser with that email not found in DB. The flow generated a code but could not reset because there was no account to update.')

print('\nTest finished')
