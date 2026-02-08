import requests
import json
import os
from backend.app import Config

def fetch_and_save_uzum_data():
    token = Config.UZUM_API_TOKEN
    shop_id = Config.UZUM_SHOP_ID
    url = f"https://api-seller.uzum.uz/api/seller-openapi/v1/product/shop/{shop_id}"
    headers = {"Authorization": token, "Accept": "*/*", "Content-Type": "application/json"}
    
    print(f"Fetching from: {url}")
    print(f"Shop ID: {shop_id}")
    
    all_products = []
    page = 0
    size = 100
    
    try:
        while True:
            params = {"sortBy": "DEFAULT", "order": "ASC", "size": size, "page": page, "filter": "ALL"}
            print(f"Fetch page {page}...")
            r = requests.get(url, params=params, headers=headers, timeout=30)
            
            if r.status_code != 200:
                print(f"Error: {r.status_code} - {r.text}")
                break
                
            data = r.json()
            prods = data.get('productList', [])
            
            if not prods:
                break
                
            all_products.extend(prods)
            print(f"Got {len(prods)} products (Total: {len(all_products)})")
            
            if len(all_products) >= data.get('totalProductsAmount', 0):
                break
            page += 1
            
        # Save to JSON
        filename = "uzum_fresh_dump.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"productList": all_products}, f, ensure_ascii=False, indent=4)
            
        print(f"\n✅ Saved {len(all_products)} products to {filename}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    fetch_and_save_uzum_data()
