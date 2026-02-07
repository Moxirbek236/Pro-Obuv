import os
import subprocess
import sys
import time

def main():
    """
    Faqat Telegram Botni alohida ishga tushirish.
    DIQQAT: Bot ishlashi uchun u Web Serverga ulana olishi kerak (FLASK_APP_URL).
    """
    print(">>> TELEGRAM BOT SERVER ishga tushmoqda...")
    
    env = os.environ.copy()
    
    # Web server manzili (Agar bot boshqa serverda bo'lsa, buni o'zgartiring)
    web_url = env.get("FLASK_APP_URL")
    if not web_url:
        print(">>> OGOHLANTIRISH: FLASK_APP_URL sozlanmagan!")
        print(">>> Bot localhost:5000 ga ulanishga harakat qiladi.")
        print(">>> Agar Web Server boshqa ip da bo'lsa, .env faylga yozing:")
        print(">>> FLASK_APP_URL=http://<web-server-ip>:5000")
    else:
        print(f">>> Web Server manzili: {web_url}")

    python_exe = sys.executable or "python"
    bot_path = os.path.join(os.path.dirname(__file__), "bot", "telegram_bot.py")
    
    if not os.path.exists(bot_path):
        print(f"ERROR: Bot fayli topilmadi: {bot_path}")
        return

    try:
        # Botni ishga tushiramiz
        subprocess.run([python_exe, bot_path], env=env, check=True)
    except KeyboardInterrupt:
        print("\n>>> Bot to'xtatildi.")
    except Exception as e:
        print(f"\n>>> Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    main()
