import requests
import json

def test_uzum_public_api(product_id, sku_id=None):
    url = f"https://uzum.uz/api/v1/products/{product_id}"
    params = {}
    if sku_id:
        params["skuId"] = sku_id
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "uz-UZ,uz;q=0.9,en;q=0.8,ru;q=0.7",
        "Referer": "https://uzum.uz/",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    print(f"Uzum Public API ga so'rov yuborilmoqda: {url}")
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                payload = data.get('payload', {})
                title = payload.get('title', 'No Title')
                print(f"Mahsulot nomi: {title}")
                
                # Save response
                with open('uzum_public_product_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print("To'liq javob 'uzum_public_product_response.json' fayliga saqlandi.")
            except Exception as json_err:
                print(f"JSON parsing error: {json_err}")
                print(f"Response (starts with): {response.text[:200]}")
        else:
            print(f"Xatolik: {response.status_code}")
            print(f"Response (starts with): {response.text[:200]}")
            
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

if __name__ == "__main__":
    # Test with a product ID from the previous seller API response if possible
    # In the previous response we got "Qishki va kuzgi botinkalar" 
    # Let's see the ID from the file if it was saved.
    try:
        with open('uzum_seller_api_response.json', 'r', encoding='utf-8') as f:
            seller_data = json.load(f)
            products = seller_data.get('productList', [])
            if products:
                prod_id = products[0].get('productId')
                print(f"Seller API dan olingan product ID: {prod_id}")
                test_uzum_public_api(prod_id)
            else:
                test_uzum_public_api(2326112) # Fallback from test_uzum_api.js
    except:
        test_uzum_public_api(2326112)
