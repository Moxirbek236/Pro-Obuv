#!/usr/bin/env python3
"""Simple Swagger API tester.

Usage: python tools/swagger_tester.py --base http://localhost:5000

This script loads swagger.yaml, iterates documented paths and methods,
and makes simple requests to the local server to record status codes
and responses. It is intentionally lightweight and tolerant of missing
dependencies (prints guidance if PyYAML or requests are unavailable).
"""
import os
import sys
import json
import argparse
import time

try:
    import yaml
except Exception:
    yaml = None

try:
    import requests
except Exception:
    requests = None


def load_spec(path):
    if yaml:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    # minimal fallback: try to parse as JSON (unlikely) or fail
    raise RuntimeError('PyYAML required: pip install pyyaml')


def sample_body_for_schema(name):
    # Provide a few helpful sample payloads for common schemas
    name = (name or '').lower()
    if 'authlogin' in name or 'login' in name:
        return {'email': 'demo@demo', 'password': 'demo'}
    if 'authregister' in name or 'register' in name:
        return {'email': 'new@demo', 'password': 'demo'}
    if 'order' in name and 'item' not in name:
        return {'items': [{'product_id': 1, 'quantity': 1}], 'customer_name': 'Test'}
    if 'cart' in name:
        return {'product_id': 1, 'quantity': 1}
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', default='swagger.yaml')
    parser.add_argument('--base', default='http://localhost:5000')
    parser.add_argument('--out', default='tools/swagger_test_report.json')
    parser.add_argument('--timeout', type=float, default=3.0)
    args = parser.parse_args()

    if requests is None:
        print('requests package required: pip install requests')
        sys.exit(2)
    if yaml is None:
        print('pyyaml package required: pip install pyyaml')
        sys.exit(2)

    spec_path = args.spec
    if not os.path.exists(spec_path):
        print('Spec not found at', spec_path)
        sys.exit(2)

    spec = load_spec(spec_path)
    paths = spec.get('paths', {}) if isinstance(spec, dict) else {}

    results = []
    # Create a requests.Session to preserve cookies for auth-aware tests
    sess = requests.Session()
    authed = False

    # Try a quick login/register to obtain cookies for protected endpoints
    # Prefer login, fall back to register if login returns 401.
    auth_login_url = args.base.rstrip('/') + '/api/auth/login'
    auth_register_url = args.base.rstrip('/') + '/api/auth/register'
    try:
        r = sess.post(auth_login_url, json={'email': 'demo@demo', 'password': 'demo'}, timeout=args.timeout)
        if r.status_code == 200:
            authed = True
            print('[+] Authenticated with /api/auth/login')
        else:
            # Try register
            r2 = sess.post(auth_register_url, json={'email': 'new@demo', 'password': 'demo'}, timeout=args.timeout)
            if r2.status_code in (200, 201):
                authed = True
                print('[+] Registered and authenticated via /api/auth/register')
    except Exception:
        pass
    for p, methods in paths.items():
        for m, details in (methods.items() if isinstance(methods, dict) else []):
            method = m.upper()
            url = args.base.rstrip('/') + p
            # Replace path params with sample values
            url = url.replace('{', '<').replace('}', '>')
            # naive replace of {id} with 1
            import re
            url = re.sub(r"\{[^}]+\}", '1', url)

            payload = None
            headers = {'Accept': 'application/json'}
            # Try to derive a sample body from requestBody/schema
            rb = details.get('requestBody') if isinstance(details, dict) else None
            if rb:
                # Basic heuristics: look for application/json schema $ref name
                content = rb.get('content', {})
                app_json = content.get('application/json') or {}
                schema = app_json.get('schema') or {}
                ref = schema.get('$ref') or schema.get('items', {}).get('$ref')
                if ref and isinstance(ref, str):
                    # ref like '#/components/schemas/AuthLoginRequest'
                    name = ref.split('/')[-1]
                    payload = sample_body_for_schema(name)
                else:
                    payload = {}

            print(f'[*] {method} {url} -> payload: {bool(payload)}')
            try:
                resp = None
                if method == 'GET':
                    if authed:
                        resp = sess.get(url, headers=headers, timeout=args.timeout)
                    else:
                        resp = requests.get(url, headers=headers, timeout=args.timeout)
                elif method in ('POST', 'PUT', 'DELETE'):
                    headers['Content-Type'] = 'application/json'
                    body = payload or {}
                    if method == 'POST':
                        if authed:
                            resp = sess.post(url, headers=headers, json=body, timeout=args.timeout)
                        else:
                            resp = requests.post(url, headers=headers, json=body, timeout=args.timeout)
                    elif method == 'PUT':
                        if authed:
                            resp = sess.put(url, headers=headers, json=body, timeout=args.timeout)
                        else:
                            resp = requests.put(url, headers=headers, json=body, timeout=args.timeout)
                    else:
                        # DELETE with body is less common; try without body first
                        try:
                            if authed:
                                resp = sess.delete(url, headers=headers, timeout=args.timeout)
                            else:
                                resp = requests.delete(url, headers=headers, timeout=args.timeout)
                        except Exception:
                            if authed:
                                resp = sess.delete(url, headers=headers, json=body, timeout=args.timeout)
                            else:
                                resp = requests.delete(url, headers=headers, json=body, timeout=args.timeout)
                else:
                    # unsupported method for tester
                    results.append({'path': p, 'method': method, 'error': 'unsupported_method'})
                    continue

                entry = {'path': p, 'method': method, 'url': url, 'status_code': resp.status_code}
                try:
                    entry['json'] = resp.json()
                except Exception:
                    entry['text'] = resp.text[:1000]
                results.append(entry)
            except Exception as e:
                results.append({'path': p, 'method': method, 'error': str(e)})
            # be nice to the server
            time.sleep(0.05)

    # Write report
    outp = args.out
    try:
        os.makedirs(os.path.dirname(outp), exist_ok=True)
    except Exception:
        pass
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Summary
    ok = sum(1 for r in results if r.get('status_code') and 200 <= r['status_code'] < 400)
    total = len(results)
    print(f'Completed {total} requests — {ok} succeeded (2xx/3xx). Report: {outp}')


if __name__ == '__main__':
    main()
