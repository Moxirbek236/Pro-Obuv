"""
Route audit script: enumerates Flask routes and makes test requests as different roles.
Generates a JSON-like report printed to stdout summarizing status codes and exceptions.

Run with: SKIP_DB_INIT=1 python tools/route_audit.py
"""
import os
import sys
import re
import traceback
from collections import defaultdict

project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('SKIP_DB_INIT', '1')

try:
    import app
    from app import app as flask_app
except Exception as e:
    print('IMPORT_ERROR', e)
    traceback.print_exc()
    sys.exit(2)

# Helper to normalize rule to concrete path by replacing <...> with sample values
def rule_to_url(rule):
    url = rule
    # Replace converters and variable names like <int:id> or <name> with '1' or 'test'
    url = re.sub(r"<[^>:]+:([^>]+)>", r"1", url)
    url = re.sub(r"<([^>]+)>", r"1", url)
    return url

roles = {
    'anonymous': {},
    'super_admin': {'super_admin': True},
    'staff': {'staff_id': 1},
    'courier': {'courier_id': 1},
    'user': {'user_id': 1}
}

report = []

with flask_app.test_client() as c:
    rules = sorted(flask_app.url_map.iter_rules(), key=lambda r: r.rule)
    for rule in rules:
        # skip static and internal endpoints
        if rule.endpoint.startswith('static'):
            continue
        if rule.rule.startswith('/_debug') or rule.rule.startswith('/favicon'):
            continue

        url = rule_to_url(rule.rule)
        methods = set(rule.methods or [])
        methods = [m for m in methods if m in ('GET', 'POST')]
        if not methods:
            methods = ['GET']

        for role_name, sess_vals in roles.items():
            # set session for role
            try:
                with c.session_transaction() as sess:
                    sess.clear()
                    for k, v in sess_vals.items():
                        sess[k] = v
            except Exception:
                pass

            # ensure CSRF token exists for this session (do a GET /settings if available)
            try:
                c.get('/settings')
            except Exception:
                pass

            for method in methods:
                entry = {
                    'rule': rule.rule,
                    'endpoint': rule.endpoint,
                    'method': method,
                    'role': role_name,
                    'url': url,
                    'status': None,
                    'error': None,
                    'snippet': None,
                }

                try:
                    if method == 'GET':
                        resp = c.get(url)
                    else:
                        # POST: attempt JSON empty body, include CSRF header if available in session
                        csrf = None
                        try:
                            with c.session_transaction() as sess:
                                csrf = sess.get('csrf_token')
                        except Exception:
                            csrf = None
                        headers = {}
                        if csrf:
                            headers['X-CSRF-Token'] = csrf
                        resp = c.post(url, json={}, headers=headers)

                    entry['status'] = getattr(resp, 'status_code', None)
                    data = None
                    try:
                        data = resp.get_data(as_text=True)
                    except Exception:
                        data = str(resp)
                    entry['snippet'] = (data or '')[:800]

                    # mark errors (500s) and invalid CSRF
                    if entry['status'] and entry['status'] >= 500:
                        entry['error'] = 'HTTP_5xx'

                    # capture JSON error responses
                    if data and data.strip().startswith('{') and 'error' in data.lower():
                        entry['error'] = entry['error'] or 'API_ERROR'

                except Exception as e:
                    entry['error'] = 'EXCEPTION'
                    entry['snippet'] = traceback.format_exc()[:2000]

                report.append(entry)

# Summarize
errors = [r for r in report if r['error']]
print('TOTAL_ENDPOINTS_TESTED:', len(report))
print('TOTAL_ERRORS_FOUND:', len(errors))

# Print a compact error list
for e in errors:
    print('---')
    print(f"{e['method']} {e['url']} (endpoint={e['endpoint']}) role={e['role']} status={e['status']}")
    print('error:', e['error'])
    print('snippet:', e['snippet'][:400].replace('\n','\\n'))

# Optionally dump everything to a file
try:
    import json
    with open('tools/route_audit_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('WROTE tools/route_audit_report.json')
except Exception as ex:
    print('FAILED_WRITE_REPORT', ex)
