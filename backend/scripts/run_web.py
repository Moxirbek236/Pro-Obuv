import os
import subprocess
import sys

def main():
    """
    Faqat Web Server (Frontend + Backend API) ni ishga tushirish.
    Telegram bot bu yerda ishga tushmaydi (uni alohida serverda run_bot.py bilan ishlatasiz).
    """
    print(">>> WEB SERVER ishga tushmoqda...")
    print(">>> Telegram Bot avto-start o'chirilmoqda...")
    
    env = os.environ.copy()
    # Botni app.py ichidan start qilishni taqiqlaymiz
    env["START_TELEGRAM_BOT"] = "0"
    
    # Agar alohida DB connect qilish kerak bo'lsa, env vars shu yerda sozlanishi mumkin
    # env["DATABASE_URL"] = "postgresql://user:pass@host:5432/db"
    
    python_exe = sys.executable or "python"
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    
    try:
        # app.py ni alohida jarayon sifatida ishga tushiramiz
        subprocess.run([python_exe, app_path], env=env, check=True)
    except KeyboardInterrupt:
        print("\n>>> Web Server to'xtatildi.")
    except Exception as e:
        print(f"\n>>> Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    main()
