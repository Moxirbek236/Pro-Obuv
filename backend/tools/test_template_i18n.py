import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import app
from flask import render_template_string, session

with app.test_request_context('/'):
    session['interface_language'] = 'uz'
    t = "{{ _('footer.company_desc') }}"
    print('jinja _ global:', app.jinja_env.globals.get('_'))
    # call the global directly
    fn = app.jinja_env.globals.get('_')
    try:
        print('direct call result:', fn('footer.company_desc'))
    except Exception as e:
        print('direct call error:', e)
    print('rendered:', render_template_string(t))
    # Render by calling the global function via `app` to observe template-time result
    t3 = "{{ app.jinja_env.globals['_']('footer.company_desc') }}"
    print('rendered via app.globals call:', render_template_string(t3))
    # Try calling via globals() to bypass any Jinja wrapper
    t2 = "{{ globals()['_']('footer.company_desc') }}"
    print('rendered via globals:', render_template_string(t2))
    session['interface_language'] = 'ru'
    print('rendered RU:', render_template_string(t))
    session['interface_language'] = 'en'
    print('rendered EN:', render_template_string(t))
