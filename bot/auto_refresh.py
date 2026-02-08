"""Auto-refresh Uzum products and update bot"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
import time

def load_current_products():
    """Load current Uzum products"""
    try:
        products_file = Path(__file__).parent / "test" / "bot_products_fixed_1770482210682.json"
        if products_file.exists():
            with open(products_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception:
        return None

def refresh_products():
    """Refresh products from Node.js script"""
    try:
        print("🔄 Uzum mahsulotlari yangilanmoqda...")
        
        # Run Node.js refresh script
        result = subprocess.run(
            ['node', 'test/refresh_uzum.js', 'refresh'],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Mahsulotlar muvaffaqiyatli yangilandi!")
            
            # Find the new products file
            test_dir = Path(__file__).parent / "test"
            json_files = list(test_dir.glob("uzum_products_variants_*.json"))
            
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                print(f"📁 Yangi fayl: {latest_file.name}")
                
                # Update bot to use new file
                update_bot_products_file(latest_file.name)
                
        else:
            print(f"❌ Xatolik: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Refresh xatoligi: {e}")

def update_bot_products_file(new_filename):
    """Update telegram_bot.py to use new products file"""
    try:
        bot_file = Path(__file__).parent / "telegram_bot.py"
        
        with open(bot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the products file name
        old_line = 'products_file = Path(__file__).parent / "test" / "bot_products_fixed_1770482210682.json"'
        new_line = f'products_file = Path(__file__).parent / "test" / "{new_filename}"'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            with open(bot_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Bot fayli yangilandi: {new_filename}")
        else:
            print("⚠️ Bot faylida products file topilmadi")
            
    except Exception as e:
        print(f"❌ Bot faylini yangilash xatoligi: {e}")

async def auto_refresh_loop():
    """Auto-refresh products every 5 minutes"""
    while True:
        try:
            print("⏰ Avto-refresh boshlandi...")
            refresh_products()
            print("⏳ 5 daqiqadan keyin yangilanadi...")
            await asyncio.sleep(5 * 60)  # 5 minutes
            
        except Exception as e:
            print(f"❌ Auto-refresh xatoligi: {e}")
            print("⏳ 1 daqiqadan keyin qayta uriniladi...")
            await asyncio.sleep(60)  # 1 minute on error

async def main():
    """Main function"""
    command = os.environ.get('REFRESH_MODE', 'once')
    
    if command == 'auto':
        print("🔄 Avto-refresh rejimi")
        await auto_refresh_loop()
    else:
        print("🔄 Bir marta yangilash")
        refresh_products()

if __name__ == "__main__":
    asyncio.run(main())
