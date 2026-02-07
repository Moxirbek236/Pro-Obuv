import requests
try:
    r = requests.get('http://127.0.0.1:5000/sitemap.xml', timeout=2)
    print('status', r.status_code)
    print(r.text[:200])
except Exception as e:
    print('fetch failed (server likely not running):', e)
