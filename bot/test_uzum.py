"""Test bot without Telegram API - just for testing Uzum products functionality"""

import asyncio
import json
from pathlib import Path

# Load Uzum products
def load_uzum_products():
    try:
        products_file = Path(__file__).parent / "test" / "bot_products_fixed_1770628828863.json"
        if products_file.exists():
            with open(products_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("Uzum products file not found")
            return None
    except Exception as e:
        print(f"Error loading Uzum products: {e}")
        return None

# Simulate bot message
class MockUpdate:
    def __init__(self):
        self.message = MockMessage()

class MockMessage:
    def __init__(self):
        self.from_user = MockUser()

class MockUser:
    def __init__(self):
        self.id = 12345

# Mock reply function
async def mock_reply_text(text, parse_mode=None):
    print(f"\n📨 BOT MESSAGE:")
    print("=" * 50)
    print(text)
    print("=" * 50)
    print()

async def mock_reply_photo(photo, caption, parse_mode=None):
    print(f"\n🖼️ BOT MESSAGE WITH IMAGE:")
    print(f"🖼️ Image: {photo}")
    print("=" * 50)
    print(caption)
    print("=" * 50)
    print()

# Uzum products command (copied from main bot)
async def products_cmd_uzum():
    """Show Uzum products from seller API data"""
    UZUM_PRODUCTS = load_uzum_products()
    
    if not UZUM_PRODUCTS or not UZUM_PRODUCTS.get("products"):
        await mock_reply_text("❌ Mahsulotlar ma'lumotlari topilmadi")
        return
    
    products = UZUM_PRODUCTS["products"]
    available_products = [p for p in products if p.get("totalQuantity", 0) > 0]
    
    if not available_products:
        await mock_reply_text("❌ Hozirda mavjud mahsulotlar yo'q")
        return
    
    print(f"📊 Found {len(available_products)} available products out of {len(products)} total")
    
    # Show first 5 available products for testing
    for i, product in enumerate(available_products[:5]):
        title = product.get("title", "Noma'lum mahsulot")
        price = product.get("priceRange", "Narx noma'lum")
        quantity = product.get("totalQuantity", 0)
        brand = product.get("brand", "Noma'lum")
        product_id = product.get("id", "")
        sizes = product.get("sizes", [])
        colors = product.get("colors", [])
        image_url = product.get("image", "")
        
        # Create Uzum URL
        if product_id:
            uzum_url = f"https://uzum.uz/product/{product_id}"
        else:
            uzum_url = product.get("uzumMarketUrl", "https://uzum.uz")
        
        # Build message text
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
            # Try to send with image first
            if image_url and image_url.startswith('http'):
                await mock_reply_photo(
                    photo=image_url,
                    caption=message,
                    parse_mode='Markdown'
                )
            else:
                # No valid image URL, send text only
                await mock_reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            print(f"Error sending product {i}: {e}")
            # Fallback without markdown and without image
            fallback_msg = f"{title}\nNarx: {price}\nMavjud: {quantity} dona\nBrend: {brand}"
            if sizes: fallback_msg += f"\nO\'lchamlar: {', '.join(sizes)}"
            if colors: fallback_msg += f"\nRanglar: {', '.join(colors)}"
            fallback_msg += f"\nUzum: {uzum_url}"
            await mock_reply_text(fallback_msg)
        
        # Small delay between messages
        await asyncio.sleep(0.5)

async def main():
    print("🤖 Uzum Bot Test Mode")
    print("Testing Uzum products functionality without Telegram API...")
    print()
    
    await products_cmd_uzum()
    
    print("\n✅ Test completed!")
    print("If messages look good, the bot functionality is working correctly.")
    print("The issue is likely with Telegram API connection.")

if __name__ == "__main__":
    asyncio.run(main())
