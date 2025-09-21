import importlib.util
import sys
import os

APP = r'c:\Users\Moxir_Coder\OneDrive\Desktop\retourant\app.py'
# Avoid heavy app initialization during import
os.environ.setdefault('SKIP_DB_INIT', '1')

spec = importlib.util.spec_from_file_location('app_mod', APP)
mod = importlib.util.module_from_spec(spec)
sys.modules['app_mod'] = mod
spec.loader.exec_module(mod)

print('app.config["YANDEX_MAPS_API"] =', repr(mod.app.config.get('YANDEX_MAPS_API')))
print('env YANDEX_MAPS_API =', repr(os.environ.get('YANDEX_MAPS_API')))
