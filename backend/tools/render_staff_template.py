from flask import Flask, session
import os
import sqlite3
from jinja2 import Environment, FileSystemLoader, select_autoescape
from urllib.parse import quote_plus


def fake_url_for(endpoint, **kwargs):
	# Minimal url_for replacement for offline template rendering
	if endpoint == 'static':
		return '/static/' + kwargs.get('filename', '')
	return f'/{endpoint}'


def fake_get_flashed_messages(with_categories=False):
	return []


class FakeRequest:
	path = '/' 
	args = {}

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.sqlite3')

# Load orders sample
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, ticket_no, customer_name, status, created_at, eta_time FROM orders ORDER BY created_at DESC LIMIT 20")
rows = cur.fetchall()
orders = [dict(row) for row in rows]
conn.close()

# Setup Jinja env
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(['html','xml']))
# Provide minimal globals expected by templates
env.globals['url_for'] = fake_url_for
env.globals['session'] = {'staff_name': 'Test Staff'}
env.globals['config'] = {}
env.globals['get_flashed_messages'] = fake_get_flashed_messages
env.globals['request'] = FakeRequest()

tpl = env.get_template('staff_dashboard.html')

# Render with minimal context
rendered = tpl.render(orders=orders, session={'staff_name':'Test Staff'})
print('Rendered length:', len(rendered))
