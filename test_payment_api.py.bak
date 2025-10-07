#!/usr/bin/env python3
"""
Test payment methods API
"""

import requests
import json

def test_payment_methods():
    try:
        print("🔍 Testing payment methods API...")
        response = requests.get('http://127.0.0.1:5000/api/payment-methods', timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check each payment method
            if 'payment_methods' in data:
                methods = data['payment_methods']
                print("\n📋 Payment Methods Status:")
                for method_name, method_data in methods.items():
                    available = method_data.get('available', False)
                    name = method_data.get('name', method_name)
                    status = "✅ Available" if available else "❌ Not Available"
                    print(f"  {method_name.upper()}: {status} - {name}")
                    
                    if method_name == 'card' and available:
                        cards = method_data.get('cards', [])
                        print(f"    └── Cards count: {len(cards)}")
                        for card in cards:
                            print(f"        └── {card.get('card_name', 'Unknown')}: {card.get('card_number', '')}")
                    
                    if method_name in ['click', 'payme'] and available:
                        qr_url = method_data.get('qr_url')
                        print(f"    └── QR URL: {qr_url}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app is not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_payment_methods()