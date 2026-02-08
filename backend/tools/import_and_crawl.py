# Script to import the Flask app and crawl non-parameter GET routes using test_client
# Run: python tools\import_and_crawl.py
import sys, traceback, importlib, os
importlib.invalidate_caches()
errors = []

# Try normal import first (may resolve to package), then fall back to loading app.py by path
flask_app = None
try:
    import app as imported_app
    flask_app = getattr(imported_app, 'app', None)
except Exception:
    # Fallback: attempt to load the top-level app.py file directly
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        candidate = os.path.join(repo_root, 'app.py')
        if os.path.exists(candidate):
            spec = spec_from_file_location('main_app', candidate)
            mod = module_from_spec(spec)
            spec.loader.exec_module(mod)
            flask_app = getattr(mod, 'app', None)
        else:
            raise FileNotFoundError(candidate)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
if flask_app is None:
    print('FLASK_APP_NOT_FOUND')
    sys.exit(1)

print('FOUND_APP')

print('ROUTES:')
for rule in sorted(flask_app.url_map.iter_rules(), key=lambda r: r.rule):
    print(rule.rule, sorted(list(rule.methods)))

client = flask_app.test_client()
for rule in sorted(flask_app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'GET' not in rule.methods:
        continue
    if '<' in rule.rule:
        continue
    if rule.rule.startswith('/static'):
        continue
    try:
        resp = client.get(rule.rule)
        status = resp.status_code
        if status >= 500:
            print('\nERROR', rule.rule, status)
            body = resp.get_data(as_text=True)
            print(body[:4000])
            errors.append((rule.rule, status, body[:4000]))
        else:
            print('OK', rule.rule, status)
    except Exception:
        tb = traceback.format_exc()
        print('\nEXC', rule.rule)
        print(tb)
        errors.append((rule.rule, 'exception', tb))

print('\nDONE ERRORS:', len(errors))
if errors:
    sys.exit(2)
else:
    sys.exit(0)
