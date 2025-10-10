#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher: Flask (app.py) va Telegram bot (bot/telegram_bot.py) ni bir vaqtda ishga tushiradi.
Windows/Powershell muhitida qulay ishlashi uchun subprocess va signal boshqaruvi qo'llanilgan.
"""

import os
import sys
import subprocess
import threading
import signal
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable or "python"
LOGS_DIR = ROOT / "logs"
BOT_PID_FILE = LOGS_DIR / "telegram_bot.pid"

flask_proc = None
bot_proc = None


def start_flask():
    env = os.environ.copy()
    # Flask reloader'ni o'chirib, bitta processda ishlatamiz
    env.setdefault("FLASK_ENV", "production")
    # App ichidan botni avtomatik ishga tushirmaslik uchun (konfliktning oldini olish)
    env["START_TELEGRAM_BOT"] = "0"
    # If requested, start Gunicorn as the WSGI server instead of the builtin Flask dev server.
    # This is useful for production hosts which expect a single entrypoint. Set USE_GUNICORN=1
    # and optionally GUNICORN_WORKERS to control worker count.
    use_gunicorn = os.environ.get("USE_GUNICORN", "0") == "1"
    # Gunicorn is not supported on Windows (depends on fcntl). If we're on
    # Windows and the user requested gunicorn, warn and fall back to the
    # builtin Flask launcher so run_both remains usable on Windows dev boxes.
    is_windows = sys.platform.startswith("win") or os.name == "nt"
    if use_gunicorn and is_windows:
        print("[RUN] USE_GUNICORN=1 requested but running on Windows — gunicorn is unsupported. Falling back to app.py")
        use_gunicorn = False
    if use_gunicorn:
        workers = os.environ.get("GUNICORN_WORKERS", "2")
        bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:10000")
        # Run gunicorn module so we don't depend on shell wrappers
        cmd = [PYTHON, "-m", "gunicorn", f"app:app", "-b", bind, "-w", str(workers)]
    else:
        cmd = [PYTHON, str(ROOT / "app.py")]
    return subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        env=env,
    )


def start_bot():
    cmd = [PYTHON, str(ROOT / "bot" / "telegram_bot.py")]
    return subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )


def _stream_output(prefix: str, proc: subprocess.Popen):
    try:
        if proc.stdout is None:
            return
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            print(f"[{prefix}] {line.rstrip()}")
    except Exception:
        pass


def _is_process_running(pid: int) -> bool:
    try:
        if pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _existing_bot_running() -> bool:
    try:
        if not BOT_PID_FILE.exists():
            return False
        content = BOT_PID_FILE.read_text(encoding="utf-8").strip() or "0"
        pid = int(content)
        return _is_process_running(pid)
    except Exception:
        return False


def terminate_process(proc: subprocess.Popen, name: str):
    if proc is None:
        return
    try:
        if proc.poll() is None:
            try:
                # Windows: avval terminate, so'ng kill fallback
                proc.terminate()
            except Exception:
                pass
            try:
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    except Exception:
        pass


def main(*args, **kwargs):
    """Launcher/WSGI compatibility wrapper.

    - When invoked with no args (CLI), behaves as the original launcher:
      starts Flask and bot subprocesses and streams their output.
    - When invoked as a WSGI callable (environ, start_response) by Gunicorn
      (e.g. gunicorn run_both:main), delegate to the Flask app's WSGI app so
      the same module can be used as the entrypoint in environments that
      incorrectly configured the callable.
    """

    # If called as a WSGI application, delegate to the Flask app
    if len(args) >= 2 and callable(args[1]):
        environ = args[0]
        start_response = args[1]
        try:
            # Import the Flask app from app.py and dispatch
            from app import app as flask_app

            # flask_app is a Flask instance; its wsgi_app is a callable
            return flask_app.wsgi_app(environ, start_response)
        except Exception:
            # If Flask app can't be imported, re-raise for the WSGI server to log
            raise

    global flask_proc, bot_proc

    print("[RUN] Flask va Telegram bot ishga tushirilmoqda...")
    flask_proc = start_flask()
    time.sleep(1)  # Flask'ga boshlash uchun qisqa vaqt
    if _existing_bot_running():
        print(
            "[RUN] Bot allaqachon ishlayapti (pid faylga ko'ra). Yangi nusxa ishga tushirilmaydi."
        )
        bot_proc = None
    else:
        bot_proc = start_bot()

    try:
        print("[RUN] Flask PID:", getattr(flask_proc, "pid", None))
        print(
            "[RUN] Bot   PID:",
            getattr(bot_proc, "pid", None) if bot_proc is not None else None,
        )
        print("[RUN] To'xtatish uchun Ctrl+C bosing")
    except KeyboardInterrupt:
        # Agar foydalanuvchi shu paytda Ctrl+C bossa, toza yopamiz
        print("\n[RUN] KeyboardInterrupt qabul qilindi. To'xtatilmoqda...")
        if bot_proc is not None:
            terminate_process(bot_proc, "bot")
        terminate_process(flask_proc, "flask")
        return

    # Log oqimini konsolga chiqarish uchun thrеadlar
    t_flask = threading.Thread(
        target=_stream_output, args=("FLASK", flask_proc), daemon=True
    )
    t_flask.start()
    t_bot = None
    if bot_proc is not None:
        t_bot = threading.Thread(
            target=_stream_output, args=("BOT", bot_proc), daemon=True
        )
        t_bot.start()

    # Graceful shutdown signallarini tutish
    def handle_exit(signum, frame):
        print(f"\n[RUN] Signal qabul qilindi ({signum}). To'xtatilmoqda...")
        if bot_proc is not None:
            terminate_process(bot_proc, "bot")
        terminate_process(flask_proc, "flask")
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        try:
            signal.signal(sig, handle_exit)
        except Exception:
            pass

    # Nazorat sikli: agar jarayonlardan biri yiqilsa, ikkinchisini ham to'xtatamiz
    try:
        while True:
            f_code = flask_proc.poll()
            b_code = bot_proc.poll() if bot_proc is not None else None
            if f_code is not None:
                print(f"[RUN] Flask yakunlandi kod={f_code}. Bot ham to'xtatiladi.")
                if bot_proc is not None:
                    terminate_process(bot_proc, "bot")
                break
            if bot_proc is not None and b_code is not None:
                print(f"[RUN] Bot yakunlandi kod={b_code}. Flask davom etadi.")
                bot_proc = None
            time.sleep(1)
    except KeyboardInterrupt:
        handle_exit(signal.SIGINT, None)
    finally:
        if bot_proc is not None:
            terminate_process(bot_proc, "bot")
        terminate_process(flask_proc, "flask")


if __name__ == "__main__":
    main()
