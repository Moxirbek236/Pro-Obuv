from app import app

# Test which pages have the main element issue
test_pages = [
    '/',
    '/login',
    '/register',
    '/menu',
    '/contact',
    '/profile',
    '/super-admin-master-login-z9x4m',
]

c = app.test_client()

print("Testing pages for <main> element:\n")
for page in test_pages:
    try:
        r = c.get(page, follow_redirects=False)
        content = r.get_data(as_text=True)
        has_main = '<main' in content
        status = r.status_code
        
        status_emoji = '✓' if status == 200 else '⚠'
        main_emoji = '✓' if has_main else '✗'
        
        print(f"{status_emoji} {status:3d} | {main_emoji} {page:40s} | <main: {has_main}")
    except Exception as e:
        print(f"✗ ERROR | {page:40s} | {str(e)[:40]}")

print("\nPages without <main> element need to use simple_base.html instead of base.html")
