import importlib.util
import sys
spec = importlib.util.spec_from_file_location('app_mod', r'c:\Users\Moxir_Coder\OneDrive\Desktop\v3\retourant\app.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('app.config["YANDEX_MAPS_API"] =', repr(mod.app.config.get('YANDEX_MAPS_API')))
print('env YANDEX_MAPS_API =', repr(__import__('os').environ.get('YANDEX_MAPS_API')))
