import sys, os, traceback
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app import app

with app.test_client() as c:
    try:
        resp = c.get('/menu')
        print('STATUS:', resp.status_code)
        if resp.status_code == 200:
            print('LEN', len(resp.get_data(as_text=True)))
            i = resp.get_data(as_text=True).find('<main')
            if i!=-1:
                print('SNIP:', resp.get_data(as_text=True)[i:i+400])
        else:
            print(resp.get_data(as_text=True)[:1000])
    except Exception:
        print('ERROR during request:')
        traceback.print_exc()
