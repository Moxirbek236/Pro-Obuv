from app import app

# Test all main pages including subpages
test_pages = {
    '/': 'home',
    '/menu': 'menu',
    '/contact': 'contact', 
    '/register': 'register',
    '/super-admin-master-login-z9x4m': 'super_admin_login',
}

c = app.test_client()

print("="*70)
print("TESTING ALL PAGES FOR <main> ELEMENT")
print("="*70)
print()

working = []
broken = []

for page, name in test_pages.items():
    try:
        r = c.get(page, follow_redirects=True)
        content = r.get_data(as_text=True)
        has_main = '<main' in content
        status = r.status_code
        
        if status == 200 and has_main:
            working.append((page, name))
            print(f"✓ {name:30s} - Status {status} | Has <main>: YES")
        else:
            broken.append((page, name, status, has_main))
            emoji = '⚠' if status in (302, 301) else '✗'
            print(f"{emoji} {name:30s} - Status {status} | Has <main>: {has_main}")
    except Exception as e:
        broken.append((page, name, 'ERROR', str(e)))
        print(f"✗ {name:30s} - ERROR: {str(e)[:40]}")

print()
print("="*70)
print(f"SUMMARY: {len(working)} working, {len(broken)} issues")
print("="*70)

if working:
    print("\n✓ WORKING PAGES:")
    for page, name in working:
        print(f"  - {name}")

if broken:
    print("\n⚠ PAGES WITH ISSUES:")
    for item in broken:
        if len(item) == 4:
            page, name, status, has_main = item
            print(f"  - {name:30s} (Status: {status}, Has <main>: {has_main})")
        else:
            page, name, status, err = item
            print(f"  - {name:30s} (Error: {err})")
