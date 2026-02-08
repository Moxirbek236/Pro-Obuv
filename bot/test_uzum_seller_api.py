import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(r'd:\Safety.uz\backend\.env')

def test_uzum_seller_api():
    token = os.getenv('UZUM_API_TOKEN')
    if not token:
        print("UZUM_API_TOKEN topilmadi!")
        return

    # Endpoint from refresh_uzum.js
    shop_id = "88415"
    url = f"https://api-seller.uzum.uz/api/seller-openapi/v1/product/shop/{shop_id}"
    
    headers = {
        "Authorization": token,
        "Accept": "*/*",
        "Content-Type": "application/json"
    }

    all_products = []
    page = 0
    size = 100 # Katta size so'rovlar sonini kamaytirish uchun
    total_expected = 0

    print(f"Uzum Seller API dan barcha mahsulotlarni yuklash boshlandi: {url}")
    
    while True:
        params = {
            "sortBy": "DEFAULT",
            "order": "ASC",
            "size": size,
            "page": page,
            "filter": "ALL"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Xatolik (Sahifa {page}): {response.status_code}, {response.text}")
                break
                
            data = response.json()
            products = data.get('productList', [])
            total_expected = data.get('totalProductsAmount', 0)
            
            if not products:
                break
                
            all_products.extend(products)
            print(f"Sahifa {page} yuklandi. Jami: {len(all_products)}/{total_expected}")
            
            # Agar barcha mahsulotlar olingan bo'lsa yoki jami miqdordan oshsa, to'xtatamiz
            if len(all_products) >= total_expected:
                break
                
            page += 1
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            break

    if all_products:
        print(f"\n✅ Muvaffaqiyatli! Jami {len(all_products)} ta mahsulot yuklandi.")
        
        # Ma'lumotlarni saqlash
        output_data = {
            "productList": all_products,
            "totalProductsAmount": total_expected
        }
        
        with open('uzum_seller_api_response.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print("Barcha ma'lumotlar 'uzum_seller_api_response.json' fayliga saqlandi.")
        
        # Test uchun bir nechtasini chiqarish
        for i, product in enumerate(all_products[:5]):
            print(f"{i+1}. {product.get('title')}")
        if len(all_products) > 5:
            print(f"... va yana {len(all_products)-5} ta mahsulot.")

if __name__ == "__main__":
    test_uzum_seller_api()
