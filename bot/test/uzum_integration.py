# Uzum products integration for telegram bot

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

# Load Uzum products data
def load_uzum_products():
    try:
        products_file = Path(__file__).parent / "test" / "bot_ready_products_1770480265230.json"
        if products_file.exists():
            with open(products_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logging.warning("Uzum products file not found")
            return None
    except Exception as e:
        logging.error(f"Error loading Uzum products: {e}")
        return None

UZUM_PRODUCTS = load_uzum_products()

async def products_cmd_uzum(update, context):
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
            # Fallback without markdown
            await update.message.reply_text(f"{title}\nNarx: {price}\nMavjud: {quantity} dona\nUzum: {uzum_url}")
        
        # Small delay between messages
        await asyncio.sleep(0.5)
    
    uid = getattr(update.message.from_user, "id", None)
    logging.info(f"products_cmd_uzum: showed {len(available_products)} products to user {uid}")

# Add this to your main telegram_bot.py file and integrate with existing handlers
