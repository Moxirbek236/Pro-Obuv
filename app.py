from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, datetime, json
from flask_sqlalchemy import SQLAlchemy
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_change_me")

# Database fayl yo'lini to'g'rilash
DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite3")

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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            ticket_no INTEGER NOT NULL,
            status TEXT NOT NULL, -- 'waiting' yoki 'given'
            created_at TEXT NOT NULL,
            eta_time TEXT NOT NULL
        );
    """)
    # ticketlar ketma-ketligi uchun alohida jadval
    cur.execute("""
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        );
    """)
    cur.execute("INSERT OR IGNORE INTO counters (name, value) VALUES ('ticket', 0);")
    
    # Menyu jadval
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL, -- 'food' yoki 'drink'
            available BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL
        );
    """)
    
    # Savatcha jadval
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        );
    """)
    
    # Buyurtma tafsilotlari jadval
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
    
    # Boshlang'ich taomlar qo'shish
    cur.execute("SELECT COUNT(*) FROM menu_items")
    if cur.fetchone()[0] == 0:
        now = get_current_time().isoformat()
        sample_items = [
            ('Osh', 25000, 'food', now),
            ('Manti', 20000, 'food', now),
            ('Shashlik', 30000, 'food', now),
            ('Lagmon', 22000, 'food', now),
            ('Choy', 5000, 'drink', now),
            ('Qora choy', 6000, 'drink', now),
            ('Kompot', 8000, 'drink', now),
            ('Coca Cola', 10000, 'drink', now),
        ]
        cur.executemany("INSERT INTO menu_items (name, price, category, created_at) VALUES (?, ?, ?, ?)", sample_items)
    
    conn.commit()
    conn.close()

# Flask 2.2+ da before_first_request deprecated
def ensure_orders_status_column():
    """Agar orders jadvalida status ustuni bo'lmasa, qo'shadi (migration)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(orders);")
        cols = [r[1] for r in cur.fetchall()]
        if 'status' not in cols:
            cur.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'waiting';")
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

# Ensure column exists on startup
ensure_orders_status_column()


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

def get_session_id():
    """Session ID yaratish yoki olish"""
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_cart_items(conn, session_id):
    """Savatchadagi mahsulotlarni olish"""
    cur = conn.cursor()
    cur.execute("""
        SELECT ci.id, mi.name, mi.price, ci.quantity, (mi.price * ci.quantity) as total
        FROM cart_items ci
        JOIN menu_items mi ON ci.menu_item_id = mi.id
        WHERE ci.session_id = ?
        ORDER BY ci.created_at DESC
    """, (session_id,))
    return cur.fetchall()

def get_cart_total(conn, session_id):
    """Savatchaning umumiy summasini hisoblash"""
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(mi.price * ci.quantity)
        FROM cart_items ci
        JOIN menu_items mi ON ci.menu_item_id = mi.id
        WHERE ci.session_id = ?
    """, (session_id,))
    result = cur.fetchone()[0]
    return result if result else 0

def clear_cart(conn, session_id):
    """Savatchani tozalash"""
    cur = conn.cursor()
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
    return render_template("admin_index.html")

@app.route("/display-monitor-tv-screen-z9p4n")
def admin_monitor():
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
    conn = get_db()
    cur = conn.cursor()
    
    # Mavjudligini tekshirish
    cur.execute("SELECT * FROM cart_items WHERE session_id = ? AND menu_item_id = ?", (session_id, menu_item_id))
    existing = cur.fetchone()
    
    now = get_current_time().isoformat()
    
    if existing:
        # Mavjud bo'lsa miqdorni oshirish
        cur.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (quantity, existing['id']))
    else:
        # Yangi qo'shish
        cur.execute("INSERT INTO cart_items (session_id, menu_item_id, quantity, created_at) VALUES (?, ?, ?, ?)", 
                   (session_id, menu_item_id, quantity, now))
    
    conn.commit()
    conn.close()
    flash("Mahsulot savatchaga qo'shildi!", "success")
    return redirect(url_for("menu"))

@app.route("/cart")
def cart():
    session_id = get_session_id()
    conn = get_db()
    cart_items = get_cart_items(conn, session_id)
    total = get_cart_total(conn, session_id)
    conn.close()
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/remove_from_cart/<int:cart_item_id>", methods=["POST"])
def remove_from_cart(cart_item_id):
    session_id = get_session_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart_items WHERE id = ? AND session_id = ?", (cart_item_id, session_id))
    conn.commit()
    conn.close()
    flash("Mahsulot savatchadan olib tashlandi.", "success")
    return redirect(url_for("cart"))

@app.route("/get_cart_count")
def get_cart_count():
    session_id = get_session_id()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT SUM(quantity) FROM cart_items WHERE session_id = ?", (session_id,))
    result = cur.fetchone()[0]
    count = result if result else 0
    conn.close()
    return jsonify({"count": count})

# ---- USER ----
@app.route("/user", methods=["GET", "POST"])
def user_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Ismni kiriting.", "error")
            return redirect(url_for("cart"))
            
        session_id = get_session_id()
        conn = get_db()
        
        # Savatchani tekshirish
        cart_items = get_cart_items(conn, session_id)
        if not cart_items:
            flash("Savatchangiz bo'sh. Avval taom tanlang.", "error")
            conn.close()
            return redirect(url_for("menu"))
            
        try:
            tno = next_ticket_no(conn)
            eta_minutes = calc_eta_minutes(conn)
            now = get_current_time()
            eta_time = now + datetime.timedelta(minutes=eta_minutes)
            total = get_cart_total(conn, session_id)
            
            cur = conn.cursor()
            # Buyurtma yaratish
            cur.execute("""
                INSERT INTO orders (customer_name, ticket_no, status, created_at, eta_time)
                VALUES (?, ?, 'waiting', ?, ?);
            """, (name, tno, now.isoformat(), eta_time.isoformat()))
            
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
            
            # Savatchani tozalash
            clear_cart(conn, session_id)
            
            conn.commit()
            
            # Foydalanuvchini JSON fayliga saqlash
            save_user_to_json(name, tno, now, order_items_for_json)
            
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

# ---- STAFF AUTH ----
@app.route("/staff-secure-login-w7m2k", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        staff_id = request.form.get("staff_id", "").strip()
        password = request.form.get("password", "")
        if not staff_id or not password:
            flash("ID va parolni kiriting.", "error")
            return redirect(url_for("staff_login"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM staff WHERE id=?;", (staff_id,))
        row = cur.fetchone()
        conn.close()
        if not row or not check_password_hash(row["password_hash"], password):
            flash("Noto'g'ri ID yoki parol.", "error")
            return redirect(url_for("staff_login"))
        session["staff_id"] = row["id"]
        session["staff_name"] = f"{row['first_name']} {row['last_name']}"
        return redirect(url_for("staff_dashboard"))
    return render_template("staff_login.html")

@app.route("/admin/logout")
def staff_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/staff-register-secure-k3x8p", methods=["GET", "POST"])
def staff_register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        birth_date = request.form.get("birth_date", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not all([first_name, last_name, birth_date, phone, password]):
            flash("Barcha maydonlarni to'ldiring.", "error")
            return redirect(url_for("staff_register"))

        conn = get_db()
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        now = get_current_time()
        cur.execute("""
            INSERT INTO staff (first_name, last_name, birth_date, phone, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (first_name, last_name, birth_date, phone, password_hash, now.isoformat()))
        conn.commit()
        new_id = cur.lastrowid
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
        if "staff_id" not in session:
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
    
    if not all([name, price, category]):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("staff_menu"))
    
    try:
        price = float(price)
    except ValueError:
        flash("Narx raqam bo'lishi kerak.", "error")
        return redirect(url_for("staff_menu"))
    
    conn = get_db()
    cur = conn.cursor()
    now = get_current_time().isoformat()
    cur.execute("INSERT INTO menu_items (name, price, category, created_at) VALUES (?, ?, ?, ?)",
               (name, price, category, now))
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

@app.route("/admin/order/<int:order_id>/served", methods=["POST"])
@login_required
def staff_mark_served(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='served' WHERE id=?;", (order_id,))
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
@app.route("/super-admin-control-panel-master-z8x9k")
def super_admin_login():
    return render_template("super_admin_login.html")

@app.route("/super-admin-control-panel-master-z8x9k", methods=["POST"])
def super_admin_login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    # Super admin kredentsiallari (amaliyotda buni muhim joyga saqlash kerak)
    SUPER_ADMIN_USERNAME = "superadmin"
    SUPER_ADMIN_PASSWORD = "Admin123!@#"
    
    if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
        session["super_admin"] = True
        return redirect(url_for("super_admin_dashboard"))
    else:
        flash("Noto'g'ri login yoki parol!", "error")
        return redirect(url_for("super_admin_login"))

@app.route("/super-admin-dashboard-ultimate-m4st3r")
def super_admin_dashboard():
    if not session.get("super_admin"):
        return redirect(url_for("super_admin_login"))
    
    # Barcha xodimlarni olish
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM staff ORDER BY created_at DESC")
    staff_db = cur.fetchall()
    conn.close()
    
    # JSON fayldan ham xodimlarni olish
    employees_file = 'employees.json'
    employees_json = []
    if os.path.exists(employees_file):
        try:
            with open(employees_file, 'r', encoding='utf-8') as f:
                employees_json = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            employees_json = []
    
    # Barcha foydalanuvchilarni olish
    users_file = 'users.json'
    users_json = []
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users_json = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            users_json = []
    
    # Buyurtmalar statistikasi
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting'")
    waiting_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='ready'")
    ready_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='served'")
    served_orders = cur.fetchone()[0]
    conn.close()
    
    stats = {
        'total_orders': total_orders,
        'waiting_orders': waiting_orders,
        'ready_orders': ready_orders,
        'served_orders': served_orders,
        'total_staff': len(staff_db),
        'total_users': len(users_json)
    }
    
    return render_template("super_admin_dashboard.html", 
                         staff_db=staff_db, 
                         employees_json=employees_json,
                         users_json=users_json,
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
    password = request.form.get("password", "")

    if not all([first_name, last_name, birth_date, phone, password]):
        flash("Barcha maydonlarni to'ldiring.", "error")
        return redirect(url_for("super_admin_dashboard"))

    conn = get_db()
    cur = conn.cursor()
    password_hash = generate_password_hash(password)
    now = get_current_time()
    cur.execute("""
        INSERT INTO staff (first_name, last_name, birth_date, phone, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (first_name, last_name, birth_date, phone, password_hash, now.isoformat()))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    
    # JSON fayliga ham saqlash
    save_staff_to_json(first_name, last_name, birth_date, phone, new_id, now)
    
    flash(f"Yangi xodim qo'shildi. ID: {new_id}", "success")
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



with app.app_context():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
