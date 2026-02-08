import requests
import json

def test_uzum_search(query):
    url = "https://uzum.uz/api/v1/search"
    params = {
        "query": query,
        "size": 5
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "uz-UZ,uz;q=0.9,en;q=0.8",
        "Referer": "https://uzum.uz/",
        "X-Requested-With": "XMLHttpRequest"
    }

    print(f"Sending request to Uzum Market API for query: '{query}'...")
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                # The structure from JS was response.payload.items
                items = data.get('payload', {}).get('items', [])
                print(f"Found {len(items)} items.")
                
                for i, item in enumerate(items):
                    title = item.get('title', 'No Title')
                    price = item.get('lowPrice', 'N/A')
                    print(f"{i+1}. {title} - {price} so'm")
                
                # Save the full response for inspection
                with open('uzum_api_test_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print("\nFull response saved to 'uzum_api_test_response.json'")
            except Exception as json_err:
                print(f"Failed to parse JSON: {json_err}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
        else:
            print(f"Error response status {response.status_code}: {response.text[:500]}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_uzum_search("krossovka")
