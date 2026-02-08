import sys, os, traceback
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import app

env = app.jinja_env
errors = []
for name in env.list_templates():
    try:
        env.get_template(name)
        print('OK:', name)
    except Exception as e:
        print('ERROR:', name)
        traceback.print_exc()
        errors.append((name, e))

print('\nSummary: templates with errors:', len(errors))
if errors:
    for n,e in errors:
        print('-', n, type(e).__name__, str(e)[:200])
    sys.exit(1)
else:
    sys.exit(0)
