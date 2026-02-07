import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import utils
for lang in ('uz','ru','en','kz'):
    print('\nLANG=',lang)
    print('nav.home =>', utils.get_text('nav.home', lang))
    print('nav.brand =>', utils.get_text('nav.brand', lang))
    print('footer.cat_specobuv =>', utils.get_text('footer.cat_specobuv', lang))
    print('messages.loading =>', utils.get_text('messages.loading', lang))
    # Test a non-nested key
    print('home_title =>', utils.get_text('home_title', lang))
    # Test nonexistent
    print('nonexistent =>', utils.get_text('no.such.key', lang))
