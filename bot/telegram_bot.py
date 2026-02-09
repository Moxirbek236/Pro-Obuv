"""Render-optimized Telegram bot consuming Safety.uz Backend API."""

import os
import logging
import requests
import json
import asyncio
import sys
import signal
import threading
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

# Load environment variables from local .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "https://safety.uz").rstrip('/')
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

try:
    from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
        CallbackQueryHandler,
        ApplicationHandlerStop
    )
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
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ACTION_LOG = LOGS_DIR / "telegram_actions.txt"
ERROR_LOG = LOGS_DIR / "telegram_errors.txt"

def log_error(error: Exception, context: str = "") -> None:
    try:
        timestamp = datetime.now().isoformat()
        error_msg = f"[{timestamp}] ERROR in {context}: {type(error).__name__}: {str(error)}\n"
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write(error_msg)
        print(error_msg) # Also print to stdout
    except Exception:
        pass

def log_action(action: str, user: str = "unknown", detail: str = "") -> None:
    try:
        timestamp = datetime.now().isoformat()
        safe_detail = detail.replace(TELEGRAM_BOT_TOKEN, "[REDACTED]") if TELEGRAM_BOT_TOKEN else detail
        log_entry = f"[{timestamp}] ACTION: {action} | USER: {user} | DETAIL: {safe_detail}\n"
        with open(ACTION_LOG, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

# --- API Helpers ---

def api_get(endpoint: str, params: dict = None) -> dict:
    try:
        url = f"{BACKEND_URL}{endpoint}"
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        LOG.error(f"API GET {url} failed: {resp.status_code}")
        return None
    except Exception as e:
        LOG.error(f"API GET {endpoint} error: {e}")
        return None

def api_post(endpoint: str, data: dict = None) -> dict:
    try:
        url = f"{BACKEND_URL}{endpoint}"
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code in (200, 201):
            return resp.json()
        LOG.error(f"API POST {url} failed: {resp.status_code}")
        return None
    except Exception as e:
        LOG.error(f"API POST {endpoint} error: {e}")
        return None

# --- Bot Handlers ---

async def start(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Handle /start command"""
    try:
        await update.message.reply_text(
            "Assalomu alaykum! Safety.uz botiga xush kelibsiz.\n"
            "Mahsulotlarni ko'rish uchun quyidagi tugmalardan foydalaning."
        )
        await show_main_menu(update)
        uid = getattr(update.message.from_user, "id", None)
        log_action("start_command", user=f"tg:{uid}", detail="start command sent")
    except Exception as e:
        log_error(e, "start")

async def show_main_menu(update: "Update"):
    kb = [
        [KeyboardButton("🛒 Mahsulotlar"), KeyboardButton("🛍️ Uzum Mahsulotlar")],
        [KeyboardButton("🤖 AI Chat"), KeyboardButton("👨‍💼 Operator")],
        [KeyboardButton("ℹ️ Biz haqimizda")]
    ]
    markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text("Assalomu alaykum, Xizmat turini tanlang:", reply_markup=markup)

async def handle_categories(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Fetch categories from backend and show as keyboard"""
    try:
        result = api_get("/api/bot/categories")
        if result and result.get("success"):
            categories = result.get("categories", [])
            if not categories:
                await update.message.reply_text("Hozircha kategoriyalar mavjud emas.")
                return

            # Dynamic keyboard for categories
            # Show 2 per row
            kb = []
            row = []
            for cat in categories:
                # Assuming cat has 'name' and 'id'
                # Use name for button text
                cat_name = cat.get("name", "Unknown")
                row.append(KeyboardButton(cat_name))
                if len(row) == 2:
                    kb.append(row)
                    row = []
            if row:
                kb.append(row)
            
            kb.append([KeyboardButton("🔙 Asosiy menyu")])
            markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
            await update.message.reply_text("Kategoriyani tanlang:", reply_markup=markup)
        else:
            await update.message.reply_text("Kategoriyalarni yuklashda xatolik yuz berdi. Backend bilan aloqa yo'q.")
    except Exception as e:
        log_error(e, "handle_categories")
        await update.message.reply_text("Tizim xatoligi.")

async def show_products_by_category(update: "Update", category_name: str):
    """Fetch products for category"""
    try:
        # We need the ID usually, but if category name is unique we can use it. 
        # API expects 'category' param which matches 'type' in DB.
        # Assuming category_name matches the 'name' returned by /categories, which matches 'type'.
        
        # If the category name is localized (e.g. Cyrillic), we might need to map it back if backend expects slug.
        # But backend logic seemed to use the type/name directly. Let's send the text as is.
        # Ideally we should store ID in button but ReplyKeyboard only sends text.
        # For better UX we should use InlineKeyboard but user flow asked for buttons.
        # Let's try sending the name as 'category'.
        
        await update.message.reply_text(f"🔍 {category_name} bo'yicha mahsulotlar izlanmoqda...")
        
        # Map known categories names to IDs if needed (simple fallback)
        cat_id = category_name
        if category_name == 'Спецодежда': cat_id = 'specodezhda'
        elif category_name == 'Спецобувь': cat_id = 'obuv'

        result = api_get("/api/bot/products", {"category": cat_id, "limit": 10})
        
        if result and result.get("success"):
            products = result.get("products", [])
            if not products:
                await update.message.reply_text("Bu kategoriyada mahsulotlar topilmadi.")
                return
            
            for p in products:
                name = p.get('name', 'Nomsiz')
                price = p.get('price', 0)
                desc = p.get('description', '')[:100]
                image = p.get('image')
                
                caption = f"🛡 *{name}*\n\n📝 {desc}...\n\n💰 Narxi: {price:,.0f} so'm"
                
                # Inline button to order or view details
                # callback_data limit is 64 chars
                params = InlineKeyboardMarkup([[InlineKeyboardButton("Buyurtma berish", callback_data=f"order_{p.get('id')}") ]])

                if image and image.startswith('http'):
                    try:
                        await update.message.reply_photo(photo=image, caption=caption, parse_mode='Markdown', reply_markup=params)
                    except Exception:
                         await update.message.reply_text(caption, parse_mode='Markdown', reply_markup=params)
                else:
                    await update.message.reply_text(caption, parse_mode='Markdown', reply_markup=params)
                
                await asyncio.sleep(0.3) 
        else:
             await update.message.reply_text("Mahsulotlarni yuklashda xatolik.")

    except Exception as e:
        log_error(e, f"show_products_by_category: {category_name}")
        await update.message.reply_text("Xatolik yuz berdi.")

async def handle_uzum_products(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    try:
        await update.message.reply_text("🛍️ Uzum Market mahsulotlari yuklanmoqda...")
        result = api_get("/api/bot/uzum/products")
        if result and result.get("success"):
             products = result.get("products", [])
             # Filter available
             available = [p for p in products if p.get('skuList') or p.get('totalQuantity', 0) > 0][:10]
             
             if not available:
                 await update.message.reply_text("Uzum da mavjud mahsulotlar topilmadi.")
                 return

             for p in available:
                 title = p.get('title')
                 price = p.get('priceRange') or p.get('price') # Adjust based on actual data structure
                 url = p.get('url') or f"https://uzum.uz/product/{p.get('id')}"
                 img = p.get('previewImage') or p.get('image')
                 
                 msg = f"🛍 *{title}*\n💰 {price}\n🔗 [Uzum da ko'rish]({url})"
                 
                 if img:
                     try:
                        await update.message.reply_photo(photo=img, caption=msg, parse_mode='Markdown')
                     except:
                        await update.message.reply_text(msg, parse_mode='Markdown')
                 else:
                     await update.message.reply_text(msg, parse_mode='Markdown')
                 await asyncio.sleep(0.3)
        else:
             await update.message.reply_text("Uzum ma'lumotlarini olishda xatolik.")
    except Exception as e:
        log_error(e, "handle_uzum_products")

async def chat_with_backend(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    """Handle generic messages - maybe chat or category selection"""
    txt = update.message.text
    
    if txt == "🔙 Asosiy menyu":
        await show_main_menu(update)
        return
        
    if txt == "🛒 Mahsulotlar":
        await handle_categories(update, context)
        return
        
    if txt == "🛍️ Uzum Mahsulotlar":
        await handle_uzum_products(update, context)
        return
        
    # Check if text is a category
    # Simple check: fetch categories and see if txt is in them
    # Optimally we cache categories, but for now we fetch (or hardcode check)
    # If users type random text, we send to AI Chat API
    
    # Try chat API first
    payload = {
        "sender": f"tg:{update.message.from_user.id}",
        "text": txt,
        "sender_name": update.message.from_user.full_name
    }
    
    # Check if it matches a category?
    # Let's just assume if they utilize the menu, it's exact match.
    # If they type "Спецодежда" manually, it matches.
    if txt in ["Спецодежда", "Спецобувь", "Bosh kiyimlar", "Qo'lqoplar"]: # Add more if known
         await show_products_by_category(update, txt)
         return
    
    # Else send to chat
    # If AI Chat mode is implied or requested
    if txt in ["🤖 AI Chat", "/ai"]:
         await update.message.reply_text("AI Chat rejimi. Savolingizni yozing...")
         return
         
    # Default: Echo or Send to Backend Chat
    try:
        # Check if we should treat this as a category selection or search
        # We can implement a search later.
        # For now, let's just echo usage or send to chat API
        # Actually, let's treat any unknown text as search or chat
        pass 
    except Exception:
        pass
        
    # For now, simplistic response
    # await update.message.reply_text(f"Siz yozdingiz: {txt}\nMenyudan foydalaning.")

async def handle_callback(update: "Update", context: "ContextTypes.DEFAULT_TYPE"):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("order_"):
        pid = data.split("_")[1]
        await query.message.reply_text(f"Mahsulot (ID: {pid}) savatchaga qo'shish uchun miqdorni yozing (Hozircha faqat ko'rish rejimi).")
        # Here logic would be: Ask quantity -> POST /api/bot/order

# --- Main ---

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return

    print(f"🚀 Starting Bot. Backend: {BACKEND_URL}")
    
    # Configure request with timeouts as suggested by error message
    try:
        from telegram.request import HTTPXRequest
        request = HTTPXRequest(
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0
        )
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).request(request).build()
    except Exception:
        # Fallback if import fails or old version
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_backend))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log the error and handle specific cases."""
        # Check if error is Conflict
        error_str = str(context.error)
        
        if "Conflict" in error_str:
            print("🔴 Conflict detected: Another bot instance is running. Shutting down this instance.")
            # We must stop the application to avoid loop
            # Raising SystemExit or calling stop() might work depending on context, 
            # but usually the polling loop will catch it.
            # Best is to let it crash gracefully.
            return

        LOG.error("Exception while handling an update:", exc_info=context.error)

    application.add_error_handler(error_handler)

    print("🤖 Polling started...")
    
    # Run polling with specific exception handling
    try:
        # allowed_updates=Update.ALL_TYPES makes sure we get everything
        # drop_pending_updates=True clears old queue
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        error_str = str(e)
        if "Conflict" in error_str:
             print("🔴 Bot stopped due to conflict (Multiple instances running). This is normal during deployment.")
        else:
             print(f"❌ Polling error: {e}")
             # Log full trace for other errors
             LOG.exception("Detailed polling error:")

# --- Flask for Health Check (Render) ---
app = Flask(__name__)
@app.route('/')
def health(): return "Bot is healthy"

def run_flask():
    port = int(os.environ.get('PORT', 5001)) # Different port than backend if local
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Main loop error: {e}")
