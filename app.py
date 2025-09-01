from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, datetime, json
from flask_sqlalchemy import SQLAlchemy
import pytz
import qrcode
from io import BytesIO
import base64
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_change_me")

# Database fayl yo'lini to'g'rilash
DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")

import logging

# Log faylini sozlash
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error.log'),
        logging.StreamHandler()
    ]
)



AVG_PREP_MINUTES = int(os.environ.get("AVG_PREP_MINUTES", "7"))
db = SQLAlchemy(app)
# o'rtacha tayyorlanish vaqti (daqiqalarda)

# O'zbekiston vaqt zonasi
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

def get_current_time():
    return datetime.datetime.now(TASHKENT_TZ)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Foydalanuvchilar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            address TEXT,
            card_number TEXT,
            card_expiry TEXT,
            created_at TEXT NOT NULL
        );
    """)

    # Xodimlar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            phone TEXT NOT NULL,
            passport_series TEXT NOT NULL,
            passport_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            total_hours INTEGER DEFAULT 0,
            orders_handled INTEGER DEFAULT 0,
            last_activity TEXT,
            created_at TEXT NOT NULL
        );
    """)

    # Kuryerlar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS couriers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            phone TEXT NOT NULL,
            passport_series TEXT NOT NULL,
            passport_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            total_hours INTEGER DEFAULT 0,
            deliveries_completed INTEGER DEFAULT 0,
            last_activity TEXT,
            created_at TEXT NOT NULL
        );
    """)

    # Buyurtmalar jadvali (yangilangan)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            ticket_no INTEGER NOT NULL,
            order_type TEXT NOT NULL, -- 'dine_in' yoki 'delivery'
            status TEXT NOT NULL,
            delivery_address TEXT,
            delivery_distance REAL DEFAULT 0, -- masofa km da
            delivery_price REAL DEFAULT 0, -- yetkazish narxi
            customer_phone TEXT,
            card_number TEXT,
            courier_id INTEGER,
            created_at TEXT NOT NULL,
            eta_time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (courier_id) REFERENCES couriers (id)
        );
    """)

    # Tikketlar hisoblagich
    cur.execute("""
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        );
    """)
    cur.execute("INSERT OR IGNORE INTO counters (name, value) VALUES ('ticket', 10000);")

    # Menyu mahsulotlari (yangilangan)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            available BOOLEAN DEFAULT 1,
            stock_quantity INTEGER DEFAULT 0,
            orders_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 0.0,
            created_at TEXT NOT NULL
        );
    """)

    # Sevimlilar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id),
            UNIQUE(user_id, menu_item_id)
        );
    """)

    # Savatcha jadvali (yangilangan)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT NOT NULL DEFAULT 'default_session',
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    """)

    # Buyurtma tafsilotlari jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    """)

    # Baholar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id),
            UNIQUE(user_id, menu_item_id)
        );
    """)

    # Savollar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
    """)

    # Cheklar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            receipt_number TEXT NOT NULL UNIQUE,
            total_amount REAL NOT NULL,
            cashback_amount REAL NOT NULL,
            cashback_percentage REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        );
    """)

    # Boshlang'ich taomlar qo'shish
    cur.execute("SELECT COUNT(*) FROM menu_items")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        sample_items = [
            ('Osh', 25000, 'food', 'An\'anaviy o\'zbek taomi, guruch va go\'sht bilan', 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=300&h=200&fit=crop', 1, 50, 0, 4.5, 0.0, now),
            ('Manti', 20000, 'food', 'Bug\'da pishirilgan go\'shtli manti', 'https://images.unsplash.com/photo-1534938665420-4193effeacc4?w=300&h=200&fit=crop', 1, 30, 0, 4.8, 5.0, now),
            ('Shashlik', 30000, 'food', 'Mangalda pishirilgan mazali shashlik', 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=300&h=200&fit=crop', 1, 25, 0, 4.7, 0.0, now),
            ('Lagmon', 22000, 'food', 'Qo\'l tortmasi bilan tayyorlangan lagmon', 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=300&h=200&fit=crop', 1, 40, 0, 4.6, 10.0, now),
            ('Choy', 5000, 'drink', 'Issiq qora choy', 'https://images.unsplash.com/photo-1559056961-84c5ffc10e14?w=300&h=200&fit=crop', 1, 100, 0, 4.2, 0.0, now),
            ('Qora choy', 6000, 'drink', 'O\'zbek an\'anaviy choy', 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=300&h=200&fit=crop', 1, 80, 0, 4.3, 0.0, now),
            ('Kompot', 8000, 'drink', 'Mevali kompot', 'https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=300&h=200&fit=crop', 1, 60, 0, 4.1, 15.0, now),
            ('Coca Cola', 10000, 'drink', 'Sovuq ichimlik', 'https://images.unsplash.com/photo-1581636625402-29b2a704ef13?w=300&h=200&fit=crop', 1, 70, 0, 4.0, 0.0, now),
        ]
        cur.executemany("INSERT INTO menu_items (name, price, category, description, image_url, available, stock_quantity, orders_count, rating, discount_percentage, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_items)

    conn.commit()
    conn.close()

# Flask 2.2+ da before_first_request deprecated
def ensure_orders_columns():
    """Orders jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(orders);")
        cols = [r[1] for r in cur.fetchall()]

        if 'status' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'waiting';")
            conn.commit()

        if 'user_id' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN user_id INTEGER;")
            conn.commit()

        if 'delivery_address' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_address TEXT;")
            conn.commit()

        if 'delivery_distance' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_distance REAL DEFAULT 0;")
            conn.commit()

        if 'delivery_price' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_price REAL DEFAULT 0;")
            conn.commit()

        if 'customer_phone' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT;")
            conn.commit()

        if 'card_number' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN card_number TEXT;")
            conn.commit()

        if 'courier_id' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_id INTEGER;")
            conn.commit()

        if 'order_type' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN order_type TEXT NOT NULL DEFAULT 'dine_in';")
            conn.commit()

        if 'delivery_latitude' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_latitude REAL;")
            conn.commit()

        if 'delivery_longitude' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_longitude REAL;")
            conn.commit()

        if 'courier_delivery_time' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_delivery_time INTEGER DEFAULT 30;")
            conn.commit()

        if 'delivery_map_url' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN delivery_map_url TEXT;")
            conn.commit()

        if 'customer_note' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN customer_note TEXT;")
            conn.commit()

        if 'courier_price' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_price REAL DEFAULT 0;")
            conn.commit()

        if 'courier_delivery_minutes' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN courier_delivery_minutes INTEGER DEFAULT 0;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_users_columns():
    """Users jadvaliga latitude va longitude ustunlarini qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(users);")
        cols = [r[1] for r in cur.fetchall()]

        if 'address_latitude' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN address_latitude REAL;")
            conn.commit()

        if 'address_longitude' not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN address_longitude REAL;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_cart_items_columns():
    """Cart_items jadvaliga user_id ustunini qo'shadi va session_id ni optional qiladi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(cart_items);")
        cols = [r[1] for r in cur.fetchall()]
        if 'user_id' not in cols:
            cur.execute("ALTER TABLE cart_items ADD COLUMN user_id INTEGER;")
            conn.commit()

        # Eski jadval strukturasini yangilash - session_id ni NULL qilib qo'yish
        cur.execute("UPDATE cart_items SET session_id = 'temp_session' WHERE session_id IS NULL OR session_id = ''")
        conn.commit()
    except Exception as e:
        pass
    conn.close()

def ensure_staff_columns():
    """Staff jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(staff);")
        cols = [r[1] for r in cur.fetchall()]

        if 'passport_series' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN passport_series TEXT;")
            conn.commit()

        if 'passport_number' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN passport_number TEXT;")
            conn.commit()

        if 'orders_handled' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN orders_handled INTEGER DEFAULT 0;")
            conn.commit()

        if 'last_activity' not in cols:
            cur.execute("ALTER TABLE staff ADD COLUMN last_activity TEXT;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_courier_columns():
    """Courier jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(couriers);")
        cols = [r[1] for r in cur.fetchall()]

        if 'passport_series' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN passport_series TEXT;")
            conn.commit()

        if 'passport_number' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN passport_number TEXT;")
            conn.commit()

        if 'total_hours' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN total_hours REAL DEFAULT 0;")
            conn.commit()

        if 'deliveries_completed' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN deliveries_completed INTEGER DEFAULT 0;")
            conn.commit()

        if 'last_activity' not in cols:
            cur.execute("ALTER TABLE couriers ADD COLUMN last_activity TEXT;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def ensure_menu_items_columns():
    """Menu_items jadvaliga kerakli ustunlarni qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(menu_items);")
        cols = [r[1] for r in cur.fetchall()]

        if 'description' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN description TEXT;")
            conn.commit()

        if 'image_url' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN image_url TEXT;")
            conn.commit()

        if 'available' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN available BOOLEAN DEFAULT 1;")
            conn.commit()

        if 'stock_quantity' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN stock_quantity INTEGER DEFAULT 0;")
            conn.commit()

        if 'orders_count' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN orders_count INTEGER DEFAULT 0;")
            conn.commit()

        if 'rating' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN rating REAL DEFAULT 0.0;")
            conn.commit()

        if 'discount_percentage' not in cols:
            cur.execute("ALTER TABLE menu_items ADD COLUMN discount_percentage REAL DEFAULT 0.0;")
            conn.commit()

    except Exception as e:
        pass
    conn.close()

def cleanup_expired_orders():
    """Waiting holatidagi, 30 daqiqadan oshgan buyurtmalarni cancelled ga o'tkazadi."""
    conn = get_db()
    cur = conn.cursor()
    cutoff = (get_current_time() - datetime.timedelta(minutes=30)).isoformat()
    try:
        cur.execute("UPDATE orders SET status='cancelled' WHERE status='waiting' AND created_at < ?", (cutoff,))
        conn.commit()
    except Exception as e:
        pass
    conn.close()

# Ensure columns exist on startup
ensure_orders_columns()
ensure_cart_items_columns()
ensure_staff_columns()
ensure_courier_columns()
ensure_menu_items_columns()
ensure_users_columns()


# O'rniga buni app context ichida chaqiramiz

# ---------- Helpers ----------

def next_ticket_no(conn):
    cur = conn.cursor()
    cur.execute("UPDATE counters SET value = value + 1 WHERE name = 'ticket';")
    cur.execute("SELECT value FROM counters WHERE name = 'ticket';")
    return cur.fetchone()[0]

def waiting_position(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting';")
    return cur.fetchone()[0]

def calc_eta_minutes(conn):
    # navbatdagi pozitsiya bo'yicha ETA ni hisoblash
    position = waiting_position(conn)  # sizdan oldingi kutayotganlar soni
    eta_minutes = (position + 1) * AVG_PREP_MINUTES
    return eta_minutes

def get_user_queue_position(conn, ticket_no):
    # Foydalanuvchining navbatdagi o'rni
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM orders 
        WHERE status='waiting' AND created_at < (
            SELECT created_at FROM orders WHERE ticket_no=? AND status='waiting'
        )
    """, (ticket_no,))
    result = cur.fetchone()
    return result[0] + 1 if result else 0

def fmt_time(dt):
    return dt.strftime("%H:%M")

def search_location_with_serper(query, gl="uz", hl="uz"):
    """Serper API orqali joylashuvlarni qidirish"""
    try:
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': '1b077296f67499a12ee28ce232bb48221d29be14',
            'Content-Type': 'application/json'
        }
        data = {
            "q": query,
            "gl": gl,
            "hl": hl
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Serper API xatoligi: {e}")
        return None

def get_places_with_serper(query, gl="uz", hl="uz"):
    """Serper API orqali Google Places ma'lumotlarini olish"""
    try:
        url = "https://google.serper.dev/places"
        headers = {
            'X-API-KEY': '1b077296f67499a12ee28ce232bb48221d29be14',
            'Content-Type': 'application/json'
        }
        data = {
            "q": query,
            "gl": gl,
            "hl": hl
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Serper Places API xatoligi: {e}")
        return None

def validate_delivery_address(address):
    """Yetkazib berish manzilini tekshirish Yandex API orqali"""
    if not address:
        return False, "Manzil kiritilmagan"

    try:
        # Yandex Geocoding API orqali manzilni tekshirish
        geocoding_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'apikey': app.config['YANDEX_GEOCODER_API'],
            'geocode': f"{address}, Toshkent, O'zbekiston",
            'format': 'json',
            'results': 1
        }

        response = requests.get(geocoding_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Natijalarni tekshirish
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

            if geo_objects:
                return True, "Manzil topildi"
            else:
                return False, "Manzil topilmadi"
        else:
            # API ishlamasa, oddiy tekshirish
            if len(address) > 5 and any(word in address.lower() for word in ['ko\'cha', 'mahalla', 'tuman', 'shoh', 'yo\'l']):
                return True, "Manzil qabul qilindi"
            else:
                return False, "Manzilni to'liqroq kiriting"

    except Exception as e:
        # Xatolik bo'lsa, oddiy tekshirish
        if len(address) > 5:
            return True, "Manzil qabul qilindi"
        else:
            return False, "Manzilni to'liqroq kiriting"

def calculate_delivery_distance(address):
    """Yetkazib berish masofasini hisoblash Yandex API orqali"""
    try:
        # Restoran koordinatalari (Toshkent markazi)
        restaurant_coords = [41.2995, 69.2401]

        # Yandex Geocoding API orqali manzilni koordinatalarga o'tkazish
        geocoding_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'apikey': app.config['YANDEX_GEOCODER_API'],
            'geocode': f"{address}, Toshkent, O'zbekiston",
            'format': 'json',
            'results': 1
        }

        response = requests.get(geocoding_url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            geo_objects = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

            if geo_objects:
                # Koordinatalarni olish
                point = geo_objects[0]['GeoObject']['Point']['pos'].split()
                dest_coords = [float(point[1]), float(point[0])]  # lat, lng formatida

                # To'g'ri chiziq bo'yicha masofa hisoblash (Haversine formula)
                import math

                lat1, lng1 = math.radians(restaurant_coords[0]), math.radians(restaurant_coords[1])
                lat2, lng2 = math.radians(dest_coords[0]), math.radians(dest_coords[1])

                dlat = lat2 - lat1
                dlng = lng2 - lng1

                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
                c = 2 * math.asin(math.sqrt(a))
                distance_km = 6371 * c  # Yer radiusi 6371 km

                return round(min(50, max(0.5, distance_km)), 1)

        # Agar API ishlamasa yoki natija bo'lmasa, oddiy hisoblash
        if 'toshkent' in address.lower() or 'алмазар' in address.lower():
            return 5.0
        elif any(word in address.lower() for word in ['sergeli', 'yunusobod', 'yashnobod']):
            return 8.0
        elif any(word in address.lower() for word in ['chilonzor', 'bektemir']):
            return 12.0
        else:
            return 7.0

    except Exception as e:
        logging.error(f"Masofa hisoblashda xatolik: {str(e)}")
        return 5.0

def generate_qr_code(receipt_data):
    """Chek uchun QR kod yaratish"""
    # Soliq.uz uchun chek ma'lumotlari
    qr_data = {
        "receipt_number": receipt_data['receipt_number'],
        "total_amount": receipt_data['total_amount'],
        "cashback_amount": receipt_data['cashback_amount'],
        "date": receipt_data['created_at'][:10],
        "time": receipt_data['created_at'][11:19],
        "restaurant": "O'zbek Milliy Taomlar Restorani",
        "inn": "123456789",  # Restoran INN raqami
        "cashback_percent": receipt_data['cashback_percentage']
    }

    # JSON formatda ma'lumotlarni tayyorlash
    qr_text = json.dumps(qr_data, ensure_ascii=False)

    # QR kod yaratish
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    # QR kod rasmini yaratish
    img = qr.make_image(fill_color="black", back_color="white")

    # Base64 formatga o'tkazish
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str

def get_session_id():
    """Session ID yaratish yoki olish"""
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_cart_items(conn, session_id, user_id=None):
    """Savatchadagi mahsulotlarni olish"""
    cur = conn.cursor()
    if user_id:
        cur.execute("""
            SELECT ci.id, mi.name, mi.price, ci.quantity, (mi.price * ci.quantity) as total
            FROM cart_items ci
            JOIN menu_items mi ON ci.menu_item_id = mi.id
            WHERE ci.user_id = ?
            ORDER BY ci.created_at DESC
        """, (user_id,))
    else:
        cur.execute("""
            SELECT ci.id, mi.name, mi.price, ci.quantity, (mi.price * ci.quantity) as total
            FROM cart_items ci
            JOIN menu_items mi ON ci.menu_item_id = mi.id
            WHERE ci.session_id = ?
            ORDER BY ci.created_at DESC
        """, (session_id,))
    return cur.fetchall()

def get_cart_total(conn, session_id, user_id=None):
    """Savatchaning umumiy summasini hisoblash"""
    cur = conn.cursor()
    if user_id:
        cur.execute("""
            SELECT SUM(mi.price * ci.quantity)
            FROM cart_items ci
            JOIN menu_items mi ON ci.menu_item_id = mi.id
            WHERE ci.user_id = ?
        """, (user_id,))
    else:
        cur.execute("""
            SELECT SUM(mi.price * ci.quantity)
            FROM cart_items ci
            JOIN menu_items mi ON ci.menu_item_id = mi.id
            WHERE ci.session_id = ?
        """, (session_id,))
    result = cur.fetchone()[0]
    return result if result else 0

def clear_cart(conn, session_id, user_id=None):
    """Savatchani tozalash"""
    cur = conn.cursor()
    if user_id:
        cur.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    else:
        cur.execute("DELETE FROM cart_items WHERE session_id = ?", (session_id,))
    conn.commit()

def save_user_to_json(name, ticket_no, order_time, order_items):
    """Foydalanuvchi ma'lumotlarini users.json fayliga saqlash"""
    users_file = 'users.json'

    # Yangi foydalanuvchi ma'lumotlari
    user_data = {
        'ism': name,
        'buyurtma_raqami': ticket_no,
        'buyurtma_vaqti': order_time.strftime("%Y-%m-%d %H:%M:%S"),
        'buyurtma_mahsulotlari': order_items
    }

    # Mavjud ma'lumotlarni o'qish
    users_list = []
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            users_list = []

    # Yangi ma'lumotni qo'shish
    users_list.append(user_data)

    # Faylga saqlash
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, ensure_ascii=False, indent=2)

def save_staff_to_json(first_name, last_name, birth_date, phone, staff_id, register_time):
    """Xodim ma'lumotlarini employees.json fayliga saqlash"""
    employees_file = 'employees.json'

    # Yangi xodim ma'lumotlari
    employee_data = {
        'id': staff_id,
        'ism': first_name,
        'familiya': last_name,
        'tugulgan_sana': birth_date,
        'telefon': phone,
        'royxatdan_otgan_vaqti': register_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Mavjud ma'lumotlarni o'qish
    employees_list = []
    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees_list = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            employees_list = []

    # Yangi ma'lumotni qo'shish
    employees_list.append(employee_data)

    # Faylga saqlash
    with open(employees_file, 'w', encoding='utf-8') as f:
        json.dump(employees_list, f, ensure_ascii=False, indent=2)

# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/system-management-panel-x8k2m")
def admin_index():
    # Super admin yoki staff kirgan bo'lishi kerak
    if not session.get("super_admin") and not session.get("staff_id"):
        flash("Bu sahifaga kirish uchun admin huquqi kerak.", "error")
        return redirect(url_for("index"))
    return render_template("admin_index.html")

@app.route("/display-monitor-tv-screen-z9p4n")
def admin_monitor():
    # Super admin yoki staff kirgan bo'lishi kerak
    if not session.get("super_admin") and not session.get("staff_id"):
        flash("Bu sahifaga kirish uchun admin huquqi kerak.", "error")
        return redirect(url_for("index"))
    cleanup_expired_orders()
    conn = get_db()
    cur = conn.cursor()
    # Waiting ordered by eta_time (earliest first)
    cur.execute("""SELECT o.*, 
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE o.status='waiting'
        GROUP BY o.id
        ORDER BY o.eta_time ASC
    """)
    waiting = cur.fetchall()
    # Ready orders
    cur.execute("""SELECT o.*, 
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE o.status='ready'
        GROUP BY o.id
        ORDER BY o.eta_time ASC
    """)
    ready = cur.fetchall()
    # Served orders in last 5 minutes
    five_min_ago = (get_current_time() - datetime.timedelta(minutes=5)).isoformat()
    cur.execute("""SELECT o.*, 
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE o.status='served' AND o.created_at >= ?
        GROUP BY o.id
        ORDER BY o.created_at ASC
    """, (five_min_ago,))
    served_recent = cur.fetchall()
    conn.close()
    return render_template('admin_monitor.html', waiting=waiting, ready=ready, served_recent=served_recent)

# ---- MENU ----
@app.route("/menu")
def menu():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu_items WHERE available = 1 ORDER BY category, name")
    menu_items = cur.fetchall()
    conn.close()

    foods = [item for item in menu_items if item['category'] == 'food']
    drinks = [item for item in menu_items if item['category'] == 'drink']

    return render_template("menu.html", foods=foods, drinks=drinks)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    menu_item_id = request.form.get("menu_item_id")
    quantity = int(request.form.get("quantity", 1))

    if not menu_item_id:
        flash("Mahsulot tanlanmadi.", "error")
        return redirect(url_for("menu"))

    session_id = get_session_id()
    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()

    # Mavjudligini tekshirish
    if user_id:
        cur.execute("SELECT * FROM cart_items WHERE user_id = ? AND menu_item_id = ?", (user_id, menu_item_id))
    else:
        cur.execute("SELECT * FROM cart_items WHERE session_id = ? AND menu_item_id = ?", (session_id, menu_item_id))

    existing = cur.fetchone()
    now = get_current_time().isoformat()

    if existing:
        # Mavjud bo'lsa miqdorni oshirish
        cur.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (quantity, existing['id']))
    else:
        # Yangi qo'shish - har doim session_id ni ham berish
        if user_id:
            cur.execute("INSERT INTO cart_items (user_id, session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?, ?)", 
                       (user_id, session_id, menu_item_id, quantity, now))
        else:
            cur.execute("INSERT INTO cart_items (session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?)", 
                       (session_id, menu_item_id, quantity, now))

    conn.commit()
    conn.close()
    flash("Mahsulot savatchaga qo'shildi!", "success")
    return redirect(url_for("menu"))

@app.route("/cart")
def cart():
    session_id = get_session_id()
    user_id = session.get("user_id")
    conn = get_db()

    # Foydalanuvchi ma'lumotlarini olish va session ga yuklash
    if user_id:
        cur = conn.cursor()
        cur.execute("SELECT phone, address, address_latitude, address_longitude, first_name, last_name FROM users WHERE id = ?", (user_id,))
        user_profile = cur.fetchone()

        if user_profile:
            session['user_phone'] = user_profile['phone'] or ''
            session['user_address'] = user_profile['address'] or ''
            session['user_address_latitude'] = user_profile['address_latitude'] or ''
            session['user_address_longitude'] = user_profile['address_longitude'] or ''
            session['user_first_name'] = user_profile['first_name'] or ''
            session['user_last_name'] = user_profile['last_name'] or ''

    cart_items = get_cart_items(conn, session_id, user_id)
    total = get_cart_total(conn, session_id, user_id)
    conn.close()
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/remove_from_cart/<int:cart_item_id>", methods=["POST"])
def remove_from_cart(cart_item_id):
    session_id = get_session_id()
    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()

    if user_id:
        cur.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?", (cart_item_id, user_id))
    else:
        cur.execute("DELETE FROM cart_items WHERE id = ? AND session_id = ?", (cart_item_id, session_id))

    conn.commit()
    conn.close()
    flash("Mahsulot savatchadan olib tashlandi.", "success")
    return redirect(url_for("cart"))

@app.route("/get_cart_count")
def get_cart_count():
    session_id = get_session_id()
    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()

    if user_id:
        cur.execute("SELECT SUM(quantity) FROM cart_items WHERE user_id = ?", (user_id,))
    else:
        cur.execute("SELECT SUM(quantity) FROM cart_items WHERE session_id = ?", (session_id,))

    result = cur.fetchone()[0]
    count = result if result else 0
    conn.close()
    return jsonify({"count": count})

# ---- USER LOGIN & REGISTER ----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email va parolni kiriting.", "error")
            return redirect(url_for("login"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = f"{user['first_name']} {user['last_name']}"
            session["user_email"] = user["email"]
            flash(f"Xush kelibsiz, {user['first_name']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Noto'g'ri email yoki parol.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([first_name, last_name, email, password, confirm_password]):
            flash("Majburiy maydonlarni to'ldiring.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Parollar mos kelmaydi.", "error")
            return redirect(url_for("register"))

        conn = get_db()
        cur = conn.cursor()

        # Email mavjudligini tekshirish
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            flash("Bu email allaqachon ro'yxatdan o'tgan.", "error")
            conn.close()
            return redirect(url_for("register"))

        # Xarita koordinatalari
        address_latitude = request.form.get("address_latitude", "")
        address_longitude = request.form.get("address_longitude", "")

        # Yangi foydalanuvchi yaratish
        password_hash = generate_password_hash(password)
        now = get_current_time().isoformat()

        cur.execute("""
            INSERT INTO users (first_name, last_name, email, phone, address, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, address, password_hash, now))

        conn.commit()
        user_id = cur.lastrowid
        conn.close()

        # Avtomatik tizimga kiritish
        session["user_id"] = user_id
        session["user_name"] = f"{first_name} {last_name}"
        session["user_email"] = email

        flash(f"Muvaffaqiyatli ro'yxatdan o'tdingiz! Xush kelibsiz, {first_name}!", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        flash("Profilni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()

    try:
        # Foydalanuvchi ma'lumotlarini olish
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()

        if not user:
            conn.close()
            flash("Foydalanuvchi ma'lumotlari topilmadi.", "error")
            return redirect(url_for("logout"))

        # Foydalanuvchi buyurtmalar tarixi va umumiy summa
        cur.execute("""
            SELECT o.*, COALESCE(r.total_amount, 0) as total_amount, 
                   GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
            FROM orders o
            LEFT JOIN receipts r ON o.id = r.order_id
            LEFT JOIN order_details od ON o.id = od.order_id
            LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
            WHERE o.user_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 10
        """, (user_id,))
        orders = cur.fetchall()

        conn.close()

        return render_template("profile.html", user=user, orders=orders)

    except Exception as e:
        conn.close()
        logging.error(f"Profile sahifasida xatolik: {str(e)}")
        flash("Profilni yuklashda xatolik yuz berdi.", "error")
        return redirect(url_for("index"))

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not all([first_name, last_name, email]):
        flash("Ism, familiya va email majburiy.", "error")
        return redirect(url_for("profile"))

    conn = get_db()
    cur = conn.cursor()

    # Email takrorlanishini tekshirish
    cur.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
    if cur.fetchone():
        flash("Bu email allaqachon ishlatilmoqda.", "error")
        conn.close()
        return redirect(url_for("profile"))

    # Ma'lumotlarni yangilash
    cur.execute("""
        UPDATE users 
        SET first_name = ?, last_name = ?, email = ?, phone = ?
        WHERE id = ?
    """, (first_name, last_name, email, phone, user_id))

    conn.commit()
    conn.close()

    # Session ma'lumotlarini yangilash
    session["user_name"] = f"{first_name} {last_name}"
    session["user_email"] = email

    flash("Profil muvaffaqiyatli yangilandi!", "success")
    return redirect(url_for("profile"))

@app.route("/update_address", methods=["POST"])
def update_address():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    address = request.form.get("address", "").strip()
    address_latitude = request.form.get("address_latitude", "")
    address_longitude = request.form.get("address_longitude", "")

    if not address:
        flash("Manzilni xaritadan tanlang.", "error")
        return redirect(url_for("profile"))

    conn = get_db()
    cur = conn.cursor()

    # Manzilni yangilash
    cur.execute("""
        UPDATE users 
        SET address = ?, address_latitude = ?, address_longitude = ?
        WHERE id = ?
    """, (address, address_latitude if address_latitude else None, 
          address_longitude if address_longitude else None, user_id))

    conn.commit()
    conn.close()

    flash("Manzil muvaffaqiyatli yangilandi!", "success")
    return redirect(url_for("profile"))

@app.route("/change_password", methods=["POST"])
def change_password():
    if not session.get("user_id"):
        flash("Tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not all([current_password, new_password, confirm_password]):
        flash("Barcha parol maydonlarini to'ldiring.", "error")
        return redirect(url_for("profile_settings"))

    if new_password != confirm_password:
        flash("Yangi parollar mos kelmaydi.", "error")
        return redirect(url_for("profile_settings"))

    if len(new_password) < 6:
        flash("Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak.", "error")
        return redirect(url_for("profile_settings"))

    conn = get_db()
    cur = conn.cursor()

    # Joriy parolni tekshirish
    cur.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    user_hash = cur.fetchone()

    if not user_hash or not check_password_hash(user_hash["password_hash"], current_password):
        flash("Joriy parol noto'g'ri.", "error")
        conn.close()
        return redirect(url_for("profile_settings"))

    # Yangi parolni saqlash
    new_password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))

    conn.commit()
    conn.close()

    flash("Parol muvaffaqiyatli o'zgartirildi!", "success")
    return redirect(url_for("profile_settings"))

@app.route("/profile/settings")
def profile_settings():
    # Har qanday turdagi foydalanuvchi (user, staff, courier, super_admin) kirishi mumkin
    if not (session.get("user_id") or session.get("staff_id") or session.get("courier_id") or session.get("super_admin")):
        flash("Profil sozlamalarini ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    return render_template("profile_settings.html")

@app.route("/settings")
def general_settings():
    # Har qanday turdagi foydalanuvchi (user, staff, courier, super_admin) kirishi mumkin
    if not (session.get("user_id") or session.get("staff_id") or session.get("courier_id") or session.get("super_admin")):
        flash("Umumi sozlamalarni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("index"))

    return render_template("general_settings.html")

@app.route("/logout")
def logout():
    user_name = session.get("user_name", "")
    session.clear()
    flash(f"Tizimdan chiqdingiz. Xayr, {user_name}!", "info")
    return redirect(url_for("index"))

# ---- USER ----
@app.route("/user", methods=["GET", "POST"])
def user_page():
    if request.method == "POST":
        print("DEBUG: POST so'rov keldi /user endpoint ga")

        # Foydalanuvchi session'dan ismni olish
        if not session.get("user_id"):
            print("DEBUG: User ID session da yo'q")
            flash("Buyurtma berish uchun avval tizimga kiring.", "error")
            return redirect(url_for("login"))

        name = session.get("user_name", "")
        user_id = session.get("user_id")

        if not name:
            print("DEBUG: User name session da yo'q")
            flash("Foydalanuvchi ma'lumotlari topilmadi.", "error")
            return redirect(url_for("login"))

        print(f"DEBUG: Buyurtma berish boshlandi - User ID: {user_id}, Name: {name}")
        print(f"DEBUG: Form ma'lumotlari: {dict(request.form)}")

        # Foydalanuvchi profilidan ma'lumotlarni olish
        conn_profile = get_db()
        cur_profile = conn_profile.cursor()
        cur_profile.execute("SELECT phone, address, card_number FROM users WHERE id = ?", (user_id,))
        user_profile = cur_profile.fetchone()
        conn_profile.close()

        # Session ga profil ma'lumotlarini saqlash
        if user_profile:
            session['user_phone'] = user_profile['phone'] or ''
            session['user_address'] = user_profile['address'] or ''
            session['user_card_number'] = user_profile['card_number'] or ''

        session_id = get_session_id()
        conn = get_db()

        # Savatchani tekshirish
        cart_items = get_cart_items(conn, session_id, user_id)
        if not cart_items:
            flash("Savatchangiz bo'sh. Avval taom tanlang.", "error")
            conn.close()
            return redirect(url_for("menu"))

        try:
            # Profil ma'lumotlarini yangilash (agar yangi ma'lumotlar berilgan bo'lsa)
            home_address = request.form.get("home_address", "").strip()
            customer_phone_new = request.form.get("customer_phone", "").strip()

            print(f"DEBUG: Form ma'lumotlari - home_address: {home_address}, customer_phone: {customer_phone_new}")

            # Foydalanuvchi profilini yangilash
            if home_address or customer_phone_new:
                cur_update = conn.cursor()
                if home_address:
                    cur_update.execute("UPDATE users SET address = ? WHERE id = ?", (home_address, user_id))
                    session['user_address'] = home_address
                if customer_phone_new:
                    cur_update.execute("UPDATE users SET phone = ? WHERE id = ?", (customer_phone_new, user_id))
                    session['user_phone'] = customer_phone_new
                conn.commit()

            tno = next_ticket_no(conn)
            eta_minutes = calc_eta_minutes(conn)
            now = get_current_time()
            eta_time = now + datetime.timedelta(minutes=eta_minutes)
            total = get_cart_total(conn, session_id, user_id)

            print(f"DEBUG: Buyurtma ma'lumotlari - ticket: {tno}, total: {total}")

            cur = conn.cursor()
            # Buyurtma yaratish - dostavka manzili bor bo'lsa delivery, yo'q bo'lsa dine_in
            order_type = request.form.get("order_type", "dine_in")
            delivery_address = request.form.get("delivery_address", "").strip()
            delivery_latitude = request.form.get("delivery_latitude", "")
            delivery_longitude = request.form.get("delivery_longitude", "")
            delivery_distance = request.form.get("delivery_distance", 0)
            delivery_map_url = request.form.get("delivery_map_url", "")
            customer_note = request.form.get("customer_note", "")

            # Profil ma'lumotlaridan olish
            customer_phone = session.get('user_phone', '')
            card_number = session.get('user_card_number', '') or request.form.get("card_number", "").strip()

            # Masofa va vaqtni float ga aylantirish
            try:
                delivery_distance = float(delivery_distance) if delivery_distance else 0
            except ValueError:
                delivery_distance = 0

            # Kuryer yetkazish vaqti (30 daqiqa default)
            courier_delivery_time = 30

            # Delivery uchun ETA ni qayta hisoblash
            if order_type == "delivery":
                eta_time = now + datetime.timedelta(minutes=eta_minutes + courier_delivery_time)

            cur.execute("""
                INSERT INTO orders (user_id, customer_name, ticket_no, order_type, status, delivery_address, delivery_distance, delivery_latitude, delivery_longitude, delivery_map_url, customer_note, customer_phone, card_number, created_at, eta_time)
                VALUES (?, ?, ?, ?, 'waiting', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (user_id, name, tno, order_type, delivery_address, delivery_distance, delivery_latitude, delivery_longitude, delivery_map_url, customer_note, customer_phone, card_number, now.isoformat(), eta_time.isoformat()))

            order_id = cur.lastrowid

            # Savatchadagi mahsulotlarni order_details ga ko'chirish va JSON uchun to'plash
            order_items_for_json = []
            for item in cart_items:
                cur.execute("""
                    INSERT INTO order_details (order_id, menu_item_id, quantity, price)
                    SELECT ?, ci.menu_item_id, ci.quantity, mi.price
                    FROM cart_items ci
                    JOIN menu_items mi ON ci.menu_item_id = mi.id
                    WHERE ci.id = ?
                """, (order_id, item['id']))

                # JSON uchun mahsulot ma'lumotlarini to'plash
                order_items_for_json.append({
                    'nomi': item['name'],
                    'miqdori': item['quantity'],
                    'narxi': item['price'],
                    'jami': item['total']
                })

            # Chek yaratish
            receipt_number = f"R{tno}{now.strftime('%H%M%S')}"
            cashback_percentage = 1.0
            cashback_amount = total * (cashback_percentage / 100)

            cur.execute("""
                INSERT INTO receipts (order_id, receipt_number, total_amount, cashback_amount, cashback_percentage, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (order_id, receipt_number, total, cashback_amount, cashback_percentage, now.isoformat()))

            # Savatchani tozalash
            clear_cart(conn, session_id, user_id)

            conn.commit()

            # Foydalanuvchini JSON fayliga saqlash
            save_user_to_json(name, tno, now, order_items_for_json)

            print(f"DEBUG: Buyurtma muvaffaqiyatli yaratildi - ticket: {tno}")

        except Exception as e:
            print(f"ERROR: Buyurtma berishda xatolik: {str(e)}")
            logging.error(f"Buyurtma berishda xatolik: {str(e)}")
            flash("Buyurtma berishda xatolik yuz berdi. Qaytadan urinib ko'ring.", "error")
            return redirect(url_for("cart"))
        finally:
            conn.close()
        return redirect(url_for("user_success", ticket_no=tno))
    return redirect(url_for("menu"))

@app.route("/user/success/<int:ticket_no>")
def user_success(ticket_no):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE ticket_no=? ORDER BY id DESC LIMIT 1;", (ticket_no,))
    order = cur.fetchone()
    conn.close()
    if not order:
        flash("Buyurtma topilmadi.", "error")
        return redirect(url_for("user_page"))
    # valmis bo'lish vaqti
    eta_time = datetime.datetime.fromisoformat(order["eta_time"])
    return render_template("user_success.html", order=order, eta_hhmm=eta_time.strftime("%H:%M"))

@app.route("/user/status/<int:ticket_no>")
def user_status(ticket_no):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE ticket_no=? ORDER BY id DESC LIMIT 1;", (ticket_no,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return jsonify({"ok": False, "error": "not_found"}), 404

    queue_position = 0
    if order["status"] == "waiting":
        queue_position = get_user_queue_position(conn, ticket_no)

    conn.close()
    return jsonify({
        "ok": True,
        "status": order["status"],
        "ticket_no": order["ticket_no"],
        "queue_position": queue_position
    })

# ---- COURIER AUTH ----
@app.route("/courier-secure-login-k4m7p", methods=["GET", "POST"])
def courier_login():
    if request.method == "POST":
        courier_id = request.form.get("courier_id", "").strip()
        password = request.form.get("password", "")
        if not courier_id or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("courier_login"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM couriers WHERE id=?;", (courier_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            # Faollik vaqtini yangilash va ishchi soatlarini hisoblash
            now = get_current_time().isoformat()

            # Yangi connection yaratish
            conn_update = get_db()
            cur_update = conn_update.cursor()

            # Agar avvalgi faollik vaqti mavjud bo'lsa, ishchi soatlarni yangilash
            if row["last_activity"]:
                try:
                    last_activity = datetime.datetime.fromisoformat(row["last_activity"])
                    current_time = get_current_time()
                    time_diff = current_time - last_activity

                    # Agar 8 soatdan kam bo'lsa, ishchi vaqtga qo'shish
                    if time_diff.total_seconds() < 28800:  # 8 soat
                        additional_hours = time_diff.total_seconds() / 3600
                        cur_update.execute("UPDATE couriers SET total_hours = COALESCE(total_hours, 0) + ?, last_activity = ? WHERE id = ?", 
                                   (additional_hours, now, courier_id))
                    else:
                        cur_update.execute("UPDATE couriers SET last_activity = ? WHERE id = ?", (now, courier_id))
                except:
                    cur_update.execute("UPDATE couriers SET last_activity = ? WHERE id = ?", (now, courier_id))
            else:
                cur_update.execute("UPDATE couriers SET last_activity = ? WHERE id = ?", (now, courier_id))

            conn_update.commit()
            conn_update.close()

        conn.close()
        if not row or not check_password_hash(row["password_hash"], password):
            flash("Noto'g'ri ID yoki parol.", "error")
            return redirect(url_for("courier_login"))
        session["courier_id"] = row["id"]
        session["courier_name"] = f"{row['first_name']} {row['last_name']}"
        return redirect(url_for("courier_dashboard"))
    return render_template("courier_login.html")

@app.route("/courier-register-secure-p8x3m", methods=["GET", "POST"])
def courier_register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        passport_series = request.form.get("passport_series", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        password = request.form.get("password", "")

        if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("courier_register"))

        conn = get_db()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        now = get_current_time()
        try:
            cur.execute("""
                INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))
        except sqlite3.OperationalError:
            # Agar birth_date ustuni mavjud bo'lmasa, uni qo'shish
            cur.execute("ALTER TABLE couriers ADD COLUMN birth_date TEXT;")
            cur.execute("""
                INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

        new_id = cur.lastrowid
        # ID kamida 5 ta raqamdan iborat bo'lishi uchun
        if new_id < 10000:
            cur.execute("UPDATE couriers SET id = ? WHERE id = ?", (10000 + new_id, new_id))
            new_id = 10000 + new_id

        conn.commit()
        conn.close()

        flash(f"Kuryer sifatida ro'yxatdan o'tdingiz. Sizning ID raqamingiz: {new_id}", "success")
        return redirect(url_for("courier_login"))

    return render_template("courier_register.html")

@app.route("/courier/dashboard")
def courier_dashboard():
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    conn = get_db()
    cur = conn.cursor()
    courier_id = session.get("courier_id")

    # Barcha ready delivery buyurtmalar va kuryerga tegishli buyurtmalarni olish
    cur.execute("""
        SELECT o.*, 
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE (o.order_type = 'delivery' AND o.status = 'ready') 
           OR (o.courier_id = ? AND o.status IN ('on_way', 'delivered'))
        GROUP BY o.id
        ORDER BY 
            CASE 
                WHEN o.status = 'ready' THEN 1
                WHEN o.status = 'on_way' THEN 2
                WHEN o.status = 'delivered' THEN 3
                ELSE 4
            END,
            o.created_at ASC
    """, (courier_id,))
    delivery_orders = cur.fetchall()

    # Kuryer statistikasini olish
    cur.execute("SELECT deliveries_completed, total_hours FROM couriers WHERE id = ?", (courier_id,))
    courier_stats = cur.fetchone()

    # Faol buyurtmalar sonini olish
    cur.execute("SELECT COUNT(*) FROM orders WHERE courier_id = ? AND status = 'on_way'", (courier_id,))
    active_orders = cur.fetchone()[0]

    # Session ga statistikani saqlash
    if courier_stats:
        session['courier_deliveries'] = courier_stats[0] or 0
        session['courier_hours'] = round(courier_stats[1] or 0, 1)
    session['courier_active_orders'] = active_orders

    conn.close()
    return render_template("courier_dashboard.html", orders=delivery_orders)

@app.route("/courier/order/<int:order_id>/take", methods=["POST"])
def courier_take_order(order_id):
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    courier_id = session.get("courier_id")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE orders SET status='on_way', courier_id=? WHERE id=? AND status='ready'", (courier_id, order_id))
    conn.commit()
    conn.close()

    flash("Buyurtma olib ketildi!", "success")
    return redirect(url_for("courier_dashboard"))

@app.route("/courier/order/<int:order_id>/delivered", methods=["POST"])
def courier_mark_delivered(order_id):
    if "courier_id" not in session:
        return redirect(url_for("courier_login"))

    courier_id = session.get("courier_id")
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE orders SET status='delivered' WHERE id=? AND courier_id=?", (order_id, courier_id))

    # Kuryerning yetkazib bergan buyurtmalar sonini oshirish
    cur.execute("UPDATE couriers SET deliveries_completed = COALESCE(deliveries_completed, 0) + 1 WHERE id = ?", (courier_id,))

    conn.commit()
    conn.close()

    flash("Buyurtma yetkazib berildi!", "success")
    return redirect(url_for("courier_dashboard"))

@app.route("/courier/set-price-time", methods=["POST"])
def courier_set_price_time():
    if "courier_id" not in session:
        return jsonify({"success": False, "message": "Kuryer tizimga kirmagan"}), 401

    data = request.get_json()
    order_id = data.get("order_id")
    price = data.get("price")
    delivery_time = data.get("delivery_time")

    if not all([order_id, price, delivery_time]):
        return jsonify({"success": False, "message": "Barcha maydonlarni to'ldiring"})

    try:
        price = float(price)
        delivery_time = int(delivery_time)

        if price <= 0 or delivery_time <= 0:
            return jsonify({"success": False, "message": "Narx va vaqt musbat bo'lishi kerak"})

        conn = get_db()
        cur = conn.cursor()

        # Buyurtma mavjudligini va statusini tekshirish
        cur.execute("SELECT * FROM orders WHERE id = ? AND status = 'ready'", (order_id,))
        order = cur.fetchone()

        if not order:
            conn.close()
            return jsonify({"success": False, "message": "Buyurtma topilmadi yoki tayyor emas"})

        # Narx va vaqtni yangilash
        cur.execute("""
            UPDATE orders 
            SET courier_price = ?, courier_delivery_minutes = ?, delivery_price = ?
            WHERE id = ?
        """, (price, delivery_time, price, order_id))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Narx va vaqt belgilandi"})

    except Exception as e:
        logging.error(f"Kuryer narx belgilashda xatolik: {str(e)}")
        return jsonify({"success": False, "message": "Server xatoligi"}), 500

@app.route("/courier/logout")
def courier_logout():
    session.pop("courier_id", None)
    session.pop("courier_name", None)
    return redirect(url_for("index"))

# ---- STAFF AUTH ----
@app.route("/staff-secure-login-w7m2k", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        staff_id = request.form.get("staff_id", "").strip()
        password = request.form.get("password", "")
        if not staff_id or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("staff_login"))

        # ID raqam ekanligini va kamida 5 ta raqamdan iborat ekanligini tekshirish
        try:
            staff_id_int = int(staff_id)
            if staff_id_int < 10000:
                flash("ID kamida 5 ta raqamdan iborat bo'lishi kerak.", "error")
                return redirect(url_for("staff_login"))
        except ValueError:
            flash("ID raqam bo'lishi kerak.", "error")
            return redirect(url_for("staff_login"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM staff WHERE id=?;", (staff_id_int,))
        row = cur.fetchone()

        if row and check_password_hash(row["password_hash"], password):
            # Faollik vaqtini yangilash
            now = get_current_time().isoformat()
            try:
                cur.execute("UPDATE staff SET last_activity = ? WHERE id = ?", (now, staff_id_int))
                conn.commit()
            except Exception as e:
                pass

            session["staff_id"] = row["id"]
            session["staff_name"] = f"{row['first_name']} {row['last_name']}"
            flash(f"Xush kelibsiz, {row['first_name']}!", "success")
            conn.close()
            return redirect(url_for("staff_dashboard"))
        else:
            conn.close()
            flash("Noto'g'ri ID yoki parol.", "error")
            return redirect(url_for("staff_login"))
    return render_template("staff_login.html")

@app.route("/admin/logout")
def staff_logout():
    # Super admin bo'lsa, super admin sessionni saqlash
    is_super_admin = session.get("super_admin", False)
    session.clear()
    if is_super_admin:
        session["super_admin"] = True
        flash("Staff sessiondan chiqildi, super admin sessioni saqlandi.", "info")
    return redirect(url_for("index"))

@app.route("/staff-register-secure-k3x8p", methods=["GET", "POST"])
def staff_register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        passport_series = request.form.get("passport_series", "").strip()
        passport_number = request.form.get("passport_number", "").strip()
        password = request.form.get("password", "")

        if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("staff_register"))

        conn = get_db()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        now = get_current_time()
        cur.execute("""
            INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

        new_id = cur.lastrowid
        # ID kamida 5 ta raqamdan iborat bo'lishi uchun
        if new_id < 10000:
            cur.execute("UPDATE staff SET id = ? WHERE id = ?", (10000 + new_id, new_id))
            new_id = 10000 + new_id

        conn.commit()
        conn.close()

        # Xodim ma'lumotlarini employees.json fayliga saqlash
        save_staff_to_json(first_name, last_name, birth_date, phone, new_id, now)

        flash(f"Ro'yxatdan o'tdingiz. Sizning ID raqamingiz: {new_id}", "success")
        return redirect(url_for("staff_login"))

    return render_template("staff_register.html")

# ---- STAFF DASHBOARD ----
def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Super admin yoki staff kirgan bo'lishi kerak
        if not session.get("super_admin") and not session.get("staff_id"):
            return redirect(url_for("staff_login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/admin/dashboard")
@login_required
def staff_dashboard():
    cleanup_expired_orders()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.*, 
               GROUP_CONCAT(mi.name || ' x' || od.quantity) as order_items
        FROM orders o
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        GROUP BY o.id
        ORDER BY 
            CASE 
                WHEN o.status = 'ready' THEN 1
                WHEN o.status = 'waiting' THEN 2
                WHEN o.status = 'served' THEN 3
                WHEN o.status = 'cancelled' THEN 4
                ELSE 5
            END,
            o.eta_time ASC,
            o.created_at ASC
    """)
    orders = cur.fetchall()
    conn.close()
    return render_template("staff_dashboard.html", orders=orders, staff_name=session.get("staff_name"))

@app.route("/admin/menu")
@login_required
def staff_menu():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu_items ORDER BY category, name")
    menu_items = cur.fetchall()
    conn.close()
    return render_template("staff_menu.html", menu_items=menu_items, staff_name=session.get("staff_name"))

@app.route("/admin/add_menu_item", methods=["POST"])
@login_required
def add_menu_item():
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "")
    category = request.form.get("category", "")
    description = request.form.get("description", "").strip()

    if not all([name, price, category]):
        flash("Barcha majburiy maydonlarni to'ldiring.", "error")
        return redirect(url_for("staff_menu"))

    try:
        price = float(price)
    except ValueError:
        flash("Narx raqam bo'lishi kerak.", "error")
        return redirect(url_for("staff_menu"))

    # Rasm yuklash
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            # Rasm faylini saqlash
            import uuid
            from werkzeug.utils import secure_filename

            # Static/images papkasini yaratish
            images_dir = os.path.join('static', 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            # Fayl nomini xavfsiz qilish
            filename = secure_filename(file.filename)
            # Unikal nom yaratish
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(images_dir, unique_filename)

            try:
                file.save(file_path)
                image_url = f"/static/images/{unique_filename}"
            except Exception as e:
                flash("Rasmni yuklashda xatolik yuz berdi.", "error")
                return redirect(url_for("staff_menu"))

    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()

    # Jadval tuzilishini tekshirish va kerakli ustunlarni qo'shish
    cur.execute("PRAGMA table_info(menu_items);")
    columns = [col[1] for col in cur.fetchall()]

    if 'description' not in columns:
        cur.execute("ALTER TABLE menu_items ADD COLUMN description TEXT;")

    if 'image_url' not in columns:
        cur.execute("ALTER TABLE menu_items ADD COLUMN image_url TEXT;")

    # Ma'lumotni kiritish
    cur.execute("INSERT INTO menu_items (name, price, category, description, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
               (name, price, category, description, image_url, now))

    conn.commit()
    conn.close()
    flash("Yangi mahsulot qo'shildi!", "success")
    return redirect(url_for("staff_menu"))

@app.route("/admin/toggle_menu_item/<int:item_id>", methods=["POST"])
@login_required
def toggle_menu_item(item_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE menu_items SET available = NOT available WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Mahsulot holati o'zgartirildi.", "success")
    return redirect(url_for("staff_menu"))

@app.route("/admin/edit_menu_item/<int:item_id>", methods=["POST"])
@login_required
def edit_menu_item(item_id):
    name = request.form.get("name", "").strip()
    price = request.form.get("price", "")
    description = request.form.get("description", "").strip()
    discount_percentage = request.form.get("discount_percentage", "0")

    if not all([name, price]):
        flash("Nom va narx majburiy.", "error")
        return redirect(url_for("staff_menu"))

    try:
        price = float(price)
        discount_percentage = float(discount_percentage)
        if discount_percentage < 0 or discount_percentage > 100:
            flash("Skidka 0 dan 100 gacha bo'lishi kerak.", "error")
            return redirect(url_for("staff_menu"))
    except ValueError:
        flash("Narx va skidka raqam bo'lishi kerak.", "error")
        return redirect(url_for("staff_menu"))

    # Rasm yuklash
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            import uuid
            from werkzeug.utils import secure_filename

            # Static/images papkasini yaratish
            images_dir = os.path.join('static', 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            # Fayl nomini xavfsiz qilish
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(images_dir, unique_filename)

            try:
                file.save(file_path)
                image_url = f"/static/images/{unique_filename}"
            except Exception as e:
                flash("Rasmni yuklashda xatolik yuz berdi.", "error")
                return redirect(url_for("staff_menu"))

    conn = get_db()
    cur = conn.cursor()

    if image_url:
        cur.execute("""
            UPDATE menu_items 
            SET name = ?, price = ?, description = ?, discount_percentage = ?, image_url = ?
            WHERE id = ?
        """, (name, price, description, discount_percentage, image_url, item_id))
    else:
        cur.execute("""
            UPDATE menu_items 
            SET name = ?, price = ?, description = ?, discount_percentage = ?
            WHERE id = ?
        """, (name, price, description, discount_percentage, item_id))

    conn.commit()
    conn.close()
    flash("Mahsulot tahrirlandi!", "success")
    return redirect(url_for("staff_menu"))

@app.route("/admin/order/<int:order_id>/served", methods=["POST"])
@login_required
def staff_mark_served(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='served' WHERE id=?;", (order_id,))

    # Xodimning bajargan buyurtmalar sonini oshirish
    staff_id = session.get("staff_id")
    if staff_id:
        cur.execute("UPDATE staff SET orders_handled = COALESCE(orders_handled, 0) + 1 WHERE id = ?", (staff_id,))

    conn.commit()
    conn.close()
    flash("Buyurtma foydalanuvchiga berildi sifatida belgilandi.", "success")
    return redirect(url_for("staff_dashboard"))

@app.route("/admin/order/<int:order_id>/ready", methods=["POST"])
@login_required
def staff_mark_ready(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='ready' WHERE id=?;", (order_id,))

    # Xodimning bajargan buyurtmalar sonini oshirish
    staff_id = session.get("staff_id")
    if staff_id:
        cur.execute("UPDATE staff SET orders_handled = COALESCE(orders_handled, 0) + 1 WHERE id = ?", (staff_id,))

    conn.commit()
    conn.close()
    flash("Buyurtma 'tayyor' deb belgilandi.", "success")
    return redirect(url_for("staff_dashboard"))

@app.route("/admin/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def staff_mark_cancel(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='cancelled' WHERE id=?;", (order_id,))
    conn.commit()
    conn.close()
    flash("Buyurtma bekor qilindi.", "warning")
    return redirect(url_for("staff_dashboard"))



@app.route("/user/cancel/<int:ticket_no>", methods=["POST"])
def user_cancel(ticket_no):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE ticket_no=? ORDER BY id DESC LIMIT 1", (ticket_no,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return jsonify({"ok": False, "msg": "Buyurtma topilmadi"}), 404
    if order['status'] in ('served', 'ready'):
        conn.close()
        return jsonify({"ok": False, "msg": "Buyurtma allaqachon tayyor yoki berilgan, bekor qilib bo'lmaydi"}), 400
    cur.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order['id'],))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "msg": "Buyurtma bekor qilindi"})
@app.route("/admin/orders.json")
@login_required
def staff_orders_json():
    cleanup_expired_orders()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at ASC;")
    rows = cur.fetchall()
    conn.close()
    data = [dict(row) for row in rows]
    return jsonify(data)

@app.route("/admin/employees")
@login_required
def staff_employees():
    """Xodimlar ro'yxatini ko'rish"""
    employees_file = 'employees.json'
    employees = []

    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            employees = []

    return render_template("staff_employees.html", employees=employees, staff_name=session.get("staff_name"))

# ---- SUPER ADMIN ----
# Super admin kredentsiallari
SUPER_ADMIN_USERNAME = "masteradmin"
SUPER_ADMIN_PASSWORD = "SuperAdmin2025!@#$%"

@app.route("/super-admin-control-panel-master-z8x9k", methods=["GET", "POST"])
def super_admin_login():
    if request.method == "GET":
        return render_template("super_admin_login.html")

    # POST method
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
        session["super_admin"] = True
        flash("Super admin paneliga kirish muvaffaqiyatli!", "success")
        return redirect(url_for("super_admin_dashboard"))
    else:
        flash("Noto'g'ri login yoki parol!", "error")
        return render_template("super_admin_login.html")

@app.route("/super-admin-dashboard-ultimate-m4st3r")
def super_admin_dashboard():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = get_db()
    cur = conn.cursor()

    # Xodimlar ma'lumotlari (soatlar va buyurtmalar bilan)
    cur.execute("""
        SELECT s.*
        FROM staff s
        ORDER BY s.created_at DESC
    """)
    staff_db = cur.fetchall()

    # Kuryerlar ma'lumotlari
    cur.execute("""
        SELECT c.*
        FROM couriers c
        ORDER BY c.created_at DESC
    """)
    couriers_db = cur.fetchall()

    # Foydalanuvchilarni olish
    cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    users_db = cur.fetchall()

    # JSON fayldan ham foydalanuvchilarni olish
    users_file = 'users.json'
    users_json = []
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users_json = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            users_json = []

    # Savollarni olish
    cur.execute("SELECT * FROM questions ORDER BY created_at DESC")
    questions = cur.fetchall()

    # Buyurtmalar statistikasi
    cur.execute("SELECT COUNT(*) FROM orders")
    result = cur.fetchone()
    total_orders = result[0] if result else 0

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting'")
    result = cur.fetchone()
    waiting_orders = result[0] if result else 0

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='ready'")
    result = cur.fetchone()
    ready_orders = result[0] if result else 0

    cur.execute("SELECT COUNT(*) FROM orders WHERE status='served'")
    result = cur.fetchone()
    served_orders = result[0] if result else 0

    # Bu oylik statistika
    current_month = get_current_time().strftime("%Y-%m")
    cur.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (f"{current_month}%",))
    result = cur.fetchone()
    month_orders = result[0] if result else 0

    conn.close()

    stats = {
        'total_orders': total_orders,
        'waiting_orders': waiting_orders,
        'ready_orders': ready_orders,
        'served_orders': served_orders,
        'month_orders': month_orders,
        'total_staff': len(staff_db),
        'total_couriers': len(couriers_db),
        'total_users': len(users_db),
        'total_users_json': len(users_json)
    }

    return render_template("super_admin_dashboard.html", 
                         staff_db=staff_db,
                         couriers_db=couriers_db,
                         users_db=users_db,
                         users_json=users_json,
                         questions=questions,
                         stats=stats)

@app.route("/super-admin/delete-staff/<int:staff_id>", methods=["POST"])
def super_admin_delete_staff(staff_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    conn.commit()
    conn.close()

    # JSON fayldan ham o'chirish
    employees_file = 'employees.json'
    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)

            employees = [emp for emp in employees if emp.get('id') != staff_id]

            with open(employees_file, 'w', encoding='utf-8') as f:
                json.dump(employees, f, ensure_ascii=False, indent=2)
        except:
            pass

    flash(f"Xodim #{staff_id} o'chirildi.", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/add-staff", methods=["POST"])
def super_admin_add_staff():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    birth_date = request.form.get("birth_date", "").strip()
    phone = request.form.get("phone", "").strip()
    passport_series = request.form.get("passport_series", "").strip()
    passport_number = request.form.get("passport_number", "").strip()
    password = request.form.get("password", "")

    if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)
    now = get_current_time()
    cur.execute("""
        INSERT INTO staff (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

    new_id = cur.lastrowid
    # ID kamida 5 ta raqamdan iborat bo'lishi uchun
    if new_id < 10000:
        cur.execute("UPDATE staff SET id = ? WHERE id = ?", (10000 + new_id, new_id))
        new_id = 10000 + new_id

    conn.commit()
    conn.close()

    # JSON fayliga ham saqlash
    save_staff_to_json(first_name, last_name, birth_date, phone, new_id, now)

    flash(f"Yangi xodim qo'shildi. ID: {new_id}", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/add-courier", methods=["POST"])
def super_admin_add_courier():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    birth_date = request.form.get("birth_date", "").strip()
    phone = request.form.get("phone", "").strip()
    passport_series = request.form.get("passport_series", "").strip()
    passport_number = request.form.get("passport_number", "").strip()
    password = request.form.get("password", "")

    if not all([first_name, last_name, birth_date, phone, passport_series, passport_number, password]):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)
    now = get_current_time()
    cur.execute("""
        INSERT INTO couriers (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, now.isoformat()))

    new_id = cur.lastrowid
    # ID kamida 5 ta raqamdan iborat bo'lishi uchun
    if new_id < 10000:
        cur.execute("UPDATE couriers SET id = ? WHERE id = ?", (10000 + new_id, new_id))
        new_id = 10000 + new_id

    conn.commit()
    conn.close()

    flash(f"Yangi kuryer qo'shildi. ID: {new_id}", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/delete-user", methods=["POST"])
def super_admin_delete_user():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    ticket_no = request.form.get("ticket_no")

    if not ticket_no:
        flash("Buyurtma raqamini kiriting.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        ticket_no = int(ticket_no)
    except ValueError:
        flash("Buyurtma raqami raqam bo'lishi kerak.", "error")
        return redirect(url_for("super_admin_dashboard"))

    # JSON fayldan o'chirish
    users_file = 'users.json'
    deleted = False

    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)

            original_count = len(users)
            users = [user for user in users if user.get('buyurtma_raqami') != ticket_no]

            if len(users) < original_count:
                deleted = True
                with open(users_file, 'w', encoding='utf-8') as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
        except:
            pass

    # Ma'lumotlar bazasidan ham o'chirish
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE ticket_no = ?", (ticket_no,))
    order = cur.fetchone()

    if order:
        # Order details ni ham o'chirish
        cur.execute("DELETE FROM order_details WHERE order_id = ?", (order['id'],))
        # Buyurtmani o'chirish
        cur.execute("DELETE FROM orders WHERE ticket_no = ?", (ticket_no,))
        conn.commit()
        deleted = True

    conn.close()

    if deleted:
        flash(f"Buyurtma #{ticket_no} va unga tegishli barcha ma'lumotlar o'chirildi.", "success")
    else:
        flash(f"Buyurtma #{ticket_no} topilmadi.", "error")

    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/logout")
def super_admin_logout():
    session.pop("super_admin", None)
    flash("Super admin panelidan chiqildi.", "info")
    return redirect(url_for("index"))

@app.route("/super-admin/delete-courier/<int:courier_id>", methods=["POST"])
def super_admin_delete_courier(courier_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM couriers WHERE id = ?", (courier_id,))
    conn.commit()
    conn.close()

    flash(f"Kuryer #{courier_id} o'chirildi.", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/delete-user-db/<int:user_id>", methods=["POST"])
def super_admin_delete_user_db(user_id):
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash(f"Foydalanuvchi #{user_id} o'chirildi.", "success")
    return redirect(url_for("super_admin_dashboard"))

@app.route("/super-admin/reset-staff-password", methods=["POST"])
def super_admin_reset_staff_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    staff_id = data.get("staff_id")
    new_password = data.get("new_password")

    if not staff_id or not new_password:
        return jsonify({"success": False, "message": "Noto'g'ri ma'lumotlar"})

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE staff SET password_hash = ? WHERE id = ?", (password_hash, staff_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Parol yangilandi"})

@app.route("/super-admin/reset-courier-password", methods=["POST"])
def super_admin_reset_courier_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    courier_id = data.get("courier_id")
    new_password = data.get("new_password")

    if not courier_id or not new_password:
        return jsonify({"success": False, "message": "Noto'g'ri ma'lumotlar"})

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE couriers SET password_hash = ? WHERE id = ?", (password_hash, courier_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Parol yangilandi"})

@app.route("/super-admin/reset-user-password", methods=["POST"])
def super_admin_reset_user_password():
    if not session.get("super_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.json
    user_id = data.get("user_id")
    new_password = data.get("new_password")

    if not user_id or not new_password:
        return jsonify({"success": False, "message": "Noto'g'ri ma'lumotlar"})

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Parol yangilandi"})

@app.route("/super-admin/get-orders")
def super_admin_get_orders():
    if not session.get("super_admin"):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    conn.close()

    return jsonify([dict(order) for order in orders])

@app.route("/super-admin/get-menu")
def super_admin_get_menu():
    if not session.get("super_admin"):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu_items ORDER BY category, name")
    items = cur.fetchall()
    conn.close()

    return jsonify([dict(item) for item in items])

@app.route("/super-admin/get-receipts")
def super_admin_get_receipts():
    if not session.get("super_admin"):
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM receipts ORDER BY created_at DESC LIMIT 100")
    receipts = cur.fetchall()
    conn.close()

    return jsonify([dict(receipt) for receipt in receipts])

@app.route("/super-admin/add-menu-item", methods=["POST"])
def super_admin_add_menu_item():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))

    name = request.form.get("name", "").strip()
    price = request.form.get("price", "")
    category = request.form.get("category", "")
    description = request.form.get("description", "").strip()

    if not all([name, price, category]):
        flash("Barcha majburiy maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    try:
        price = float(price)
    except ValueError:
        flash("Narx raqam bo'lishi kerak.", "error")
        return redirect(url_for("super_admin_dashboard"))

    # Rasm yuklash
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            import uuid
            from werkzeug.utils import secure_filename

            images_dir = os.path.join('static', 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(images_dir, unique_filename)

            try:
                file.save(file_path)
                image_url = f"/static/images/{unique_filename}"
            except Exception as e:
                flash("Rasmni yuklashda xatolik yuz berdi.", "error")
                return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()

    cur.execute("INSERT INTO menu_items (name, price, category, description, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
               (name, price, category, description, image_url, now))

    conn.commit()
    conn.close()
    flash("Yangi mahsulot qo'shildi!", "success")
    return redirect(url_for("super_admin_dashboard"))

# ---- YANGI SAHIFALAR ----
@app.route("/add_to_favorites/<int:menu_item_id>", methods=["POST"])
def add_to_favorites(menu_item_id):
    if not session.get("user_id"):
        flash("Sevimlilarni qo'shish uchun tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()

    try:
        cur.execute("INSERT INTO favorites (user_id, menu_item_id, created_at) VALUES (?, ?, ?)",
                   (user_id, menu_item_id, now))
        conn.commit()
        flash("Sevimlilar ro'yxatiga qo'shildi!", "success")
    except sqlite3.IntegrityError:
        flash("Bu mahsulot allaqachon sevimlilar ro'yxatida!", "warning")

    conn.close()
    return redirect(url_for("menu"))

@app.route("/remove_from_favorites/<int:menu_item_id>", methods=["POST"])
def remove_from_favorites(menu_item_id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM favorites WHERE user_id = ? AND menu_item_id = ?", (user_id, menu_item_id))
    conn.commit()
    conn.close()
    flash("Sevimlilardan olib tashlandi!", "success")
    return redirect(url_for("favorites"))

@app.route("/favorites")
def favorites():
    if not session.get("user_id"):
        flash("Sevimlilarni ko'rish uchun tizimga kiring.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT mi.* FROM favorites f
        JOIN menu_items mi ON f.menu_item_id = mi.id
        WHERE f.user_id = ? AND mi.available = 1
        ORDER BY f.created_at DESC
    """, (user_id,))
    favorites = cur.fetchall()
    conn.close()

    return render_template("favorites.html", favorites=favorites)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, subject, message]):
            flash("Ism, mavzu va xabar maydoni majburiy.", "error")
            return redirect(url_for("contact"))

        conn = get_db()
        cur = conn.cursor()
        now = get_current_time().isoformat()
        cur.execute("""
            INSERT INTO questions (user_name, email, phone, subject, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, phone, subject, message, now))
        conn.commit()
        conn.close()

        flash("Savolingiz muvaffaqiyatli yuborildi! Tez orada javob beramiz.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/downloads')
def downloads():
    return render_template('downloads.html')

@app.route("/api/validate-address", methods=["POST"])
def api_validate_address():
    """Manzilni tekshirish API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"valid": False, "message": "Ma'lumot yuborilmagan"})

        address = data.get("address", "").strip()

        if not address:
            return jsonify({"valid": False, "message": "Manzil kiritilmagan"})

        is_valid, message = validate_delivery_address(address)
        distance = calculate_delivery_distance(address) if is_valid else 0

        return jsonify({
            "valid": is_valid,
            "message": message,
            "distance": round(distance, 1),
            "delivery_price": round(distance * 2000, 0)  # Har km uchun 2000 so'm
        })
    except Exception as e:
        logging.error(f"Manzil tekshirishda xatolik: {str(e)}")
        return jsonify({"valid": False, "message": "Server xatoligi"}), 500

@app.route("/api/search-places", methods=["POST"])
def api_search_places():
    """Joylarni qidirish API"""
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"places": []})

    places_result = get_places_with_serper(f"{query} Toshkent")

    if places_result and places_result.get('places'):
        places = []
        for place in places_result['places'][:5]:  # Faqat birinchi 5 ta natija
            places.append({
                "title": place.get("title", ""),
                "address": place.get("address", ""),
                "position": place.get("position", {}),
                "rating": place.get("rating", 0)
            })
        return jsonify({"places": places})

    return jsonify({"places": []})

@app.route("/api/set-language", methods=["POST"])
def api_set_language():
    """Til sozlamasini saqlash"""
    try:
        data = request.get_json()
        language = data.get("language", "uz")
        font_size = data.get("font_size", "medium")

        # Til sozlamalarini session ga saqlash
        session['interface_language'] = language
        session['font_size'] = font_size

        # Til o'zgarishi bo'yicha message
        if language == 'ru':
            message = "Язык изменен на русский"
        elif language == 'en':
            message = "Language changed to English"
        else:
            message = "Til o'zgartirildi"

        return jsonify({
            "success": True, 
            "message": message,
            "language": language,
            "font_size": font_size
        })
    except Exception as e:
        logging.error(f"Til sozlamasida xatolik: {str(e)}")
        return jsonify({"success": False, "message": "Server xatoligi"}), 500

@app.route("/api/save-settings", methods=["POST"])
def api_save_settings():
    """Barcha sozlamalarni saqlash"""
    try:
        data = request.get_json()
        
        # Sozlamalarni session ga saqlash
        session['interface_language'] = data.get("language", "uz")
        session['font_size'] = data.get("font_size", "medium")
        session['dark_theme'] = data.get("dark_theme", False)

        # Success message til bo'yicha
        language = session.get('interface_language', 'uz')
        if language == 'ru':
            message = "Настройки сохранены успешно!"
        elif language == 'en':
            message = "Settings saved successfully!"
        else:
            message = "Sozlamalar muvaffaqiyatli saqlandi!"

        return jsonify({
            "success": True, 
            "message": message,
            "settings": {
                "language": session.get('interface_language'),
                "font_size": session.get('font_size'),
                "dark_theme": session.get('dark_theme')
            }
        })
    except Exception as e:
        logging.error(f"Sozlamalarni saqlashda xatolik: {str(e)}")
        return jsonify({"success": False, "message": "Server xatoligi"}), 500

@app.route("/api/set-theme", methods=["POST"])
def api_set_theme():
    """Mavzu sozlamasini saqlash"""
    try:
        data = request.get_json()
        dark_mode = data.get("dark_mode", False)

        # Session ga mavzu sozlamasini saqlash
        session['dark_theme'] = dark_mode

        return jsonify({"success": True, "message": "Mavzu o'zgartirildi"})
    except Exception as e:
        logging.error(f"Mavzu sozlamasida xatolik: {str(e)}")
        return jsonify({"success": False, "message": "Server xatoligi"}), 500

@app.route("/receipt/<int:ticket_no>")
def view_receipt(ticket_no):
    """Chekni ko'rish sahifasi"""
    conn = get_db()
    cur = conn.cursor()

    # Buyurtma va chek ma'lumotlarini olish
    cur.execute("""
        SELECT o.*, r.receipt_number, r.total_amount, r.cashback_amount, r.cashback_percentage, r.created_at as receipt_created,
               GROUP_CONCAT(mi.name || ' x' || od.quantity || ' = ' || od.price || ' som') as order_items
        FROM orders o
        LEFT JOIN receipts r ON o.id = r.order_id
        LEFT JOIN order_details od ON o.id = od.order_id
        LEFT JOIN menu_items mi ON od.menu_item_id = mi.id
        WHERE o.ticket_no = ?
        GROUP BY o.id
    """, (ticket_no,))

    order_with_receipt = cur.fetchone()
    conn.close()

    if not order_with_receipt:
        flash("Chek topilmadi.", "error")
        return redirect(url_for("index"))

    # QR kod yaratish
    receipt_dict = dict(order_with_receipt)
    qr_code_base64 = generate_qr_code(receipt_dict)

    return render_template("receipt.html", order=order_with_receipt, qr_code=qr_code_base64)



with app.app_context():
    db.create_all()

@app.route("/debug")
def debug():
    """Debug ma'lumotlari"""
    return {
        "session": dict(session),
        "user_id": session.get("user_id"),
        "user_name": session.get("user_name"),
        "logged_in": "user_id" in session
    }

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)