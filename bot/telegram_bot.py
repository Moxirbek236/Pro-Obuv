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
import sys
import signal

load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))
# Also try to load local test config if available
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.test'))

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

import psycopg2
from psycopg2.extras import RealDictCursor

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

# Backend API URL - can be localhost for development or production URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://safety.uz")
# Remove trailing slash if present
BACKEND_URL = BACKEND_URL.rstrip('/')

LOG = logging.getLogger("telegram_bot")

# Database connection helper
def get_db_conn():
    try:
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            return None
        conn = psycopg2.connect(dsn, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        LOG.error(f"Database connection error: {e}")
        return None

def check_uzum_setting():
    """Check if Uzum Market mode is enabled in the database"""
    conn = get_db_conn()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM site_settings WHERE key = 'use_uzum_market_bot'")
            row = cur.fetchone()
            if row and str(row['value']).lower() == 'true':
                return True
        return False
    except Exception as e:
        LOG.error(f"Error checking uzum setting: {e}")
        return False
    finally:
        conn.close()

# Uzum products will be fetched dynamically from the backend API
UZUM_PRODUCTS = None

# Ensure logs directory exists and define action/error log paths
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_LOG = LOGS_DIR / "telegram_actions.txt"
ERROR_LOG = LOGS_DIR / "telegram_errors.txt"


def log_error(error: Exception, context: str = "") -> None:
    """Log an error without sensitive data."""
    try:
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] ERROR in {context}: {type(error).__name__}: {str(error)}\n"
        
        # Only log to file, not console (to avoid token exposure)
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(error_msg)
        
        # Don't log to console to avoid sensitive data
    except Exception:
        pass


def log_action(action: str, user: str = "unknown", detail: str = "") -> None:
    """Log user actions without sensitive data."""
    try:
        timestamp = datetime.now().isoformat()
        # Remove potential sensitive data from detail
        safe_detail = detail
        if 'token' in detail.lower():
            safe_detail = "[REDACTED]"
        
        log_entry = f"[{timestamp}] ACTION: {action} | USER: {user} | DETAIL: {safe_detail}\n"
        
        # Only log to file
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass


async def _send_main_keyboard(update: "Update"):
    """Yagona joyda asosiy klaviaturani yuborish.
    
    Settingga qarab tugmalar o'zgaradi.
    """
    try:
        use_uzum = check_uzum_setting()
        
        if use_uzum:
            # Uzum rejimi: ["mahsulotlar", "ai bilan suhbat", "operatorga yozish"]
            kb = [
                [KeyboardButton("mahsulotlar")],
                [
                    KeyboardButton("ai bilan suhbat"),
                    KeyboardButton("operatorga yozish"),
                ],
            ]
        else:
            # Oddiy rejim
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
    """Show Uzum products by fetching from the Flask API - already grouped by COLOR from backend"""
    try:
        # Fetch from Flask API (uses BACKEND_URL which can be localhost or production)
        api_url = f"{BACKEND_URL}/api/products?per_page=100"
        response = requests.get(api_url, timeout=20)
        if response.status_code != 200:
            await update.message.reply_text("❌ Mahsulotlarni yuklashda xatolik yuz berdi (Backend API error)")
            return
        
        res_data = response.json()
        products = res_data.get("data", [])
        
        if not products:
            await update.message.reply_text("❌ Hozirda mahsulotlar topilmadi")
            return
        
        # Backend API already groups by color, so we can directly display products
        # Each product in the list represents one color variant with all its sizes
        for i, product in enumerate(products):
            # Get product details
            name = product.get("name", "Noma'lum mahsulot")
            price = f"{product.get('price', 0):,} UZS".replace(',', ' ')
            available = "Mavjud ✅" if product.get("available") else "Sotuvda yo'q ❌"
            parent_id = product.get("productId", "")
            sizes = product.get("size_list", [])
            colors = product.get("color_list", [])
            image_url = product.get("image_url", "")
            
            # Sort sizes for better display
            try:
                sorted_sizes = sorted(sizes, key=lambda x: (
                    int(''.join(filter(str.isdigit, str(x)))) if any(c.isdigit() for c in str(x)) else 999,
                    str(x)
                ))
            except:
                sorted_sizes = sizes
            
            # Create Uzum URL
            uzum_url = f"https://uzum.uz/product/{parent_id}" if parent_id else "https://uzum.uz"
            
            # Build message text - show product name, color (if any), and all sizes
            message = f"🛍️ *{name}*\n"
            message += f"💰 Narx: {price}\n"
            message += f"📊 Holati: {available}\n"
            
            # Show sizes if available
            if sorted_sizes:
                sizes_str = ', '.join(map(str, sorted_sizes))
                message += f"📏 O'lchamlar: {sizes_str}\n"
            
            message += f"\n🔗 [Uzum dan sotib olish]({uzum_url})"
            
            try:
                # Try to send with image first
                if image_url and image_url.startswith('http'):
                    # Append /original.jpg if not already present
                    final_img = image_url
                    if 'uzum.uz' in final_img and not final_img.endswith('.jpg'):
                        final_img = final_img.rstrip('/') + '/original.jpg'

                    try:
                        await update.message.reply_photo(
                            photo=final_img,
                            caption=message,
                            parse_mode='Markdown'
                        )
                    except Exception as photo_error:
                        # If photo fails, send text only
                        await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    # No valid image URL, send text only
                    await update.message.reply_text(message, parse_mode='Markdown')
                    
            except Exception as e:
                log_error(e, f"products_cmd_uzum product {i}")
                await update.message.reply_text(f"{name}\n{price}\n{available}\n{uzum_url}")
            
            # Small delay between messages
            await asyncio.sleep(0.3)
        
        uid = getattr(update.message.from_user, "id", None)
        log_action("products_cmd_uzum", user=f"tg:{uid}", detail=f"showed {len(products)} color variants via API")
    except Exception as e:
        log_error(e, "products_cmd_uzum failure")
        print(f"❌ Product fetch error: {e}")  # Add this debug print
        await update.message.reply_text(f"❌ Mahsulotlarni yuklashda texnik xatolik: {e}")


async def products_cmd_new(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Original products command - fetch from Flask API or Uzum depending on setting"""
    try:
        use_uzum = check_uzum_setting()
        
        if use_uzum:
            # If Uzum is on, directly show Uzum products
            await products_cmd_uzum(update, context)
            return

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
        log_error(e, "products_cmd_new")
        await update.message.reply_text("Xatolik yuz berdi.")
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
        if text in ("/products", "🛒 Mahsulotlar", "mahsulotlar"):
            await products_cmd_new(update, context)
            return
        if text in ("/uzum", "🛍️ Uzum mahsulotlar"):
            await products_cmd_uzum(update, context)
            return
        if text in ("/ai", "🤖 AI bilan suhbat", "ai bilan suhbat"):
            await update.message.reply_text("AI rejimi yoqildi. Savollaringizni yozing.")
            return
        if text in ("/operator", "👨‍💼 Operator bilan suhbat", "operatorga yozish"):
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
        api_url = f"{BACKEND_URL}/api/chat/receive"
        response = requests.post(
            api_url,
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
    # Prioritize test token if available to avoid conflicts with production
    token = os.environ.get("TELEGRAM_BOT_TOKEN_TEST") or os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not Updater or not token:
        if "IMPORT_ERROR" in globals() and IMPORT_ERROR is not None:
            LOG.error("python-telegram-bot import failed: %s", IMPORT_ERROR)
        else:
            LOG.error("python-telegram-bot not installed or TELEGRAM_BOT_TOKEN not set")
        return False

    # Build application with better timeout settings
    app = None
    try:
        from telegram.request import HTTPXRequest
        # Increase timeouts for better connection handling
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0
        )
        app = ApplicationBuilder().token(token).request(request).build()
        print(f"✅ HTTPXRequest configured with 30s timeouts (Using {'TEST' if os.environ.get('TELEGRAM_BOT_TOKEN_TEST') else 'PROD'} token)")
    except Exception as e:
        print(f"⚠️  HTTPXRequest failed: {e}")
        try:
            app = ApplicationBuilder().token(token).build()
            print("✅ Using default ApplicationBuilder")
        except Exception as e:
            LOG.exception("Failed to create Application: %s", e)
            return False

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CommandHandler("products", products_cmd_new))
    app.add_handler(CommandHandler("uzum", products_cmd_uzum))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    LOG.info("Telegram bot starting (polling)")

    # Start polling with better error handling
    try:
        app.run_polling(
            drop_pending_updates=True,
            timeout=30
        )
        return True
    except Exception as exc:
        LOG.error("Application.run_polling failed: %s", str(exc))
        if "Conflict" in str(exc) or "getUpdates" in str(exc):
            msg = (
                "\n🔴 CRITICAL CONFLICT ERROR: The bot token is already in use by another instance!\n"
                "   Likely the production bot on Render is running.\n\n"
                "   SOLUTIONS:\n"
                "   1. Stop the Render service (Scale to 0)\n"
                "   2. Use a TEST TOKEN for local dev:\n"
                "      Create a file 'bot/.env.test' with:\n"
                "      TELEGRAM_BOT_TOKEN_TEST=your_test_token_here\n"
            )
            print(msg)
            LOG.error(msg)
        return False


if __name__ == "__main__":
    # Configure logging to exclude sensitive data
    logging.basicConfig(
        level=logging.WARNING,  # Only show warnings and errors
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Disable specific loggers that might contain sensitive info
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n📡 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
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
    
    @app.route('/keep-alive')
    def keep_alive():
        """Render serverini tirik saqlash uchun"""
        return {
            "status": "active", 
            "service": "telegram-bot",
            "timestamp": datetime.now().isoformat(),
            "uptime": "Bot is running and processing messages"
        }
    
    @app.route('/ping-self')
    def ping_self():
        """Botni o'ziga ping qilish"""
        try:
            # Botni o'ziga tekshirish
            if 'app' in globals() and app:
                bot_info = app.bot.get_me()
                return {
                    "status": "success",
                    "bot_name": bot_info.username,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Start Flask server in background thread
    port = int(os.environ.get('BOT_PORT', 10001))
    
    def run_flask():
        # Disable Flask warnings in production
        app.config['ENV'] = 'production'
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    time.sleep(2)
    
    print(f"Starting Telegram bot, Flask on port {port}")
    
    # Run Telegram bot in main thread (this solves event loop issue)
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Bot error: {e}")
