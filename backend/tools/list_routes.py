import os
import sys
from pathlib import Path

# Ensure the repository root (parent of tools/) is on sys.path so `import app` works
root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

try:
    from app import app
    from flask import url_for

    with app.test_request_context():
        routes = sorted(app.url_map.iter_rules(), key=lambda x: x.rule)
        for r in routes:
            print(r.endpoint, r.rule)
        try:
            print('\nproduct_detail url:', url_for('product_detail', item_id=1))
        except Exception as e:
            print('\ncould not build product_detail url:', e)
except Exception as e:
    print('failed to import app or list routes:', e)
