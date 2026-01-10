#!/usr/bin/env python3
"""
Final test script for all Pro-Obuv fixes:
1. Payment methods (should show all: Cash, Card, Click, Payme)
2. 360° photos (should be visible on /360-room)
3. Menu grid (3 columns layout)
"""

import subprocess
import time
import requests
import json
import sys
import sqlite3

def test_database():
    """Test database setup."""
    print(" Testing database...")
    
    try:
        conn = sqlite3.connect('database.sqlite3')
        cur = conn.cursor()
        
        # Test payment cards
        cur.execute("SELECT COUNT(*) FROM payment_cards WHERE is_active = 1")
        active_cards = cur.fetchone()[0]
        print(f" Active payment cards: {active_cards}")
        
        # Test card payment settings  
        cur.execute("SELECT COUNT(*) FROM card_payment_settings")
        payment_settings = cur.fetchone()[0]
        print(f" Card payment settings: {payment_settings}")
        
        # Test 360 photos
        cur.execute("SELECT COUNT(*) FROM photos_360")
        total_360 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM photos_360 WHERE is_active = 1")
        active_360 = cur.fetchone()[0]
        print(f" 360° Photos: {active_360}/{total_360} active")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f" Database test error: {e}")
        return False

def start_flask():
    """Start Flask app."""
    print(" Starting Flask app...")
    try:
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        universal_newlines=True
        )
        
        # Wait for startup message
        for line in iter(process.stdout.readline, ''):
            print(f"[FLASK] {line.rstrip()}")
            if "Running on" in line or "Dastur quyidagi URLda" in line:
                print(" Flask app started!")
                time.sleep(2)  # Give it a moment
                return process
                
        return None
        
    except Exception as e:
        print(f" Flask start error: {e}")
        return None

def test_payment_methods():
    """Test payment methods API."""
    print("\n Testing Payment Methods API...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/payment-methods', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and 'payment_methods' in data:
                methods = data['payment_methods']
                
                print(" Available Payment Methods:")
                for method_name, method_data in methods.items():
                    available = method_data.get('available', False)
                    name = method_data.get('name', method_name)
                    status = " Available" if available else " Not Available"
                    print(f"  {method_name.upper()}: {status} - {name}")
                    
                    if method_name == 'card' and available:
                        cards = method_data.get('cards', [])
                        print(f"    └── Cards: {len(cards)}")
                    
                    if method_name in ['click', 'payme'] and available:
                        qr_url = method_data.get('qr_url')
                        print(f"    └── QR: {'Yes' if qr_url else 'No'}")
                
                available_count = sum(1 for m in methods.values() if m.get('available'))
                print(f"\n Total available payment methods: {available_count}/4")
                return available_count >= 4
            else:
                print(" Invalid API response format")
                return False
        else:
            print(f" API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f" Payment methods test error: {e}")
        return False

def test_360_room():
    """Test 360 room page."""
    print("\n Testing 360° Room page...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/360-room', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check if page loads and contains expected content
            checks = [
                ("360° Room title", "360° Room" in content),
                ("Photos container", "room-gallery" in content),
                ("Photo viewer", "photo360-modal" in content),
                ("JavaScript", "photos360 =" in content)
            ]
            
            all_passed = True
            for check_name, check_result in checks:
                status = "" if check_result else ""
                print(f"  {check_name}: {status}")
                if not check_result:
                    all_passed = False
            
            return all_passed
        else:
            print(f" 360° Room page error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f" 360° Room test error: {e}")
        return False

def test_menu_page():
    """Test menu page layout."""
    print("\n Testing Menu page layout...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/menu', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for 3-column grid
            checks = [
                ("Menu grid", "menu-grid" in content),
                ("3-column layout", "grid-template-columns: repeat(3, 1fr)" in content),
                ("Responsive design", "@media" in content),
                ("Product cards", "menu-item" in content)
            ]
            
            all_passed = True
            for check_name, check_result in checks:
                status = "" if check_result else ""
                print(f"  {check_name}: {status}")
                if not check_result:
                    all_passed = False
            
            return all_passed
        else:
            print(f" Menu page error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f" Menu page test error: {e}")
        return False

def main():
    print(" Pro-Obuv Final Testing")
    print("=" * 50)
    
    # Test 1: Database
    db_ok = test_database()
    
    if not db_ok:
        print("\n Database test failed - aborting")
        return
    
    # Test 2: Start Flask
    flask_process = start_flask()
    
    if not flask_process:
        print("\n Flask startup failed - aborting")
        return
    
    try:
        # Test 3: Payment Methods
        payment_ok = test_payment_methods()
        
        # Test 4: 360° Room
        room_ok = test_360_room()
        
        # Test 5: Menu Layout
        menu_ok = test_menu_page()
        
        # Final Results
        print("\n FINAL TEST RESULTS:")
        print("=" * 50)
        print(f" Payment Methods: {' PASSED' if payment_ok else ' FAILED'}")
        print(f" 360° Room:       {' PASSED' if room_ok else ' FAILED'}")
        print(f" Menu Layout:     {' PASSED' if menu_ok else ' FAILED'}")
        
        all_passed = payment_ok and room_ok and menu_ok
        
        if all_passed:
            print("\n ALL TESTS PASSED!")
            print(" Savatchada barcha to'lov usullari ko'rinadi")
            print(" 360° rasmlar foydalanuvchilarga ko'rinadi")  
            print(" Menu 3 ustunli grid layout-da")
            print("\n Pro-Obuv ready to go!")
        else:
            print("\n Some tests failed - check logs above")
        
    except KeyboardInterrupt:
        print("\n Tests interrupted")
        
    finally:
        if flask_process:
            print("\n Stopping Flask app...")
            flask_process.terminate()
            try:
                flask_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                flask_process.kill()

if __name__ == "__main__":
    main()