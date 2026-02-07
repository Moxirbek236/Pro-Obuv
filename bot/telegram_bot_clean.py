"""Simple Telegram bot integration with Uzum products.
This script integrates Uzum seller API products with Telegram bot.
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
import asyncio

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
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_LOG = LOGS_DIR / "telegram_actions.txt"
ERROR_LOG = LOGS_DIR / "telegram_errors.txt"


def log_error(error: Exception, context: str = "") -> None:
    """Log an error with traceback and context."""
    try:
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] ERROR in {context}: {type(error).__name__}: {error}\n"
        error_msg += f"Traceback: {traceback.format_exc()}\n"
        
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(error_msg)
        
        LOG.error(f"Error logged: {context} - {error}")
    except Exception:
        LOG.exception("Failed to log error")


def log_action(action: str, user: str = "unknown", detail: str = "") -> None:
    """Log user actions for analytics."""
    try:
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] ACTION: {action} | USER: {user} | DETAIL: {detail}\n"
        
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        LOG.info(f"Action logged: {action} by {user}")
    except Exception:
        LOG.exception("Failed to log action")


async def _send_main_keyboard(update: "Update"):
    """Yagona joyda asosiy klaviaturani yuborish.

    Har doim quyidagi tugmalar ko'rinadi:
    - Mahsulotlar
    - Uzum mahsulotlar
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
    """Handle /start command."""
    try:
        await update.message.reply_text(
            "Assalomu alaykum! Mahsulotlar uchun /products yoki '🛒 Mahsulotlar' tugmasini bosing."
        )
        await _send_main_keyboard(update)
        uid = getattr(update.message.from_user, "id", None)
        log_action("start_command", user=f"tg:{uid}", detail="start command sent")
    except Exception as e:
        log_error(e, "start")


async def test_cmd(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Simple test command to verify bot is working"""
    try:
        await update.message.reply_text("✅ Bot is working! Uzum products integrated")
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


async def handle_message(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Matnli xabarlar uchun handler."""
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        uid = getattr(update.message.from_user, "id", None)
        sender = f"tg:{uid}" if uid is not None else "tg:unknown"

        # Log incoming chat text
        try:
            log_action("incoming_message", user=sender, detail=text)
        except Exception:
            LOG.exception("Failed to log incoming message")

        # Maxsus tugmalarni tekshiramiz
        if text in ("/products", "🛒 Mahsulotlar"):
            await products_cmd_new(update, context)
            return
        if text in ("/uzum", "🛍️ Uzum mahsulotlar"):
            await products_cmd_uzum(update, context)
            return
        if text in ("/ai", "🤖 AI bilan suhbat"):
            await update.message.reply_text("AI rejimi yoqildi. Savollaringizni yozing.")
            return
        if text in ("/operator", "👨‍💼 Operator bilan suhbat"):
            await update.message.reply_text("Operator bilan suhbat rejimi yoqildi.")
            return

        # Send to Flask backend for processing
        payload = {
            "sender": sender,
            "text": text,
            "source": "telegram",
        }

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

        # Send to backend
        response = requests.post(
            "http://127.0.0.1:5000/api/chat/receive",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            reply_text = result.get("reply", "Kechirasiz, javob olinmadi.")
            await update.message.reply_text(reply_text)
        else:
            await update.message.reply_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

    except Exception as e:
        log_error(e, "handle_message")
        await update.message.reply_text("Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")


def main():
    """Botni ishga tushirish."""
    if not Updater or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        if "IMPORT_ERROR" in globals() and IMPORT_ERROR is not None:
            LOG.error("python-telegram-bot import failed: %s", IMPORT_ERROR)
        else:
            LOG.error("python-telegram-bot not installed or TELEGRAM_BOT_TOKEN not set")
        return

    # Build application
    app = None
    try:
        from telegram.request import HTTPXRequest
        request = HTTPXRequest()
        app = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).request(request).build()
    except Exception:
        try:
            app = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
        except Exception as e:
            LOG.exception("Failed to create Application: %s", e)
            return

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CommandHandler("products", products_cmd_new))
    app.add_handler(CommandHandler("uzum", products_cmd_uzum))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    LOG.info("Telegram bot starting (polling)")

    # Start polling
    try:
        app.run_polling()
    except Exception as exc:
        LOG.error("Application.run_polling failed: %s", str(exc))
        if "Conflict" in str(exc) or "getUpdates" in str(exc):
            LOG.error("Another bot instance might be running. Please stop other instances.")


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
