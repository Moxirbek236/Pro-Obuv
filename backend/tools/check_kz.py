import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import app
from flask import render_template_string, session

with app.test_request_context('/'):
    for lang in ('uz','ru','en','kz'):
        session['interface_language'] = lang
        t = "{{ _('menu.all_products') }}"
        t2 = "{{ get_text('menu.all_products') }}"
        try:
            print(lang, '->_', render_template_string(t))
        except Exception as e:
            print(lang, '->_ error', e)
        try:
            print(lang, '->get_text', render_template_string(t2))
        except Exception as e:
            print(lang, '->get_text error', e)
    
