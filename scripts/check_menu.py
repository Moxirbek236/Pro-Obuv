import os
# Prevent app from initializing DB or starting background services during import
os.environ['SKIP_DB_INIT'] = '1'

import importlib.util
import sys
from pprint import pprint
import traceback

spec = importlib.util.spec_from_file_location('app', r'c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\app.py')
appmod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(appmod)
except Exception:
    print('Import-time exception when loading app module:')
    traceback.print_exc()
    print('\nPYTHONPATH:', sys.path)
    raise

try:
    app = getattr(appmod, 'app')
except Exception:
    print('Could not get "app" attribute from module:')
    traceback.print_exc()
    raise

with app.test_client() as c:
    try:
        resp = c.get('/menu')
        print('STATUS:', resp.status_code)
        data = resp.get_data(as_text=True)
        print('LENGTH:', len(data))
        print('SNIPPET:\n', data[:2000])
        print('\n--- END SNIPPET ---\n')
    except Exception as e:
        print('Request caused exception:')
        traceback.print_exc()
        # Try to dump app.logger handlers info
        try:
            print('\nApp logger handlers:', getattr(app, 'logger').handlers)
        except Exception:
            pass
