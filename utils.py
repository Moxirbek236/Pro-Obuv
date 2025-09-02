
"""
Universal Restaurant System Utilities
Barcha yordamchi funksiyalar bu yerda
"""

import os
import time
import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, flash, redirect, url_for

def generate_unique_id(prefix="", length=8):
    """Unikal ID yaratish"""
    return f"{prefix}{secrets.token_hex(length)}"

def format_currency(amount, currency="UZS"):
    """Valyutani formatlash"""
    if currency == "UZS":
        return f"{amount:,.0f} so'm"
    elif currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def validate_phone_number(phone):
    """Telefon raqamini tekshirish"""
    import re
    # O'zbek telefon raqamlari formati
    patterns = [
        r'^\+998\d{9}$',        # +998901234567
        r'^998\d{9}$',          # 998901234567
        r'^\d{9}$',             # 901234567
    ]
    
    phone = phone.strip().replace(' ', '').replace('-', '')
    return any(re.match(pattern, phone) for pattern in patterns)

def validate_email(email):
    """Email formatini tekshirish"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def safe_int(value, default=0):
    """Xavfsiz integer conversion"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Xavfsiz float conversion"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def get_client_ip():
    """Mijozning haqiqiy IP manzilini olish"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    else:
        return request.remote_addr

def create_response(success=True, message="", data=None, status_code=200):
    """Universal API response yaratish"""
    response = {
        "success": success,
        "message": message,
        "timestamp": time.time()
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status_code

def log_user_action(action, user_type="guest", user_id=None, details=None):
    """Foydalanuvchi harakatlarini log qilish"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user_type": user_type,
        "user_id": user_id,
        "ip_address": get_client_ip(),
        "user_agent": request.headers.get('User-Agent', ''),
        "details": details
    }
    
    # Log faylga yozish
    try:
        log_file = 'logs/user_actions.log'
        os.makedirs('logs', exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except Exception as e:
        logging.error(f"User action log xatoligi: {str(e)}")

def calculate_business_hours_eta(base_minutes, timezone_str="Asia/Tashkent"):
    """Ish vaqti hisobga olingan ETA hisoblash"""
    import pytz
    
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        # Ish vaqti: 09:00 - 22:00
        work_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        work_end = now.replace(hour=22, minute=0, second=0, microsecond=0)
        
        # Agar ish vaqtida bo'lsa, oddiy hisoblash
        if work_start <= now <= work_end:
            return now + timedelta(minutes=base_minutes)
        
        # Agar ish vaqtidan tashqari bo'lsa, ertangi kun 09:00 ga qo'shish
        if now > work_end:
            # Ertangi kun
            next_day = now + timedelta(days=1)
            next_work_start = next_day.replace(hour=9, minute=0, second=0, microsecond=0)
            return next_work_start + timedelta(minutes=base_minutes)
        else:
            # Bugun, ish boshlanishi
            return work_start + timedelta(minutes=base_minutes)
    
    except Exception as e:
        logging.error(f"Business hours ETA hisoblashda xatolik: {str(e)}")
        return datetime.now() + timedelta(minutes=base_minutes)

def get_system_info():
    """Tizim ma'lumotlarini olish"""
    import platform
    import psutil
    
    try:
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent
        }
    except Exception as e:
        return {"error": str(e)}

def backup_database(db_path, backup_dir="backups"):
    """Ma'lumotlar bazasini zaxiralash"""
    try:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"restaurant_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        return backup_path
    except Exception as e:
        logging.error(f"Database backup xatoligi: {str(e)}")
        return None

def cleanup_old_backups(backup_dir="backups", keep_days=30):
    """Eski zaxiralarni tozalash"""
    try:
        if not os.path.exists(backup_dir):
            return
        
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                os.remove(file_path)
                logging.info(f"Eski backup o'chirildi: {filename}")
    
    except Exception as e:
        logging.error(f"Backup tozalashda xatolik: {str(e)}")
