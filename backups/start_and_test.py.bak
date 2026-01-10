#!/usr/bin/env python3
"""
Start Flask app and test payment methods API
"""

import subprocess
import time
import requests
import json
import threading
import sys

def start_flask_app():
    """Start Flask app in background."""
    try:
        print("🚀 Starting Flask app...")
        # Start app.py with no buffer and environment set
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
        )
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            print(f"[FLASK] {line.rstrip()}")
            if "Running on" in line or "Dastur quyidagi URLda" in line:
                print("✅ Flask app appears to be starting...")
                break
        
        return process
    except Exception as e:
        print(f"❌ Error starting Flask app: {e}")
        return None

def test_payment_api():
    """Test payment methods API."""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            print(f"🔍 Testing payment API (attempt {attempt + 1}/{max_retries})...")
            response = requests.get('http://127.0.0.1:5000/api/payment-methods', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API Response received!")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Analyze payment methods
                if 'payment_methods' in data:
                    methods = data['payment_methods']
                    print("\n📋 Payment Methods Analysis:")
                    for method_name, method_data in methods.items():
                        available = method_data.get('available', False)
                        name = method_data.get('name', method_name)
                        status = "✅ Available" if available else "❌ Not Available"
                        print(f"  {method_name.upper()}: {status} - {name}")
                        
                        if method_name == 'card' and available:
                            cards = method_data.get('cards', [])
                            print(f"    └── Cards: {len(cards)}")
                        
                        if method_name in ['click', 'payme'] and available:
                            qr_url = method_data.get('qr_url')
                            print(f"    └── QR: {qr_url}")
                
                return True
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"⏳ Connection failed, retrying in 2 seconds...")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Request error: {e}")
            time.sleep(2)
    
    print("❌ Failed to connect to Flask app after all retries")
    return False

def main():
    print("🎯 Pro-Obuv Payment Methods Test")
    print("=" * 50)
    
    # Start Flask app in background thread
    flask_process = start_flask_app()
    if not flask_process:
        return
    
    try:
        # Wait a bit for app to fully start
        time.sleep(3)
        
        # Test the API
        success = test_payment_api()
        
        if success:
            print("\n🎉 Payment API test completed successfully!")
            print("✅ All payment methods should be working now.")
        else:
            print("\n💥 Payment API test failed!")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    
    finally:
        # Clean up
        if flask_process:
            print("\n🔄 Stopping Flask app...")
            flask_process.terminate()
            try:
                flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                flask_process.kill()

if __name__ == "__main__":
    main()