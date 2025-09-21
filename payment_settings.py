# Payment Settings Management for Pro-Obuv
# This module handles payment method configurations for super admin

import sqlite3
from datetime import datetime

class PaymentSettings:
    def __init__(self, db_path='restaurant.db'):
        self.db_path = db_path
        self.init_payment_tables()
    
    def init_payment_tables(self):
        """Initialize payment settings table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create payment_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_type TEXT NOT NULL,  -- 'card', 'click', 'payme', 'cash'
                is_active BOOLEAN DEFAULT 1,
                settings_data TEXT,  -- JSON data for each payment type
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create payment_cards table for card details
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_type TEXT NOT NULL,  -- 'uzcard', 'humo', 'visa', 'mastercard'
                card_number TEXT NOT NULL,
                card_holder_name TEXT NOT NULL,
                bank_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create payment_qr_codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_qr_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qr_type TEXT NOT NULL,  -- 'click', 'payme', 'general'
                qr_code_data TEXT NOT NULL,  -- Base64 encoded QR code or URL
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_card(self, card_type, card_number, card_holder_name, bank_name=None):
        """Add a new payment card"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payment_cards (card_type, card_number, card_holder_name, bank_name)
            VALUES (?, ?, ?, ?)
        ''', (card_type, card_number, card_holder_name, bank_name))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_active_cards(self):
        """Get all active payment cards"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM payment_cards WHERE is_active = 1
            ORDER BY created_at DESC
        ''')
        
        cards = cursor.fetchall()
        conn.close()
        return cards
    
    def add_qr_code(self, qr_type, qr_code_data, description=None):
        """Add a QR code for payments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payment_qr_codes (qr_type, qr_code_data, description)
            VALUES (?, ?, ?)
        ''', (qr_type, qr_code_data, description))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_active_qr_codes(self):
        """Get all active QR codes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM payment_qr_codes WHERE is_active = 1
            ORDER BY created_at DESC
        ''')
        
        qr_codes = cursor.fetchall()
        conn.close()
        return qr_codes
    
    def update_payment_method_status(self, payment_type, is_active):
        """Enable/disable a payment method"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO payment_settings (payment_type, is_active, updated_at)
            VALUES (?, ?, ?)
        ''', (payment_type, is_active, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_payment_methods_status(self):
        """Get status of all payment methods"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT payment_type, is_active FROM payment_settings
        ''')
        
        methods = dict(cursor.fetchall())
        conn.close()
        
        # Default values for methods not set yet
        defaults = {'cash': True, 'card': True, 'click': True, 'payme': True}
        for method, default in defaults.items():
            if method not in methods:
                methods[method] = default
        
        return methods

if __name__ == "__main__":
    # Initialize payment settings
    payment_settings = PaymentSettings()
    print("Payment settings initialized successfully!")