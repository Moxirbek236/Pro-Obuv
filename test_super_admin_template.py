from app import app
from flask import render_template

with app.test_request_context('/super-admin-master-login-z9x4m'):
    try:
        result = render_template('super_admin_login.html')
        print("✓ Template rendered successfully")
        print(f"  - Has <main>: {('<main' in result)}")
        print(f"  - Has login-form: {('login-form' in result)}")
        print(f"  - Content length: {len(result)} chars")
        print(f"\nFirst 1000 chars:\n{result[:1000]}")
    except Exception as e:
        print(f"✗ Error rendering: {e}")
        import traceback
        traceback.print_exc()
