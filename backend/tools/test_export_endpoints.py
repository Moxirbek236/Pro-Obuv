# Quick test for export endpoints using Flask test client
import os
import sys
# Ensure project root is on sys.path so `import app` works when running from tools/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ['SKIP_DB_INIT'] = '1'
import app
from app import app as flask_app

client = flask_app.test_client()

# Make session super_admin for endpoints that require it
with client.session_transaction() as sess:
    sess['super_admin'] = True

# Test export-report (POST) with minimal JSON
resp = client.post('/api/super-admin/export-report', json={'summary': {'total_orders': 1}, 'sales': [{'date': '2025-09-07', 'orders_count': 1, 'revenue': 1000}]})
print('export-report', resp.status_code, resp.content_type)
print(resp.data[:200])

# Test export-staff (GET)
resp2 = client.get('/api/super-admin/export-staff')
print('export-staff', resp2.status_code, resp2.content_type)
print(resp2.data[:200])

# Test export-couriers (GET)
resp3 = client.get('/api/super-admin/export-couriers')
print('export-couriers', resp3.status_code, resp3.content_type)
print(resp3.data[:200])
