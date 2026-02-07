from app import app
from flask import render_template

with app.test_request_context('/super-admin-master-login-z9x4m'):
    # Manually call the context processors to see what context is provided
    from flask import g
    
    # Initialize context processors
    context = {}
    for func in app.template_context_processors[None]:
        context.update(func())
    
    print("Context variables for super_admin_login:")
    for key in sorted(context.keys()):
        value = context[key]
        if isinstance(value, dict):
            print(f"  {key}: dict with {len(value)} keys")
        elif isinstance(value, bool):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {type(value).__name__}")
    
    print("\nKey flags:")
    print(f"  is_user: {context.get('is_user')}")
    print(f"  is_staff: {context.get('is_staff')}")
    print(f"  is_courier: {context.get('is_courier')}")
    print(f"  is_super_admin: {context.get('is_super_admin')}")
    print(f"  show_nav: {context.get('show_nav')}")
