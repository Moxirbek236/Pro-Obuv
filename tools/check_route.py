from app import app
from flask import url_for
with app.test_request_context():
    print(url_for('product_detail', item_id=1))
