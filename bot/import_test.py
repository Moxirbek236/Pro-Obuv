import sys
import traceback

try:
    import telegram
    print('telegram version:', getattr(telegram, '__version__', 'unknown'))
    from telegram.ext import Updater
    print('Updater imported OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)
