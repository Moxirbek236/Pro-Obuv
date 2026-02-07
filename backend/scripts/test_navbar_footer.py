from app import app

pages = [
    ('/', 'home'),
    ('/menu', 'menu'),
    ('/contact', 'contact'),
    ('/register', 'register'),
    ('/super-admin-master-login-z9x4m', 'super_admin_login'),
]

c = app.test_client()

print("======================================================================")
print("CHECKING PAGES FOR <main>, NAVBAR, AND FOOTER")
print("======================================================================\n")

for url, name in pages:
    try:
        r = c.get(url, follow_redirects=True)
        content = r.get_data(as_text=True)
        
        has_main = '<main' in content
        has_navbar = 'navbar' in content.lower() or 'PRO<span' in content
        has_footer = 'footer' in content.lower() or '©' in content
        
        status_ok = "✓" if has_main else "✗"
        navbar_ok = "✓" if has_navbar else "✗"
        footer_ok = "✓" if has_footer else "✗"
        
        print(f"{status_ok} {name:25s} | Main: {has_main:5} | Navbar: {has_navbar:5} | Footer: {has_footer:5}")
        
    except Exception as e:
        print(f"✗ {name:25s} | Error: {str(e)[:50]}")

print("\n" + "="*70)
print("All pages should have <main> element, navbar, and footer!")
print("="*70)
