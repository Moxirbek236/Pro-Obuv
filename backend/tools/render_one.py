import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import app, execute_query
from flask import render_template

if len(sys.argv) > 1:
    item_id = int(sys.argv[1])
else:
    item_id = 41

with app.test_request_context(f'/product/{item_id}'):
    row = execute_query('SELECT * FROM menu_items WHERE id=?', (item_id,), fetch_one=True)
    print('ROW FOUND:', bool(row))
    if not row:
        sys.exit(0)
    item = dict(row) if hasattr(row, 'keys') else row
    try:
        s = render_template('product.html', item=item, media=[], comments=[], marketplaces={}, current_page='product')
        print('RENDER LEN', len(s))
    except Exception as e:
        import traceback
        print('ERROR during render:')
        traceback.print_exc()
        sys.exit(1)
