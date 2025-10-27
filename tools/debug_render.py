import sys
import os
# Ensure project root is on sys.path when running scripts from tools/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from flask import render_template_string

with app.test_request_context('/menu'):
    out1 = render_template_string('{{ _(\"menu.all_products\") }}')
    out1_override = render_template_string('{{ _(\"menu.all_products\") }}', **{"_": lambda k: 'OV:' + __import__('utils').translate(k)})
    out2 = render_template_string("{{ get_text('menu.all_products') }}")
    print('RENDERED _ (default):', out1)
    print('RENDERED _ (override ctx):', out1_override)
    print('RENDERED get_text:', out2)
    # Also show type of '_' in template globals
    env = app.jinja_env
    print('jinja global _ is', type(env.globals.get('_')))
    print('callable?:', callable(env.globals.get('_')))
    # Try calling the global directly
    try:
        print('direct call:', env.globals.get('_')('menu.all_products'))
    except Exception as e:
        print('direct call raised:', type(e), e)
