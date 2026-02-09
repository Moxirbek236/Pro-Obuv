"""Render-optimized Telegram bot with Uzum products integration."""

import os
import logging
import requests
from datetime import datetime
import traceback
from pathlib import Path
import time
from dotenv import load_dotenv
import threading
from flask import Flask
import json
import asyncio
import sys
import signal

load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))

try:
    from telegram import Update, Bot, InputMediaPhoto, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    )
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    Updater = True
    IMPORT_ERROR = None
except Exception:
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
        products_file = Path(__file__).parent / "test" / "bot_products_fixed_1770482210682.json"
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

# Ensure logs directory exists
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_LOG = LOGS_DIR / "telegram_actions.txt"
ERROR_LOG = LOGS_DIR / "telegram_errors.txt"

def log_error(error: Exception, context: str = "") -> None:
    """Log an error without sensitive data."""
    try:
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] ERROR in {context}: {type(error).__name__}: {str(error)}\n"
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(error_msg)
    except Exception:
        pass

def log_action(action: str, user: str = "unknown", detail: str = "") -> None:
    """Log user actions without sensitive data."""
    try:
        timestamp = datetime.now().isoformat()
        safe_detail = detail
        if 'token' in detail.lower():
            safe_detail = "[REDACTED]"
        log_entry = f"[{timestamp}] ACTION: {action} | USER: {user} | DETAIL: {safe_detail}\n"
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

async def _send_main_keyboard(update: "Update"):
    """Send main keyboard."""
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
    """Test command."""
    try:
        await update.message.reply_text("✅ Bot is working! Uzum products integrated")
        uid = getattr(update.message.from_user, "id", None)
        log_action("test_command", user=f"tg:{uid}", detail="test command sent")
    except Exception as e:
        log_error(e, "test handler")

async def products_cmd_uzum(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Show Uzum products."""
    if not UZUM_PRODUCTS or not UZUM_PRODUCTS.get("products"):
        await update.message.reply_text("❌ Mahsulotlar ma'lumotlari topilmadi")
        return
    
    products = UZUM_PRODUCTS["products"]
    available_products = [p for p in products if p.get("totalQuantity", 0) > 0]
    
    if not available_products:
        await update.message.reply_text("❌ Hozirda mavjud mahsulotlar yo'q")
        return
    
    for i, product in enumerate(available_products[:10]):
        title = product.get("title", "Noma'lum mahsulot")
        price = product.get("priceRange", "Narx noma'lum")
        quantity = product.get("totalQuantity", 0)
        brand = product.get("brand", "Noma'lum")
        product_id = product.get("id", "")
        sizes = product.get("sizes", [])
        colors = product.get("colors", [])
        image_url = product.get("image", "")
        
        if product_id:
            uzum_url = f"https://uzum.uz/product/{product_id}"
        else:
            uzum_url = product.get("uzumMarketUrl", "https://uzum.uz")
        
        message = f"🛍️ *{title}*\n"
        message += f"💰 Narx: {price}\n"
        message += f"📊 Mavjud: {quantity} dona\n"
        message += f"🏷️ Brend: {brand}"
        
        if sizes:
            message += f"\n📏 O\'lchamlar: {', '.join(sizes)}"
        
        if colors:
            message += f"\n🎨 Ranglar: {', '.join(colors)}"
        
        message += f"\n🔗 [Uzum da ko'rish]({uzum_url})"
        
        try:
            if image_url and image_url.startswith('http'):
                try:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=message,
                        parse_mode='Markdown'
                    )
                except Exception:
                    await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            log_error(e, f"products_cmd_uzum product {i}")
            fallback_msg = f"{title}\nNarx: {price}\nMavjud: {quantity} dona\nBrend: {brand}"
            if sizes: fallback_msg += f"\nO\'lchamlar: {', '.join(sizes)}"
            if colors: fallback_msg += f"\nRanglar: {', '.join(colors)}"
            fallback_msg += f"\nUzum: {uzum_url}"
            await update.message.reply_text(fallback_msg)
        
        await asyncio.sleep(0.5)
    
    uid = getattr(update.message.from_user, "id", None)
    log_action("products_cmd_uzum", user=f"tg:{uid}", detail=f"showed {len(available_products)} products")

async def products_cmd_new(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Original products command."""
    try:
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
    """Handle text messages."""
    try:
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        uid = getattr(update.message.from_user, "id", None)
        sender = f"tg:{uid}" if uid is not None else "tg:unknown"

        try:
            log_action("incoming_message", user=sender, detail=text)
        except Exception:
            pass

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

        # Send to Flask backend
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
    """Start the bot."""
    if not Updater or not os.environ.get("TELEGRAM_BOT_TOKEN"):
        if "IMPORT_ERROR" in globals() and IMPORT_ERROR is not None:
            LOG.error("python-telegram-bot import failed: %s", IMPORT_ERROR)
        else:
            LOG.error("python-telegram-bot not installed or TELEGRAM_BOT_TOKEN not set")
        return False

    # Build application
    app = None
    try:
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0
        )
        app = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).request(request).build()
        print("✅ HTTPXRequest configured with 30s timeouts")
    except Exception as e:
        print(f"⚠️  HTTPXRequest failed: {e}")
        try:
            app = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
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
    
    # Add global error handler
    from telegram.ext import ApplicationHandlerStop
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors gracefully"""
        error = context.error
        error_str = str(error)
        
        print(f"🔍 Error Handler: {error_str}")
        
        if "Conflict" in error_str or "getUpdates" in error_str:
            print("⚠️  Bot conflict detected - this is normal on Render")
            print("🔄 Bot will continue running...")
            return  # Don't crash the bot
        elif "Timed out" in error_str or "timeout" in error_str.lower():
            print("⏰ Timeout occurred - bot will retry")
            return
        elif "Network" in error_str or "Connection" in error_str:
            print("🌐 Network error - bot will retry")
            return
        else:
            print(f"❌ Unknown error: {error_str}")
            # Don't crash the bot, just log it
            return
    
    app.add_error_handler(error_handler)
    print("✅ Error handler registered")

    print("🤖 Starting Telegram bot polling...")
    
    # Start polling with conflict handling
    try:
        app.run_polling(
            drop_pending_updates=True,
            timeout=30
        )
        return True
    except Exception as exc:
        error_msg = str(exc)
        if "Conflict" in error_msg or "getUpdates" in error_msg:
            print("⚠️  Another bot instance detected. This is normal on Render.")
            print("🔄 Bot will continue running...")
            return True  # Don't exit the bot
        else:
            print(f"❌ Error: {error_msg}")
            return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # Change from WARNING to INFO to see more
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Keep telegram warnings but allow error handlers to work
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Kill existing processes first
    print("🔄 Checking for existing bot processes...")
    try:
        import subprocess
        import signal
        import platform
        
        system = platform.system().lower()
        
        if system == "windows":
            # Windows process cleanup
            try:
                # Kill Python processes
                result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                      capture_output=True, text=True)
                print("✅ Windows processes terminated")
            except:
                pass
        else:
            # Linux/Unix process cleanup
            try:
                # Kill existing Python processes with telegram_bot
                result = subprocess.run(['pkill', '-f', 'python.*telegram_bot'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Existing bot processes terminated")
                time.sleep(2)  # Wait for processes to stop
            except:
                pass
            
            # Kill processes on our port
            port = int(os.environ.get('PORT', 10000))
            try:
                result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            print(f"✅ Killed process {pid} on port {port}")
                        except:
                            pass
                    time.sleep(1)
            except:
                pass
            
            # Final check - force kill if needed
            try:
                subprocess.run(['pkill', '-9', '-f', 'python.*telegram_bot'], 
                              capture_output=True, text=True)
            except:
                pass
            
    except Exception as e:
        print(f"⚠️  Process cleanup warning: {e}")
    
    print("🚀 Starting fresh bot instance...")
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n📡 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create Flask app for health checks
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
        """Render keep-alive endpoint"""
        return {
            "status": "active", 
            "service": "telegram-bot",
            "timestamp": datetime.now().isoformat(),
            "uptime": "Bot is running and processing messages"
        }
    
    @app.route('/ping-self')
    def ping_self():
        """Bot self-ping"""
        try:
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Start Flask server
    port = int(os.environ.get('PORT', 10000))
    
    def run_flask():
        app.config['ENV'] = 'production'
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    time.sleep(2)
    print(f"Starting Telegram bot, Flask on port {port}")
    
    # Run bot
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Bot error: {e}")
