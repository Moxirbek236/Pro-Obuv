"""Simple Telegram bot integration using python-telegram-bot.
This script listens for commands and forwards them to the Flask app via HTTP
or writes to the database directly. It's a minimal scaffold — configure
TELEGRAM_BOT_TOKEN and the app URL or run it locally with a webhook or polling.
"""
import os
import logging
import requests
from datetime import datetime
import traceback
from pathlib import Path
import atexit
import time

try:
    from telegram import Update, Bot, InputMediaPhoto
    # v20+ imports
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    # CallbackQueryHandler removed - no callback buttons needed anymore
    )
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    # keep marker for old-style check
    Updater = True
    IMPORT_ERROR = None
except Exception:
    # If library not installed or wrong version, capture the exception so we can log a helpful hint at runtime.
    IMPORT_ERROR = None
    try:
        raise
    except Exception as e:
        IMPORT_ERROR = e
    Updater = None

LOG = logging.getLogger('telegram_bot')

# Ensure logs directory exists and define action/error log paths
LOGS_DIR = Path(__file__).resolve().parents[1] / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_LOG = LOGS_DIR / 'telegram_actions.txt'
ERROR_LOG = LOGS_DIR / 'telegram_errors.txt'


def _now_iso():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def log_action(action: str, user: str = None, detail: str = ''):
    try:
        line = f"{_now_iso()} | ACTION | {action}"
        if user:
            line += f" | user:{user}"
        if detail:
            line += f" | {detail}"
        line += "\n"
        with open(ACTION_LOG, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        LOG.exception('Failed to write action log')


def log_error(err: Exception, context: str = ''):
    try:
        tb = traceback.format_exc()
        line = f"{_now_iso()} | ERROR | {context}\n{tb}\n"
        with open(ERROR_LOG, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        LOG.exception('Failed to write error log')

# Prefer environment variable, but fallback to the token you provided so the
# bot can run without setting env when testing locally. For production, set
# TELEGRAM_BOT_TOKEN in environment and remove the hardcoded fallback.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8443912951:AAF-1gKuqQv0b0BQw_KOPCS85gYZk-n10V4')

# FLASK_APP_URL should be set in environment; default to safety.uz if missing.
FLASK_APP_URL = os.environ.get('FLASK_APP_URL', 'https://safety.uz')  # e.g., https://example.com


async def start(update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
    try:
        await update.message.reply_text("Assalomu alaykum! Mahsulotlar va buyurtma uchun /products buyrug'ini bosing.")
        uid = getattr(update.message.from_user, 'id', None)
        log_action('start_command', user=f'tg:{uid}', detail='start command sent')
    except Exception as e:
        log_error(e, 'start handler')
        raise


async def products_cmd(update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
    # Fetch a small list of products (for demo use menu API)
    try:
        url = FLASK_APP_URL.rstrip('/') + '/api/menu-search?limit=10'
        r = requests.get(url, timeout=6)
        j = r.json()
        items = j.get('items', [])
        if not items:
            await update.message.reply_text('Hech qanday mahsulot topilmadi.')
            uid = getattr(update.message.from_user, 'id', None)
            log_action('products_cmd', user=f'tg:{uid}', detail='no items found')
            return
        for it in items[:6]:
            item_id = it.get('id')
            text = f"{it.get('name')}\n{(it.get('description') or '')[:120]}\nNarx: {it.get('price') or ''}\n"

            # Build product page URL (uses same path pattern as earlier text)
            view_url = FLASK_APP_URL.rstrip('/') + f'/view_{item_id}'

            # collect candidate image urls from common keys
            candidate_keys = ['images', 'image_urls', 'media', 'media_urls', 'image_url']
            imgs = []
            for k in candidate_keys:
                v = it.get(k)
                if not v:
                    continue
                if isinstance(v, str):
                    imgs.append(v)
                elif isinstance(v, (list, tuple)):
                    for _u in v:
                        if isinstance(_u, str):
                            imgs.append(_u)

            # unique & up to 10
            seen = set()
            urls = []
            for u in imgs:
                if not u:
                    continue
                uu = u.strip()
                if not uu or uu in seen:
                    continue
                seen.add(uu)
                urls.append(uu)
                if len(urls) >= 10:
                    break

            img = urls[0] if urls else ''
            # If no images were provided by the API, use site default image
            if not urls:
                default_img = FLASK_APP_URL.rstrip('/') + '/static/defoult.jpg'
                urls = [default_img]
                img = default_img
                LOG.info('products_cmd: using default image for item %s -> %s', item_id, default_img)
                uid = getattr(update.message.from_user, 'id', None)
                log_action('products_default_image_used', user=f'tg:{uid}', detail=f'item:{item_id}')
            normalized = None
            if img:
                # If it's already an absolute URL, use it. Otherwise prefix with FLASK_APP_URL.
                if img.startswith('http://') or img.startswith('https://'):
                    normalized = img
                elif img.startswith('/'):
                    normalized = FLASK_APP_URL.rstrip('/') + img
                else:
                    # relative path or malformed URL -> attempt to prefix
                    normalized = FLASK_APP_URL.rstrip('/') + '/' + img
                LOG.info('products_cmd: normalized image url: %s -> %s', img, normalized)

            # Build inline buttons: only View (URL). Save/Buy removed as requested.
            buttons = [InlineKeyboardButton('View', url=view_url)]
            markup = InlineKeyboardMarkup([buttons])

            # If we have multiple images, try to send a media group
            if urls:
                media = []
                for idx, u in enumerate(urls):
                    # normalize each
                    if u.startswith('http://') or u.startswith('https://'):
                        nu = u
                    elif u.startswith('/'):
                        nu = FLASK_APP_URL.rstrip('/') + u
                    else:
                        nu = FLASK_APP_URL.rstrip('/') + '/' + u
                    if idx == 0:
                        media.append(InputMediaPhoto(media=nu, caption=text))
                    else:
                        media.append(InputMediaPhoto(media=nu))
                try:
                    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
                    # send buttons as a separate message (media_group can't contain inline keyboard for all)
                    await update.message.reply_text(text, reply_markup=markup)
                    uid = getattr(update.message.from_user, 'id', None)
                    log_action('products_sent', user=f'tg:{uid}', detail=f'item:{item_id} images:{len(urls)}')
                except Exception as e:
                    LOG.exception('send_media_group failed, falling back to single messages')
                    log_error(e, f'send_media_group item:{item_id}')
                    # fallback: send first image as photo + buttons
                    if normalized:
                        try:
                            await update.message.reply_photo(photo=normalized, caption=text, reply_markup=markup)
                            uid = getattr(update.message.from_user, 'id', None)
                            log_action('products_sent_fallback', user=f'tg:{uid}', detail=f'item:{item_id}')
                        except Exception as e2:
                            LOG.exception('failed sending photo in fallback, sending text')
                            log_error(e2, f'fallback_photo item:{item_id}')
                            await update.message.reply_text(text, reply_markup=markup)
                    else:
                        await update.message.reply_text(text, reply_markup=markup)
                        uid = getattr(update.message.from_user, 'id', None)
                        log_action('products_sent_text', user=f'tg:{uid}', detail=f'item:{item_id}')
            else:
                # no images: just send text with buttons
                await update.message.reply_text(text, reply_markup=markup)
                uid = getattr(update.message.from_user, 'id', None)
                log_action('products_sent_text', user=f'tg:{uid}', detail=f'item:{item_id}')
    except Exception:
        LOG.exception('products_cmd error')
        await update.message.reply_text('Mahsulotlarni yuklashda xatolik yuz berdi.')


async def handle_message(update: 'Update', context: 'ContextTypes.DEFAULT_TYPE'):
    # Basic echo + forward to site chat endpoint for AI processing
    try:
        text = update.message.text or ''
        uid = getattr(update.message.from_user, 'id', None)
        # Log the incoming chat text to actions file
        try:
            log_action('incoming_message', user=f'tg:{uid}', detail=text)
        except Exception:
            LOG.exception('Failed to log incoming message')

        payload = {'sender': f'tg:{uid}', 'text': text}
        if FLASK_APP_URL:
            try:
                requests.post(FLASK_APP_URL.rstrip('/') + '/api/chat/receive', json=payload, timeout=4)
            except Exception as e:
                LOG.exception('chat/receive POST failed')
                log_error(e, 'chat/receive POST failed')
        # Acknowledge
        await update.message.reply_text('Xabar qabul qilindi. Tez orada javob olasiz.')
    except Exception as e:
        LOG.exception('handle_message')
        log_error(e, 'handle_message')


    # callback_handler removed - Save/Buy buttons no longer used


def main():
    # PID file guard to avoid multiple getUpdates pollers (409 Conflict)
    try:
        pid_path = LOGS_DIR / 'telegram_bot.pid'
        if pid_path.exists():
            try:
                existing_pid = int(pid_path.read_text().strip())
                # Check if process exists
                try:
                    os.kill(existing_pid, 0)
                    LOG.error('Another bot process is running (pid=%s). Exiting to avoid getUpdates conflict.', existing_pid)
                    return
                except Exception:
                    LOG.info('Stale pid file found for pid %s, removing.', existing_pid)
                    try:
                        pid_path.unlink()
                    except Exception:
                        pass
            except Exception:
                try:
                    pid_path.unlink()
                except Exception:
                    pass
        # write my pid
        try:
            pid_path.write_text(str(os.getpid()))
        except Exception:
            LOG.exception('Failed to write telegram bot pid file')

        def _cleanup_pid():
            try:
                if pid_path.exists():
                    pid_path.unlink()
            except Exception:
                pass

        atexit.register(_cleanup_pid)
    except Exception:
        LOG.exception('PID guard setup failed')

    if not Updater or not TELEGRAM_TOKEN:
        if 'IMPORT_ERROR' in globals() and IMPORT_ERROR is not None:
            LOG.error('python-telegram-bot import failed: %s', IMPORT_ERROR)
            LOG.error("To fix: activate your virtualenv and run: python -m pip install 'python-telegram-bot>=20.0'")
        else:
            LOG.error('python-telegram-bot not installed or TELEGRAM_BOT_TOKEN not set')
            LOG.error("To fix: python -m pip install 'python-telegram-bot>=20.0' (or recreate your venv)")
        return

    # Build the v20+ Application with a custom HTTPXRequest to increase timeouts
    try:
        # Use default HTTPXRequest without unsupported kwargs to avoid TypeError
        from telegram.request import HTTPXRequest
        request = HTTPXRequest()
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(request).build()
    except Exception:
        # If HTTPXRequest import or construction fails, fall back to default builder
        LOG.info('HTTPXRequest unavailable or failed, using default ApplicationBuilder')
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('products', products_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    LOG.info('Telegram bot starting (polling)')
    try:
        app.run_polling()
    except Exception as exc:
        # Handle common getUpdates Conflict (409) by exiting cleanly to avoid flood
        try:
            msg = str(exc)
        except Exception:
            msg = ''

        LOG.error('Application.run_polling failed: %s', msg)

        if 'Conflict' in msg or 'getUpdates' in msg:
            LOG.error('Detected getUpdates conflict (another bot instance is polling). Exiting to avoid 409 errors.')
            return

        # For other exceptions (timeouts, network errors), attempt graceful shutdown using asyncio
        try:
            import asyncio

            loop = None
            try:
                loop = asyncio.get_event_loop()
            except Exception:
                loop = None

            if loop and loop.is_running():
                # schedule stop asynchronously
                try:
                    loop.create_task(app.stop())
                except Exception:
                    LOG.exception('Failed to schedule app.stop()')
            else:
                try:
                    # run stop synchronously if no running loop
                    asyncio.run(app.stop())
                except Exception:
                    LOG.exception('Failed to run app.stop() synchronously')
        except Exception:
            LOG.exception('Application.stop failed')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
