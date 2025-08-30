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
    conn.commit()
    conn.close()

# Flask 2.2+ da before_first_request deprecated
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

def save_user_to_json(name, ticket_no, order_time):
    """Foydalanuvchi ma'lumotlarini users.json fayliga saqlash"""
    users_file = 'users.json'
    
    # Yangi foydalanuvchi ma'lumotlari
    user_data = {
        'ism': name,
        'buyurtma_raqami': ticket_no,
        'buyurtma_vaqti': order_time.strftime("%Y-%m-%d %H:%M:%S")
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

# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html")

# ---- USER ----
@app.route("/user", methods=["GET", "POST"])
def user_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Ismni kiriting.", "error")
            return redirect(url_for("user_page"))
        conn = get_db()
        try:
            tno = next_ticket_no(conn)
            eta_minutes = calc_eta_minutes(conn)
            now = get_current_time()
            eta_time = now + datetime.timedelta(minutes=eta_minutes)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO orders (customer_name, ticket_no, status, created_at, eta_time)
                VALUES (?, ?, 'waiting', ?, ?);
            """, (name, tno, now.isoformat(), eta_time.isoformat()))
            conn.commit()
            
            # Foydalanuvchini JSON fayliga saqlash
            save_user_to_json(name, tno, now)
            
        finally:
            conn.close()
        return redirect(url_for("user_success", ticket_no=tno))
    return render_template("user.html")

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
@app.route("/staff/login", methods=["GET", "POST"])
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

@app.route("/staff/logout")
def staff_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/staff/register", methods=["GET", "POST"])
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
        now = get_current_time().isoformat()
        cur.execute("""
            INSERT INTO staff (first_name, last_name, birth_date, phone, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (first_name, last_name, birth_date, phone, password_hash, now))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
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

@app.route("/staff")
@login_required
def staff_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at ASC;")
    orders = cur.fetchall()
    conn.close()
    return render_template("staff_dashboard.html", orders=orders, staff_name=session.get("staff_name"))

@app.route("/staff/order/<int:order_id>/given", methods=["POST"])
@login_required
def staff_mark_given(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='given' WHERE id=?;", (order_id,))
    conn.commit()
    conn.close()
    flash("Buyurtma foydalanuvchiga berildi sifatida belgilandi.", "success")
    return redirect(url_for("staff_dashboard"))

@app.route("/staff/orders.json")
@login_required
def staff_orders_json():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at ASC;")
    rows = cur.fetchall()
    conn.close()
    data = [dict(row) for row in rows]
    return jsonify(data)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
