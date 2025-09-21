import importlib.util, traceback, os

# Absolute path to app.py in the workspace
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.py'))

spec = importlib.util.spec_from_file_location('app_module', APP_PATH)
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    # Call init_db to (re)create schema
    if hasattr(m, 'init_db'):
        m.init_db()
        print('init_db done')
    else:
        print('init_db not found in app.py')
except Exception:
    traceback.print_exc()
