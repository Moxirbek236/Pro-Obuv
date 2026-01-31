from app import app

c = app.test_client()
r = c.get('/super-admin-master-login-z9x4m')
print(f'Status: {r.status_code}')
d = r.get_data(as_text=True)
has_main = '<main' in d
has_form = 'login-form' in d

print(f'Has <main>: {has_main}')
print(f'Has login-form: {has_form}')
print(f'Content length: {len(d)} bytes')

if has_main and has_form:
    print()
    print('✓✓✓ SUCCESS! ✓✓✓')
    print('The super admin login page is now loading correctly!')
    print('The page contains both the <main> element and login form.')
else:
    print('✗ Some elements are missing')
