import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, execute_query
from flask import render_template

item_id = 40
with app.test_request_context(f'/product/{item_id}'):
    row = execute_query('SELECT * FROM menu_items WHERE id=?', (item_id,), fetch_one=True)
    if not row:
        print('NO ROW for id', item_id)
    else:
        item = dict(row) if hasattr(row, 'keys') else row
        s = render_template('product.html', item=item, media=[], comments=[], marketplaces={}, current_page='product')
        print('LEN', len(s))
        i = s.find('<h1>')
        if i!=-1:
            print('H1_SNIP:', s[i:i+200])
        else:
            print('H1 not found')
        j = s.find('<meta name="description"')
        if j!=-1:
            print('META_SNIP:', s[j:j+200])
        else:
            print('META not found')
