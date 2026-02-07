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
from dotenv import load_dotenv
import threading
from flask import Flask
import json
load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))


try:
    from telegram import Update, Bot, InputMediaPhoto, ReplyKeyboardMarkup, KeyboardButton

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

LOG = logging.getLogger("telegram_bot")

# Load Uzum products data
def load_uzum_products():
    try:
        products_file = Path(__file__).parent / "test" / "bot_ready_products_1770480265230.json"
        if products_file.exists():
            with open(products_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            LOG.warning("Uzum products file not found")
            return None
    except Exception as e:
        LOG.error(f"Error loading Uzum products: {e}")
        return None

UZUM_PRODUCTS = load_uzum_products()

# Ensure logs directory exists and define action/error log paths
# Use bot directory so we don't require write access to backend/logs
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_LOG = LOGS_DIR / "telegram_actions.txt"
ERROR_LOG = LOGS_DIR / "telegram_errors.txt"


def _looks_like_image_url(url: str) -> bool:
    try:
        if not url:
            return False
        u = url.lower()
        return any(
            u.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")
        )
    except Exception:
        return False


def _is_valid_image_url(url: str) -> bool:
    """Return True only if URL resolves to an actual image payload.

    We first try HEAD, then GET a few bytes to confirm signature.
    Also avoid known placeholders like 'defoult.png' that may be blocked.
    """
    try:
        if not url:
            return False
        u = url.strip().lower()

        # Quick HEAD probe
        try:
            r = requests.head(url, allow_redirects=True, timeout=5)
            ct = (r.headers or {}).get("Content-Type", "").lower()
            if not ct.startswith("image/"):
                # Some servers misreport on HEAD; fall back to GET
                pass
            else:
                # Looks fine, but still double-check by fetching small chunk
                pass
        except Exception:
            # HEAD failed; continue with GET validation
            pass

        # GET small chunk to verify signature
        rg = requests.get(url, stream=True, allow_redirects=True, timeout=6)
        ctg = (rg.headers or {}).get("Content-Type", "").lower()
        if not ctg.startswith("image/"):
            return False
        # Read first chunk
        chunk = b""
        try:
            for c in rg.iter_content(chunk_size=2048):
                if c:
                    chunk = c
                    break
        finally:
            try:
                rg.close()
            except Exception:
                pass
        if not chunk:
            return False
        # Basic magic signatures for JPEG/PNG/WEBP/GIF
        if chunk.startswith(b"\xff\xd8\xff"):
            return True  # JPEG
        if chunk.startswith(b"\x89PNG\r\n\x1a\n"):
            return True  # PNG
        if chunk.startswith(b"GIF87a") or chunk.startswith(b"GIF89a"):
            return True  # GIF
        if chunk[:12] == b"RIFF" + chunk[4:8] + b"WEBP":
            return True  # WEBP (best-effort)
        # Fallback to content-type only if signature unknown
        return True
    except Exception:
        return False


def _openai_generate_reply(user_text: str) -> str:
    """Best-effort call to OpenAI to generate an Uzbek reply.

    Returns empty string on failure. Reads API key from OPENAI_API_KEY (or OPENAI_API).
    """
    try:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API")
        if not api_key or not user_text:
            return ""

        system_prompt = (
            "Siz Pro Obuv do'koni uchun yordamchi AI. Har doim o'zbek tilida,"
            " qisqa va aniq javob bering. Mavjud ma'lumot: Pro Obuv spetsobuv,"
            " ish kiyimlari va himoya vositalarini sotadi. Agar savol buyurtma,"
            " narx, yetkazib berish, o'lcham, rang, mavjudlik, kafolat, to'lov haqida"
            " bo'lsa, do'kon kontekstida javob bering. Noaniq bo'lsa, muloyimlik bilan"
            " qo'shimcha ma'lumot so'rang."
        )

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0.4,
            "max_tokens": 350,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=8,
        )
        if not resp or not resp.ok:
            return ""
        data = resp.json() or {}
        choices = data.get("choices") or []
        if not choices:
            return ""
        content = ((choices[0].get("message") or {}).get("content") or "").strip()
        return content
    except Exception:
        LOG.exception("OpenAI call failed")
        return ""


def _now_iso():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def log_action(action: str, user: str = None, detail: str = ""):
    try:
        line = f"{_now_iso()} | ACTION | {action}"
        if user:
            line += f" | user:{user}"
        if detail:
            line += f" | {detail}"
        line += "\n"
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        LOG.exception("Failed to write action log")


def log_error(err: Exception, context: str = ""):
    try:
        tb = traceback.format_exc()
        line = f"{_now_iso()} | ERROR | {context}\n{tb}\n"
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        LOG.exception("Failed to write error log")


def api_post(path: str, json: dict = None, timeout: int = 10, retries: int = 3):
    """Helper to POST to the Flask app API using the configured FLASK_APP_URL.

    - Composes the full URL from `FLASK_APP_URL` and `path`.
    - Retries on connection errors with small backoff.
    - Returns the `requests.Response` or `None` on failure.
    """
    try:
        if not FLASK_APP_URL:
            LOG.debug("api_post: FLASK_APP_URL not configured")
            return None

        # Ensure leading slash
        if not path.startswith("/"):
            path = "/" + path
        url = FLASK_APP_URL.rstrip("/") + path

        for attempt in range(1, max(1, int(retries)) + 1):
            try:
                r = requests.post(url, json=json, timeout=timeout)
                return r
            except Exception as e:
                # Log and retry briefly for transient network issues
                log_error(e, f"api_post error url={url} attempt={attempt}")
                if attempt < retries:
                    try:
                        time.sleep(0.4 * attempt)
                    except Exception:
                        pass
        return None
    except Exception as e:
        log_error(e, f"api_post fatal for path={path}")
        return None


async def _send_text_to_telegram(chat_id: int, text: str) -> None:
    """Yordamchi: bitta text xabarni Telegram foydalanuvchisiga yuborish.  

    Bu funksiya ApplicationBuilder dan foydalanadi. U run_both.py orqali   
    fon jarayon sifatida ishlayotgan botga mos keladi.
    """
    if not TELEGRAM_TOKEN or not Updater:
        return
    try:
        # Global bot application instance dan foydalanish
        # Agar bot allaqachon ishlayotgan bo'lsa, yangi application yaratmaslik kerak
        from telegram import Bot
        bot = Bot(token=TELEGRAM_TOKEN)
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        finally:
            try:
                await bot.close()
            except Exception:
                pass
    except Exception as e:
        log_error(e, f"_send_text_to_telegram chat_id={chat_id}")


def send_operator_reply(client_key: str, text: str, operator_name: str = "Operator") -> None:
    """Flask backend dan chaqiriladigan soddalashtirilgan yordamchi.       

    client_key odatda 'tg:<user_id>' formatida bo'ladi. Bu funksiya ushbu  
    foydalanuvchiga bot orqali javob yuboradi. Flask tomoni sync bo'lgani  
    uchun ichida asyncio event loop ni best-effort ishga tushiramiz.       
    """
    try:
        if not client_key or not isinstance(client_key, str):
            LOG.warning(f"send_operator_reply: invalid client_key: {client_key}")
            return
        if not client_key.startswith("tg:"):
            LOG.warning(f"send_operator_reply: client_key not telegram format: {client_key}")
            return
        try:
            chat_id = int(client_key.split(":", 1)[1])
        except Exception as e:
            LOG.warning(f"send_operator_reply: failed to parse chat_id from {client_key}: {e}")
            return

        # Xabar matniga operator ismini qo'shib yuboramiz
        full_text = f"{operator_name}: {text}" if operator_name else text  

        import asyncio

        # Agar allaqachon event loop ishlayotgan bo'lsa, create_task ishlatamiz,
        # aks holda yangi loop yaratib, bitta marta ishlatamiz. (get_running_loop /
        # new_event_loop ishlatamiz — get_event_loop() Python 3.10+ da deprecated.)
        try:
            loop = asyncio.get_running_loop()
            # Running loop mavjud - background task sifatida ishga tushiramiz
            loop.create_task(_send_text_to_telegram(chat_id, full_text))
            LOG.info(f"send_operator_reply: scheduled message to {chat_id} via running loop")
        except RuntimeError:
            # No running loop - yangi loop yaratamiz
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_send_text_to_telegram(chat_id, full_text))
                LOG.info(f"send_operator_reply: sent message to {chat_id} via new loop")
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
        except Exception as e:
            LOG.exception(f"send_operator_reply: error in event loop handling: {e}")
            # Fallback: to'g'ridan-to'g'ri requests orqali yuborishga urinamiz
            try:
                from telegram import Bot
                import asyncio
                bot = Bot(token=TELEGRAM_TOKEN)
                asyncio.run(bot.send_message(chat_id=chat_id, text=full_text))
                bot.close()
                LOG.info(f"send_operator_reply: sent message to {chat_id} via fallback method")
            except Exception as fallback_error:
                LOG.exception(f"send_operator_reply: fallback method also failed: {fallback_error}")
    except Exception as e:
        log_error(e, f"send_operator_reply client_key={client_key}")


# Prefer environment variable for the Flask app base URL. Allow multiple
# environment variable names for backwards compatibility and override.
# Read Telegram bot token from environment only. Do NOT keep a hardcoded
# token in source control. If not set, the bot will not start.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")

# Try several env var names (set in hosting) before falling back to sensible
# defaults. If running locally together with the Flask app, the probe below
# will detect a local server and use it. In production we prefer the public
# site URL rather than defaulting to localhost which often isn't reachable.
FLASK_APP_URL = (
    os.environ.get("FLASK_APP_URL")
    or os.environ.get("BOT_API_BASE")
    or os.environ.get("API_BASE")
    or ""
).strip()

if not FLASK_APP_URL:
    try:
        # Quick local probe to see if a dev Flask server is running alongside
        # the bot (useful for development). Non-blocking and short timeout.
        _probe = requests.get("http://127.0.0.1:5000/api/chat/ai", timeout=0.8)
        if _probe is not None and (_probe.status_code // 100) in (2, 4, 5):
            FLASK_APP_URL = "http://127.0.0.1:5000"
    except Exception:
        # No local server detected; fall back to the public site URL so the
        # bot can still reach the app when deployed (change via env var).
        FLASK_APP_URL = os.environ.get("FLASK_APP_URL") or os.environ.get("BOT_API_BASE") or "https://www.safety.uz"

# Normalize (ensure no trailing slash)
FLASK_APP_URL = FLASK_APP_URL.rstrip("/")
LOG.info("Using FLASK_APP_URL for API calls: %s", FLASK_APP_URL)


async def _send_main_keyboard(update: "Update"):
    """Yagona joyda asosiy klaviaturani yuborish.

    Har doim quyidagi tugmalar ko'rinadi:
    - Mahsulotlar
    - AI bilan suhbat
    - Operator bilan suhbat
    """
    try:
        kb = [
            [
                KeyboardButton("🛒 Mahsulotlar"),
                KeyboardButton("🛍️ Uzum mahsulotlar"),
            ],
            [
                KeyboardButton("🤖 AI bilan suhbat"),
                KeyboardButton("👨‍💼 Operator bilan suhbat"),
            ],
        ]
        markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
        await update.message.reply_text(
            "Quyidagi tugmalardan foydalaning:", reply_markup=markup
        )
    except Exception as e:
        log_error(e, "send_main_keyboard")


async def start(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    try:
        # Standart rejim: AI bilan suhbat
        context.user_data["chat_mode"] = "ai"
        await update.message.reply_text(
            "Assalomu alaykum! Mahsulotlar uchun /products yoki '🛒 Mahsulotlar' tugmasini bosing."
        )
        await _send_main_keyboard(update)
        uid = getattr(update.message.from_user, "id", None)
        log_action("start_command", user=f"tg:{uid}", detail="start command sent")
    except Exception as e:
        log_error(e, "start handler")
        raise


async def test_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Simple test command to verify bot is working"""
    try:
        await update.message.reply_text("✅ Bot is working! Version 3.0")
        uid = getattr(update.message.from_user, "id", None)
        log_action("test_command", user=f"tg:{uid}", detail="test command sent")
    except Exception as e:
        log_error(e, "test handler")
        raise


async def products_cmd_uzum(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Show Uzum products from seller API data"""
    if not UZUM_PRODUCTS or not UZUM_PRODUCTS.get("products"):
        await update.message.reply_text("❌ Mahsulotlar ma'lumotlari topilmadi")
        return
    
    products = UZUM_PRODUCTS["products"]
    available_products = [p for p in products if p.get("totalQuantity", 0) > 0]
    
    if not available_products:
        await update.message.reply_text("❌ Hozirda mavjud mahsulotlar yo'q")
        return
    
    # Show first 10 available products
    for i, product in enumerate(available_products[:10]):
        title = product.get("title", "Noma'lum mahsulot")
        price = product.get("priceRange", "Narx noma'lum")
        quantity = product.get("totalQuantity", 0)
        brand = product.get("brand", "Noma'lum")
        product_id = product.get("id", "")
        
        # Create Uzum URL
        if product_id:
            uzum_url = f"https://uzum.uz/product/{product_id}"
        else:
            uzum_url = product.get("uzumMarketUrl", "https://uzum.uz")
        
        message = f"🛍️ *{title}*\n"
        message += f"💰 Narx: {price}\n"
        message += f"📊 Mavjud: {quantity} dona\n"
        message += f"🏷️ Brend: {brand}\n"
        message += f"🔗 [Uzum da ko'rish]({uzum_url})"
        
        try:
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            log_error(e, f"products_cmd_uzum product {i}")
            # Fallback without markdown
            await update.message.reply_text(f"{title}\nNarx: {price}\nMavjud: {quantity} dona\nUzum: {uzum_url}")
        
        # Small delay between messages
        await asyncio.sleep(0.5)
    
    uid = getattr(update.message.from_user, "id", None)
    log_action("products_cmd_uzum", user=f"tg:{uid}", detail=f"showed {len(available_products)} products")


async def products_cmd_new(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Original products command - fetch from Flask API"""
    try:
        # Instead of immediately listing all products, ask user to choose a category
        kb = [[KeyboardButton("спецобувь")], [KeyboardButton("спецодежда")]]
        markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
        await update.message.reply_text(
            "Kategoriyani tanlang:", reply_markup=markup
        )
        uid = getattr(update.message.from_user, "id", None)
        log_action("products_cmd_new", user=f"tg:{uid}", detail="category selection shown")
        return
    except Exception as e:
        log_error(e, "products_cmd_new category selection")
        await update.message.reply_text("Kategoriyalarni yuklashda xatolik yuz berdi.")
        return


async def products_cmd_category(update: "Update", context: "ContextTypes.DEFAULT_TYPE", category_slug: str = ""):
                            user=f"tg:{uid}",
                            detail=f"item:{item_id}",
                        )
                    except Exception:
                        # fallback to text only if default image missing
                        await update.message.reply_text(
                            text, reply_markup=markup, parse_mode="HTML"
                        )
                        uid = getattr(update.message.from_user, "id", None)
                        log_action(
                            "products_sent_text",
                            user=f"tg:{uid}",
                            detail=f"item:{item_id}",
                        )

            except Exception as item_error:
                LOG.exception("Error processing item %s: %s", item_id, str(item_error))
                log_error(item_error, f"item_processing item:{item_id}")
                continue

    except Exception:
        LOG.exception("products_cmd error")
        await update.message.reply_text("Mahsulotlarni yuklashda xatolik yuz berdi.")


async def _item_matches_category(item: dict, slug: str) -> bool:
    """Return True if the provided item appears to belong to category `slug`.

    This is a best-effort check that looks at several possible fields that
    the API/DB might populate (`category`, `category_slug`, `categories`,
    `tags`) so it is tolerant to different backend shapes.
    """
    try:
        if not item or not slug:
            return False
        s = slug.lower()
        # Common fields
        for k in ("category", "category_slug", "cat", "category_id"):
            v = item.get(k)
            if isinstance(v, str) and v.lower() == s:
                return True
        # categories or tags lists
        for k in ("categories", "tags", "categories_slugs"):
            v = item.get(k)
            if isinstance(v, (list, tuple)):
                for el in v:
                    try:
                        if isinstance(el, str) and el.lower() == s:
                            return True
                        if isinstance(el, dict):
                            # maybe {"slug": "specobuv"}
                            if el.get("slug", "").lower() == s or el.get("id", "").lower() == s:
                                return True
                    except Exception:
                        continue
        # Fallback: sometimes category is stored as human-readable name
        v = item.get("category") or item.get("group") or item.get("type")
        if isinstance(v, str) and s in v.lower():
            return True
    except Exception:
        pass
    return False


async def products_cmd_category(update: "Update", context: "ContextTypes.DEFAULT_TYPE", category_slug: str = ""):
    """List products filtered by `category_slug`.

    This reuses the main listing logic but filters items client-side if the
    backend does not offer category query parameters.
    """
    LOG.info("products_cmd_category called for %s", category_slug)
    try:
        await update.message.reply_text("🛍️ Mahsulotlar yuklanmoqda...")
    except Exception:
        pass

    try:
        url = FLASK_APP_URL.rstrip('/') + "/api/menu-search?limit=1000"
        r = requests.get(url, timeout=10)
        j = r.json() if r is not None and r.ok else {}
        items = j.get("items", [])
        if not items:
            await update.message.reply_text("Hech qanday mahsulot topilmadi.")
            return

        # Filter by category_slug
        if category_slug:
            filtered = []
            for it in items:
                try:
                    if await _item_matches_category(it, category_slug):
                        filtered.append(it)
                except Exception:
                    continue
            items = filtered

        if not items:
            await update.message.reply_text("Ushbu kategoriyada mahsulotlar topilmadi.")
            return

        # Reuse existing sending logic (send first N items to avoid flooding)
        for it in items:
            try:
                item_id = it.get("id")
                if not item_id:
                    continue
                item_name = it.get("name", "Mahsulot")
                item_description = (it.get("description", "")[:200] if it.get("description") else "Sifatli mahsulot")
                view_url = FLASK_APP_URL.rstrip('/') + f"/product/{item_id}"
                text = f"🛍️ <b>{item_name}</b>\n\n{item_description}\n\n🔗 Mahsulot: {view_url}"

                # pick image same way as products_cmd_new
                imgs = []
                media_list = it.get("media") or it.get("item_media") or []
                if isinstance(media_list, (list, tuple)):
                    for m in media_list:
                        if isinstance(m, dict):
                            u = m.get("media_url") or m.get("url")
                            if isinstance(u, str) and u.strip():
                                imgs.append(u.strip())
                candidate_keys = ["image_url", "images", "image_urls", "media_urls"]
                for k in candidate_keys:
                    v = it.get(k)
                    if not v:
                        continue
                    if isinstance(v, str):
                        if v.strip():
                            imgs.append(v.strip())
                    elif isinstance(v, (list, tuple)):
                        for _u in v:
                            if isinstance(_u, str) and _u.strip():
                                imgs.append(_u.strip())

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
                if not urls:
                    default_img = 'https://res.cloudinary.com/dpfbu9aid/image/upload/v1766927327/products/defoult.webp'
                    urls = [default_img]
                    img = default_img

                normalized = None
                if img:
                    if img.startswith('http://') or img.startswith('https://'):
                        normalized = img
                    elif img.startswith('/'):
                        normalized = FLASK_APP_URL.rstrip('/') + img
                    else:
                        normalized = FLASK_APP_URL.rstrip('/') + '/' + img

                buttons = [InlineKeyboardButton("👁️ Mahsulotni ko'rish", url=view_url)]
                markup = InlineKeyboardMarkup([buttons])

                if normalized:
                    try:
                        await update.message.reply_photo(photo=normalized, caption=text, reply_markup=markup, parse_mode='HTML')
                    except Exception:
                        try:
                            rimg = requests.get(normalized, timeout=10)
                            rimg.raise_for_status()
                            data = rimg.content
                            await update.message.reply_photo(photo=data, caption=text, reply_markup=markup, parse_mode='HTML')
                        except Exception:
                            await update.message.reply_text(text, reply_markup=markup, parse_mode='HTML')
                else:
                    try:
                        default_path = (LOGS_DIR.parent.parent / "frontend" / "static" / "defoult.webp").resolve()
                        with open(default_path, 'rb') as f:
                            data = f.read()
                        await update.message.reply_photo(photo=data, caption=text, reply_markup=markup, parse_mode='HTML')
                    except Exception:
                        await update.message.reply_text(text, reply_markup=markup, parse_mode='HTML')
            except Exception:
                continue
    except Exception as e:
        LOG.exception('products_cmd_category failed')
        await update.message.reply_text('Mahsulotlarni yuklashda xatolik yuz berdi.')


async def handle_message(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Matnli xabarlar uchun handler.

    Rejimlar:
    - "ai": /api/chat/ai orqali AI javob
    - "operator": operator bilan jonli chat (serverga yoziladi)
    Maxsus tugmalar:
    - "🛒 Mahsulotlar" -> /products
    - "🤖 AI bilan suhbat" -> chat_mode = "ai"
    - "👨‍💼 Operator bilan suhbat" -> chat_mode = "operator"
    """
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        uid = getattr(update.message.from_user, "id", None)
        sender = f"tg:{uid}" if uid is not None else "tg:unknown"

        # Log the incoming chat text
        try:
            log_action("incoming_message", user=sender, detail=text)
        except Exception:
            LOG.exception("Failed to log incoming message")

        # Build a unified payload for both AI and operator chat so that
        # /api/chat/receive, /api/chat/ai va /api/operator-chat/user/send
        # bir xil strukturani oladi.
        payload = {
            "sender": sender,
            "text": text,
            "source": "telegram",
        }
        # Mavjud bo'lsa, foydalanuvchi ismi va username ni ham qo'shamiz
        try:
            u = update.message.from_user
            if u:
                fullname = ((u.first_name or "") + " " + (u.last_name or "")).strip()
                if fullname:
                    payload["sender_name"] = fullname
                if u.username:
                    payload["client_username"] = u.username
        except Exception:
            pass

        # Maxsus tugmalarni tekshiramiz
        if text in ("/products", "🛒 Mahsulotlar"):
            # Show product category keyboard (do not immediately restore main keyboard)
            await products_cmd_new(update, context)
            return
        if text in ("/uzum", "🛍️ Uzum mahsulotlar"):
            # Show Uzum products
            await products_cmd_uzum(update, context)
            return
        # Category quick buttons (from products_cmd_new reply keyboard)
        if text == "спецобувь":
            # Map Russian label to internal category slug
            await products_cmd_category(update, context, category_slug="specobuv")
            # After listing items, return user to main keyboard for further actions
            await _send_main_keyboard(update)
            return
        if text == "спецодежда":
            await products_cmd_category(update, context, category_slug="specodezhda")
            # After listing items, return user to main keyboard for further actions
            await _send_main_keyboard(update)
            return
        if text in ("/ai", "🤖 AI bilan suhbat"):
            context.user_data["chat_mode"] = "ai"
            await update.message.reply_text(
                "AI rejimi yoqildi. Savollaringizni yozing.",
            )
            await _send_main_keyboard(update)
            return
        if text in ("/operator", "👨‍💼 Operator bilan suhbat"):
            context.user_data["chat_mode"] = "operator"
            await update.message.reply_text(
                "Operator bilan suhbat rejimi yoqildi. Xabaringizni yozing, xodimlar ko'rishadi.",
            )
            await _send_main_keyboard(update)
            return

        mode = context.user_data.get("chat_mode") or "ai"

        if FLASK_APP_URL and mode == "operator":
            # Operator bilan real chat: alohida endpointga yozamiz
            # source va sender maydonlarini to'g'ri o'rnatamiz
            payload["source"] = "telegram"
            try:
                r = api_post("/api/operator-chat/user/send", json=payload, timeout=10, retries=3)
                if r is not None and r.ok:
                    try:
                        j = r.json() or {}
                        ack = j.get("message") or "Xabar operatorga yuborildi."
                    except Exception:
                        ack = "Xabar operatorga yuborildi."
                else:
                    ack = "Xabar operatorga yuborildi."
            except Exception as e:
                LOG.exception("operator-chat send failed")
                log_error(e, "operator_chat_send_failed")
                ack = "Xabar qabul qilindi. Tez orada javob olasiz."

            await update.message.reply_text(ack)
            return

        # Default / AI rejimi
        if FLASK_APP_URL:
            try:
                # best-effort log of inbound (ai_respond + log uchun)
                try:
                    api_post("/api/chat/receive", json=payload, timeout=4, retries=1)
                except Exception as e:
                    LOG.exception("chat/receive POST failed")
                    log_error(e, "chat/receive POST failed")

                # Call Uzbek AI endpoint and reply back to user
                ai_r = api_post("/api/chat/ai", json=payload, timeout=10, retries=3)
                ai_text = ""
                ai_j = {}
                if ai_r is not None and ai_r.status_code == 200:
                    ct = (ai_r.headers or {}).get("Content-Type", "")
                    if "application/json" in ct.lower() or ai_r.text.strip().startswith("{"):
                        try:
                            ai_j = ai_r.json() or {}
                        except Exception:
                            ai_j = {}

                ai_text = (ai_j or {}).get("reply") or ""

                # Telegram bot AI javobi har doim sayt /api/chat/ai bilan bir xil
                if not ai_text:
                    try:
                        with open(
                            LOGS_DIR / "ai_unknown_questions.txt", "a", encoding="utf-8"
                        ) as f:
                            f.write(f"{_now_iso()} | {sender} | {text}\n")
                    except Exception:
                        pass
                    ai_text = "Xatolik: hozircha javob bera olmadim. Iltimos, savolingizni boshqacha qilib yozing."

                await update.message.reply_text(ai_text)
            except Exception as e:
                LOG.exception("chat/ai POST failed")
                log_error(e, "chat/ai POST failed")
                await update.message.reply_text(
                    "Xatolik: hozircha javob bera olmadim. Iltimos, savolingizni boshqacha qilib yozing."
                )
        else:
            await update.message.reply_text(
                "Xatolik: hozircha javob bera olmadim. Iltimos, savolingizni boshqacha qilib yozing."
            )
    except Exception as e:
        LOG.exception("handle_message")
        log_error(e, "handle_message")

    # callback_handler removed - Save/Buy buttons no longer used


def main():
    # PID file guard to avoid multiple getUpdates pollers (409 Conflict)
    try:
        pid_path = LOGS_DIR / "telegram_bot.pid"
        if pid_path.exists():
            try:
                existing_pid = int(pid_path.read_text().strip())
                # Check if process exists
                try:
                    os.kill(existing_pid, 0)
                    LOG.error(
                        "Another bot process is running (pid=%s). Exiting to avoid getUpdates conflict.",
                        existing_pid,
                    )
                    return
                except Exception:
                    LOG.info("Stale pid file found for pid %s, removing.", existing_pid)
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
            LOG.exception("Failed to write telegram bot pid file")

        def _cleanup_pid():
            try:
                if pid_path.exists():
                    pid_path.unlink()
            except Exception:
                pass

        atexit.register(_cleanup_pid)
    except Exception:
        LOG.exception("PID guard setup failed")

    if not Updater or not TELEGRAM_TOKEN:
        if "IMPORT_ERROR" in globals() and IMPORT_ERROR is not None:
            LOG.error("python-telegram-bot import failed: %s", IMPORT_ERROR)
            LOG.error(
                "To fix: activate your virtualenv and run: python -m pip install 'python-telegram-bot>=20.0'"
            )
        else:
            LOG.error("python-telegram-bot not installed or TELEGRAM_BOT_TOKEN not set")
            LOG.error(
                "To fix: python -m pip install 'python-telegram-bot>=20.0' (or recreate your venv)"
            )
        return

    # Build the v20+ Application with a custom HTTPXRequest to increase timeouts
    app = None
    try:
        # Use default HTTPXRequest without unsupported kwargs to avoid TypeError
        from telegram.request import HTTPXRequest

        request = HTTPXRequest()
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(request).build()
    except Exception:
        # If HTTPXRequest import or construction fails, fall back to default builder
        LOG.info("HTTPXRequest unavailable or failed, using default ApplicationBuilder")
        try:
            app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        except Exception as e:
            LOG.exception("Failed to create Application: %s", e)
            return
    
    if not app:
        LOG.error("Failed to create Telegram Application")
        return
    
    # Global error handler for the Application (python-telegram-bot v20+)
    async def _global_error_handler(update: object, context: "ContextTypes.DEFAULT_TYPE"):
        """Centralized error handler to capture exceptions raised in handlers.

        This prevents the library from printing unhandled tracebacks and lets
        us write a concise message to our own logs and error file.
        """
        try:
            # context.error is set by PTB when an exception occurs
            err = getattr(context, "error", None)
            if err is None:
                # Fallback: try to extract exception from sys.exc_info
                import sys

                err = sys.exc_info()[1]

            LOG.exception("Telegram handler exception: %s", err)
            # Persist a brief traceback to our persistent error log
            try:
                log_error(err, context=str(update))
            except Exception:
                LOG.exception("Failed to write to telegram error log")
        except Exception:
            # Ensure the error handler never raises
            LOG.exception("Global error handler failed")

    # Register the global error handler so the Application logs exceptions via our handler
    try:
        app.add_error_handler(_global_error_handler)
    except Exception:
        # Some older/newer variants might expose different API - try dispatcher fallback
        try:
            if hasattr(app, "dispatcher") and app.dispatcher:
                app.dispatcher.add_error_handler(_global_error_handler)
        except Exception:
            LOG.exception("Failed to register global telegram error handler")
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CommandHandler("products", products_cmd_new))
    app.add_handler(CommandHandler("uzum", products_cmd_uzum))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    LOG.info("Telegram bot starting (polling)")

    # Robust polling loop with retry/backoff for transient errors (409 Conflict, timeouts)
    max_retries = int(os.environ.get("TELEGRAM_BOT_RETRIES", "5"))
    base_delay = float(os.environ.get("TELEGRAM_BOT_RETRY_DELAY", "5"))
    attempt = 0

    # Ensure an asyncio event loop is available in this thread. Python 3.10+
    # deprecates get_event_loop() when no loop is set; create and set one if missing.
    try:
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
    except Exception:
        LOG.exception("Failed to ensure asyncio event loop is available")

    while True:
        try:
            app.run_polling()
            # Normal exit (clean stop) -> break the loop
            break
        except Exception as exc:
            try:
                msg = str(exc) or ""
            except Exception:
                msg = ""

            LOG.error("Application.run_polling failed: %s", msg)

            # Handle getUpdates conflict: this is caused by another bot instance or
            # an active webhook. Retrying repeatedly only floods logs with 409s.
            # Instead, log a clear error and exit so deployments/platforms can
            # ensure a single bot instance runs (or switch to webhook mode).
            if "Conflict" in msg or "getUpdates" in msg:
                # Mask token for logs
                def _mask_token(tkn: str) -> str:
                    try:
                        if not tkn:
                            return "(none)"
                        parts = tkn.split(":")
                        if len(parts) >= 1:
                            bid = parts[0]
                            return f"bot_id={bid} (token masked)"
                    except Exception:
                        pass
                    return "(token masked)"

                LOG.error(
                    "getUpdates conflict detected (409). Another getUpdates request or a webhook is active; exiting to avoid conflict. %s",
                    _mask_token(TELEGRAM_TOKEN),
                )
                LOG.error(
                    "If you intend to run the bot in webhook mode, remove polling or disable auto-start. If running multiple instances, ensure START_TELEGRAM_BOT=0 or use a single managed process."
                )
                # Do not retry - raise exception to trigger restart in outer loop
                raise Exception("Conflict detected - need restart")

            # For other exceptions (timeouts, network errors), attempt graceful shutdown using asyncio
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # If loop is running, schedule stop; otherwise run stop synchronously
                try:
                    if loop.is_running():
                        try:
                            loop.create_task(app.stop())
                        except Exception:
                            LOG.exception("Failed to schedule app.stop()")
                    else:
                        try:
                            loop.run_until_complete(app.stop())
                        except RuntimeError as re:
                            # Application may not be running; ignore this specific case
                            LOG.warning("app.stop() raised RuntimeError: %s", re)
                        except Exception:
                            LOG.exception("Failed to run app.stop() synchronously")
                except Exception:
                    LOG.exception("Error while attempting app.stop()")
            except Exception:
                LOG.exception("Application.stop failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create simple Flask app for health checks
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        return {"status": "ok", "service": "telegram-bot"}
    
    @app.route('/health')
    def health():
        return {"status": "healthy"}
    
    @app.route('/ping')
    def ping():
        return "pong"
    
    # Start Flask server in main thread
    port = int(os.environ.get('PORT', 10000))
    
    # Start Telegram bot in background thread
    import asyncio
    
    def run_telegram_bot():
        while True:  # Infinite retry loop
            try:
                main()
            except Exception as e:
                LOG.error(f"Telegram bot crashed: {e}")
                LOG.info("Restarting bot in 30 seconds...")
                time.sleep(30)  # Wait before retry
    
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=False)
    bot_thread.start()
    
    # Give bot time to start
    time.sleep(2)
    
    LOG.info(f"Starting health check server on port {port}")
    
    # Run Flask server in main thread (this keeps the process alive)
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        LOG.info("Shutting down...")
    except Exception as e:
        LOG.error(f"Flask server error: {e}")
