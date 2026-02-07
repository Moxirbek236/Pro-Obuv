import os
import sys
import importlib.util

# Load app.py directly to avoid package name shadowing with the app/ package
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.py'))
spec = importlib.util.spec_from_file_location('app_main', APP_PATH)
app_mod = importlib.util.module_from_spec(spec)
sys.modules['app_main'] = app_mod
# Prevent heavy initialization (DB init, background threads, servers) when importing app.py
os.environ.setdefault('SKIP_DB_INIT', '1')
spec.loader.exec_module(app_mod)

execute_query = app_mod.execute_query
get_db = app_mod.get_db
get_cart_items = app_mod.get_cart_items

print('DB path:', os.path.abspath('database.sqlite3'))
print('DB exists:', os.path.exists('database.sqlite3'))

res = execute_query('SELECT name FROM sqlite_master WHERE type="table" AND name="cart_items";', fetch_one=True)
print('cart_items table row:', res)

conn = get_db()
try:
    items = get_cart_items(conn, 'doesnotexist', None)
    print('get_cart_items(empty session):', items)
finally:
    try:
        conn.close()
    except:
        pass

print('sanity check done')
