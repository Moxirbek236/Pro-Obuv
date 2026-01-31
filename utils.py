
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
from flask import request, jsonify, session, flash, redirect, url_for, g
from config import Config

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

def load_translations():
    """Barcha tillardagi tarjimalarni yuklash"""
    try:
        # Use absolute path relative to this file to ensure it works regardless of CWD
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'data', 'translations.json')
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # Try relative path as fallback
        try:
            with open('data/translations.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            logging.error(f"Tarjimalarni yuklashda xatolik: {str(e)}")
            return {}

_translations = load_translations()

def get_current_language():
    """Joriy tilni qaytarish"""
    # Prefer unified 'interface_language' session key; fall back to legacy 'language'
    # If a request-scoped value was set earlier (g.interface_language), prefer it.
    try:
        from flask import g
        if hasattr(g, 'interface_language') and g.interface_language:
            return g.interface_language
    except Exception:
        pass
    return session.get('interface_language', session.get('language', Config.DEFAULT_LANGUAGE))

def set_language(lang_code):
    """Tilni o'zgartirish"""
    if lang_code in Config.SUPPORTED_LANGUAGES:
        session['interface_language'] = lang_code
        # keep backward compatibility
        session['language'] = lang_code
        return True
    return False

def get_text(key, lang=None):
    """Matnni joriy tilda olish"""
    if not lang:
        lang = get_current_language()
    # ensure we modify the module-level translations when reloading
    global _translations
    
    try:
        # Support dot-separated keys for nested objects (e.g., 'nav.home')
        parts = key.split('.') if isinstance(key, str) and '.' in key else [key]
        node = _translations.get(lang, {})
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                # Fallback to default language if nested key missing
                node = None
                break
        if node is not None:
            return node
        # If key not found in current in-memory translations, try reloading translations
        try:
            fresh = load_translations()
            if fresh:
                _translations = fresh
                node = _translations.get(lang, {})
                parts = key.split('.') if isinstance(key, str) and '.' in key else [key]
                for p in parts:
                    if isinstance(node, dict) and p in node:
                        node = node[p]
                    else:
                        node = None
                        break
                if node is not None:
                    return node
        except Exception:
            # If reload fails, continue to fallback logic below
            pass
        # Fallback: return top-level key if exists (or None)
        val = _translations.get(lang, {}).get(key, None)
        if val is not None:
             return val
             
        # Agar joriy tilda topilmasa, default tilini tekshiramiz
        val = _translations.get(Config.DEFAULT_LANGUAGE, {}).get(key, None)
        if val is not None:
            return val
            
        # Agar default tilda ham topilmasa, kalitni o'zini qaytarish
        return key
    except KeyError:
        # Agar tarjima topilmasa, default tildagi matnni qaytarish
        try:
            # Try dot-notation on default language
            parts = key.split('.') if isinstance(key, str) and '.' in key else [key]
            node = _translations.get(Config.DEFAULT_LANGUAGE, {})
            for p in parts:
                if isinstance(node, dict) and p in node:
                    node = node[p]
                else:
                    node = None
                    break
            if node is not None:
                return node
            return _translations[Config.DEFAULT_LANGUAGE].get(key)
        except KeyError:
            # Agar default tilda ham topilmasa, kalitni o'zini qaytarish
            return key


def translate(key, lang=None):
    """Robust translation helper used by templates.

    Attempts to return a localized string for `key`. Behaviors:
    - Try `get_text(key, lang)` first (nested lookups).
    - If that yields None, fall back to the flattened translations map which
      is used by client-side JS (keys like 'menu.all_products').
    - If still not found, return the original `key` so templates show a
      predictable placeholder instead of crashing.
    """
    try:
        val = get_text(key, lang)
        if val:
            return val
        # Fallback to flattened map
        flat = flatten_translations(lang)
        if isinstance(key, str) and key in flat and flat.get(key):
            return flat.get(key)
        return key
    except Exception:
        return key


def localized_field(item, field_base, lang=None):
    """Return localized field value from a DB row or dict-like item.

    Example: localized_field(item, 'name') will try 'name_uz','name_ru','name_en','name_kz'
    depending on session language or provided lang. Falls back to 'name' if localized field missing.
    """
    try:
        if not lang:
            lang = get_current_language()
        # Normalize lang (e.g., 'uz') and build candidate key
        cand = f"{field_base}_{lang}"
        # item might be sqlite Row, dict, or object with attributes
        if isinstance(item, dict):
            # Prefer explicit per-lang key like title_uz
            if cand in item and item[cand]:
                return item[cand]
            # If base field is a dict with language keys (e.g. title: {"uz": "...", "ru": "..."}), pick the lang value
            base_val = item.get(field_base)
            if isinstance(base_val, dict):
                # exact lang
                if lang in base_val and base_val[lang]:
                    return base_val[lang]
                # try common fallbacks
                for lk in (lang, 'uz', 'ru', 'en', 'kz'):
                    if lk in base_val and base_val[lk]:
                        return base_val[lk]
            # fallback to base field or legacy suffixed keys
            return (
                base_val
                or item.get(f"{field_base}_uz")
                or item.get(f"{field_base}_ru")
                or item.get(f"{field_base}_en")
                or item.get(f"{field_base}_kz")
            )

        # sqlite3.Row supports mapping access
        try:
            val = item[cand]
            if val:
                return val
        except Exception:
            pass

        # object attribute fallback
        try:
            val = getattr(item, cand, None)
            if val:
                return val
        except Exception:
            pass

        # Try base field
        try:
            val = item[field_base]
            if val:
                return val
        except Exception:
            pass

        try:
            val = getattr(item, field_base, None)
            if val:
                return val
        except Exception:
            pass

    except Exception:
        pass
    return None


def flatten_translations(lang=None):
    """Return a flat mapping of translation keys to strings for the given language.

    Example: {'footer.company_desc': '...'}
    """
    if not lang:
        lang = get_current_language()
    flat = {}

    def _walk(node, prefix=""):
        if isinstance(node, dict):
            for k, v in node.items():
                nk = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    _walk(v, nk)
                else:
                    flat[nk] = v

    try:
        node = _translations.get(lang, {}) or {}
        _walk(node, "")
    except Exception:
        pass
    return flat
