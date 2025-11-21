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

# Ensure logs directory exists and define action/error log paths
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
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
        # aks holda yangi loop yaratib, bitta marta ishlatamiz.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running loop mavjud - background task sifatida ishga tushiramiz
                loop.create_task(_send_text_to_telegram(chat_id, full_text))
                LOG.info(f"send_operator_reply: scheduled message to {chat_id} via running loop")
            else:
                # Loop mavjud lekin ishlamayapti - run_until_complete ishlatamiz
                loop.run_until_complete(_send_text_to_telegram(chat_id, full_text))
                LOG.info(f"send_operator_reply: sent message to {chat_id} via existing loop")
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


# Prefer environment variable, but fallback to the token you provided so the
# bot can run without setting env when testing locally. For production, set
# TELEGRAM_BOT_TOKEN in environment and remove the hardcoded fallback.
TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8443912951:AAF-1gKuqQv0b0BQw_KOPCS85gYZk-n10V4"
)

# FLASK_APP_URL should be set in environment; default to safety.uz if missing.
FLASK_APP_URL = (os.environ.get("FLASK_APP_URL") or "").strip()
# If no FLASK_APP_URL provided, prefer a local dev server if reachable, otherwise
# fall back to the production default. This helps local runs where the app is
# started together with the bot (no external URL needed).
if not FLASK_APP_URL:
    try:
        # probe local Flask default address quickly
        _probe = requests.get("http://127.0.0.1:5000/api/chat/ai", timeout=0.8)
        # If we get any 200-range or 405/501 (method not allowed, etc.), assume local server exists
        if _probe is not None and (_probe.status_code // 100) in (2, 4, 5):
            FLASK_APP_URL = "http://127.0.0.1:5000"
    except Exception:
        # no local server detected; fall back to configured env var or default
        # Local development uchun default localhost
        FLASK_APP_URL = os.environ.get("FLASK_APP_URL", "http://127.0.0.1:5000")
else:
    FLASK_APP_URL = FLASK_APP_URL


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


async def products_cmd_new(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    # Fetch a small list of products (for demo use menu API)
    # DEBUG: Force reload by adding timestamp
    LOG.info("products_cmd_new called - version 3.0 - %s", datetime.now().isoformat())

    # Simple fallback first
    try:
        await update.message.reply_text("🛍️ Mahsulotlar yuklanmoqda...")
    except Exception as e:
        LOG.exception("Failed to send loading message")

    try:
        # Barcha mahsulotlarni yuklash uchun limitni katta qilamiz
        url = FLASK_APP_URL.rstrip("/") + "/api/menu-search?limit=1000"
        r = requests.get(url, timeout=10)
        j = r.json()
        items = j.get("items", [])
        if not items:
            await update.message.reply_text("Hech qanday mahsulot topilmadi.")
            uid = getattr(update.message.from_user, "id", None)
            log_action("products_cmd", user=f"tg:{uid}", detail="no items found")
            return

        # Barcha mahsulotlarni yuborish
        for it in items:
            try:
                # Extract product data
                item_id = it.get("id")
                if not item_id:
                    LOG.warning("Skipping item without ID: %s", it)
                    continue

                item_name = it.get("name", "Mahsulot")
                item_description = (
                    it.get("description", "")[:200]
                    if it.get("description")
                    else "Sifatli mahsulot"
                )
                # Narxni chatga yubormaymiz
                # item_price = it.get("price", "Narx ko'rsatilmagan")

                # Build product page URL
                view_url = FLASK_APP_URL.rstrip("/") + f"/product/{item_id}"
                LOG.info("Processing item %s: %s", item_id, item_name)

                # Social media links
                social_links = f"""
📱 Bizni kuzating:
• <a href="https://www.instagram.com/proguarduz/">INSTAGRAM</a>   
• <a href="https://t.me/specobuv">TELEGRAM</a>   
• <a href="https://www.youtube.com/channel/UCAsyOqztQHOgWX95086LCIA">YOUTUBE</a>   
• <a href="https://www.facebook.com/aklashoes/">FACEBOOK</a>

🔗 Mahsulot haqida batafsil: {view_url}"""

                # Format the product message
                text = f"""🛍️ <b>{item_name}</b>

{item_description}
{social_links}"""

                # Get product images
                # Collect possible image URLs from multiple structures
                # 1) Structured media list with media_url from /api/menu-search
                imgs = []
                media_list = it.get("media") or it.get("item_media") or []
                if isinstance(media_list, (list, tuple)):
                    for m in media_list:
                        if isinstance(m, dict):
                            u = m.get("media_url") or m.get("url")
                            if isinstance(u, str) and u.strip():
                                imgs.append(u.strip())

                # 2) Legacy/simple fields used in some responses
                candidate_keys = [
                    "image_url",
                    "images",
                    "image_urls",
                    "media_urls",
                ]
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

                # Get unique image URLs
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

                # Use first image or default
                img = urls[0] if urls else ""
                if not urls:
                    default_img = FLASK_APP_URL.rstrip("/") + "/static/defoult.webp"
                    urls = [default_img]
                    img = default_img
                    LOG.info(
                        "products_cmd: using default image for item %s -> %s",
                        item_id,
                        default_img,
                    )
                    uid = getattr(update.message.from_user, "id", None)
                    log_action(
                        "products_default_image_used",
                        user=f"tg:{uid}",
                        detail=f"item:{item_id}",
                    )

                # Normalize image URL
                normalized = None
                if img:
                    if img.startswith("http://") or img.startswith("https://"):
                        normalized = img
                    elif img.startswith("/"):
                        normalized = FLASK_APP_URL.rstrip("/") + img
                    else:
                        normalized = FLASK_APP_URL.rstrip("/") + "/" + img
                LOG.info(
                    "products_cmd: normalized image url: %s -> %s", img, normalized
                )

                # Validate image URL actually points to an image; otherwise skip photo
                if normalized and not _is_valid_image_url(normalized):
                    # If validation fails, keep the URL but log the issue and
                    # still try to send it so real product photos are not lost
                    LOG.info(
                        "products_cmd: image validation failed, sending anyway: %s",
                        normalized,
                    )
                    # Do not nullify normalized here

                # Build inline buttons
                buttons = [InlineKeyboardButton("👁️ Mahsulotni ko'rish", url=view_url)]
                markup = InlineKeyboardMarkup([buttons])

                # Send message with image and formatted text
                if normalized:
                    try:
                        # First try: URL directly
                        await update.message.reply_photo(
                            photo=normalized,
                            caption=text,
                            reply_markup=markup,
                            parse_mode="HTML",
                        )
                        uid = getattr(update.message.from_user, "id", None)
                        log_action(
                            "products_sent", user=f"tg:{uid}", detail=f"item:{item_id}"
                        )
                    except Exception as e_url:
                        # Second try: download bytes then send
                        try:
                            LOG.info(
                                "products_cmd: URL send failed, trying bytes for %s",
                                normalized,
                            )
                            rimg = requests.get(normalized, timeout=10)
                            rimg.raise_for_status()
                            content_type = (rimg.headers or {}).get(
                                "Content-Type", "image/jpeg"
                            )
                            data = rimg.content
                            await update.message.reply_photo(
                                photo=data,
                                caption=text,
                                reply_markup=markup,
                                parse_mode="HTML",
                            )
                            uid = getattr(update.message.from_user, "id", None)
                            log_action(
                                "products_sent_bytes",
                                user=f"tg:{uid}",
                                detail=f"item:{item_id}",
                            )
                        except Exception as e_bytes:
                            LOG.exception(
                                "Failed sending photo (url and bytes), fallback to text"
                            )
                            log_error(e_bytes, f"photo_send_bytes item:{item_id}")
                            await update.message.reply_text(
                                text, reply_markup=markup, parse_mode="HTML"
                            )
                            uid = getattr(update.message.from_user, "id", None)
                            log_action(
                                "products_sent_text_fallback",
                                user=f"tg:{uid}",
                                detail=f"item:{item_id}",
                            )
                else:
                    # no images: send default local image bytes if available
                    try:
                        default_path = (
                            LOGS_DIR.parent / "static" / "defoult.webp"
                        ).resolve()
                        with open(default_path, "rb") as f:
                            data = f.read()
                        await update.message.reply_photo(
                            photo=data,
                            caption=text,
                            reply_markup=markup,
                            parse_mode="HTML",
                        )
                        uid = getattr(update.message.from_user, "id", None)
                        log_action(
                            "products_sent_default_image",
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
            await products_cmd_new(update, context)
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
                r = requests.post(
                    FLASK_APP_URL.rstrip("/") + "/api/operator-chat/user/send",
                    json=payload,
                    timeout=10,
                )
                if r is not None and r.ok:
                    j = r.json() or {}
                    ack = j.get("message") or "Xabar operatorga yuborildi."
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
                    requests.post(
                        FLASK_APP_URL.rstrip("/") + "/api/chat/receive",
                        json=payload,
                        timeout=4,
                    )
                except Exception as e:
                    LOG.exception("chat/receive POST failed")
                    log_error(e, "chat/receive POST failed")

                # Call Uzbek AI endpoint and reply back to user
                ai_r = requests.post(
                    FLASK_APP_URL.rstrip("/") + "/api/chat/ai", json=payload, timeout=10
                )
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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    LOG.info("Telegram bot starting (polling)")

    # Robust polling loop with retry/backoff for transient errors (409 Conflict, timeouts)
    max_retries = int(os.environ.get("TELEGRAM_BOT_RETRIES", "5"))
    base_delay = float(os.environ.get("TELEGRAM_BOT_RETRY_DELAY", "5"))
    attempt = 0

    # Ensure an asyncio event loop is available in this thread. Newer Python
    # versions raise RuntimeError when no loop is set; python-telegram-bot
    # expects get_event_loop() to work. Create and set one if missing.
    try:
        import asyncio

        try:
            _loop = asyncio.get_event_loop()
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
                # Do not retry - return to let process exit/launcher or platform handle restart policy
                return

            # For other exceptions (timeouts, network errors), attempt graceful shutdown using asyncio
            try:
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
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
    main()
