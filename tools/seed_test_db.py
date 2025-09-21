"""
Seed the application's SQLite DB with minimal rows so automated audits and tests
that set session user_id/staff_id/courier_id = 1 won't hit foreign key errors.
Run with: python tools/seed_test_db.py
"""
import os
import sqlite3
import datetime

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.sqlite3')

def now():
    return datetime.datetime.utcnow().isoformat()

def ensure(conn, query, params=()):
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()

with sqlite3.connect(DB) as conn:
    cur = conn.cursor()
    # Enable foreign keys
    cur.execute('PRAGMA foreign_keys = ON;')

    # Ensure users table has id=1
    cur.execute("SELECT id FROM users WHERE id=1")
    if not cur.fetchone():
        print('Inserting test user id=1')
        cur.execute(
            "INSERT INTO users (id, first_name, last_name, email, password_hash, created_at) VALUES (1, ?, ?, ?, ?, ?)",
            ('Test', 'User', 'test.user@example.com', '', now()),
        )

    # Ensure menu_items has id=1
    cur.execute("SELECT id FROM menu_items WHERE id=1")
    if not cur.fetchone():
        print('Inserting test menu_item id=1')
        cur.execute(
            "INSERT INTO menu_items (id, name, price, category, created_at) VALUES (1, ?, ?, ?, ?)",
            ('Test Item', 1000, 'test', now()),
        )

    # Ensure staff id=1
    cur.execute("SELECT id FROM staff WHERE id=1")
    if not cur.fetchone():
        print('Inserting test staff id=1')
        cur.execute(
            "INSERT INTO staff (id, first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('Staff', 'One', '1990-01-01', '0000000000', 'AA', '111111', '', now()),
        )

    # Ensure courier id=1
    cur.execute("SELECT id FROM couriers WHERE id=1")
    if not cur.fetchone():
        print('Inserting test courier id=1')
        cur.execute(
            "INSERT INTO couriers (id, first_name, last_name, birth_date, phone, passport_series, passport_number, password_hash, created_at) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)",
            ('Courier', 'One', '1990-01-01', '0000000000', 'BB', '222222', '', now()),
        )

    conn.commit()
    print('Seeding complete')
