#!/usr/bin/env python3
"""
Debug payment methods standalone
"""

import sqlite3
import sys
import os
from contextlib import contextmanager

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')

@contextmanager 
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def debug_payment_methods():
    """Debug payment methods similar to the app logic."""
    print("🔍 Debugging payment methods...")
    
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            # Initialize payment methods structure
            payment_methods = {
                'cash': {'available': True, 'name': 'Naqd pul', 'icon': '💵'},
                'card': {'available': False, 'name': 'Bank kartasi', 'icon': '💳', 'cards': []},
                'click': {'available': False, 'name': 'Click', 'icon': '🟦', 'qr_url': None},
                'payme': {'available': False, 'name': 'Payme', 'icon': '🟨', 'qr_url': None}
            }
            
            print("✅ Basic payment methods structure initialized")
            
            # Check for active payment cards
            print("\n🔍 Checking payment cards...")
            cards_query = "SELECT id, card_name, card_number, card_holder_name, bank_name FROM payment_cards WHERE is_active = 1 ORDER BY display_order ASC"
            
            try:
                cur.execute(cards_query)
                cards = cur.fetchall()
                
                print(f"Found {len(cards)} active payment cards:")
                for card in cards:
                    print(f"  - ID: {card['id']}, Name: {card['card_name']}, Number: {card['card_number']}, Bank: {card['bank_name']}")
                
                if cards:
                    payment_methods['card']['available'] = True
                    payment_methods['card']['cards'] = [dict(card) for card in cards]
                    print("✅ Card payments enabled")
                else:
                    print("❌ No active cards found")
                    
            except Exception as e:
                print(f"❌ Error querying payment cards: {e}")
            
            # Check for QR codes
            print("\n🔍 Checking QR settings...")
            qr_query = "SELECT click_qr_url, payme_qr_url FROM card_payment_settings WHERE id = 1"
            
            try:
                cur.execute(qr_query)
                qr_settings = cur.fetchone()
                
                if qr_settings:
                    print(f"QR Settings found:")
                    print(f"  - Click QR: {qr_settings['click_qr_url']}")
                    print(f"  - Payme QR: {qr_settings['payme_qr_url']}")
                    
                    if qr_settings['click_qr_url']:
                        payment_methods['click']['available'] = True
                        payment_methods['click']['qr_url'] = qr_settings['click_qr_url']
                        print("✅ Click payments enabled")
                        
                    if qr_settings['payme_qr_url']:
                        payment_methods['payme']['available'] = True
                        payment_methods['payme']['qr_url'] = qr_settings['payme_qr_url']
                        print("✅ Payme payments enabled")
                else:
                    print("❌ No QR settings found")
                    
            except Exception as e:
                print(f"❌ Error querying QR settings: {e}")
            
            # Final summary
            print("\n📋 FINAL PAYMENT METHODS STATUS:")
            for method_name, method_data in payment_methods.items():
                available = method_data.get('available', False)
                name = method_data.get('name', method_name)
                status = "✅ Available" if available else "❌ Not Available"
                print(f"  {method_name.upper()}: {status} - {name}")
                
                if method_name == 'card' and available:
                    cards = method_data.get('cards', [])
                    print(f"    └── Cards count: {len(cards)}")
                    
                if method_name in ['click', 'payme'] and available:
                    qr_url = method_data.get('qr_url')
                    print(f"    └── QR URL: {qr_url}")
            
            return payment_methods
            
    except Exception as e:
        print(f"💥 Critical error: {e}")
        return None

if __name__ == "__main__":
    debug_payment_methods()