#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the news admin API - simulate posting new multilingual news via /api/news endpoint
This tests the full flow: form → API → DB → JSON sync
"""
import requests
import json
import os
import sqlite3
from datetime import datetime

# Test data - multilingual news item
test_news = {
    "title": "TEST: Yangi xizmat",  # default
    "title_uz": "TEST: Yangi xizmat",  # Uzbek
    "title_ru": "TEST: Новая услуга",  # Russian
    "title_en": "TEST: New Service",  # English
    "title_kz": "TEST: Жаңа қызмет",  # Kazakh
    
    "content": "Bu yangi xizmat haqida test.",  # default content
    "content_uz": "Bu yangi xizmat haqida test. (Uzbek)",
    "content_ru": "Это тестовая услуга. (Russian)",
    "content_en": "This is a test service. (English)",
    "content_kz": "Бұл сынақтық қызмет. (Kazakh)",
    
    "type": "news",
    "image_url": "https://via.placeholder.com/300",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "is_active": True,
    "display_order": 10
}

print("\n" + "="*70)
print("✓ TESTING NEWS ADMIN API - MULTILINGUAL SUPPORT")
print("="*70)

# Test 1: Check if we can connect to the API
print("\n1. Testing API connectivity...")
base_url = "http://localhost:5000"
api_endpoint = f"{base_url}/api/news"

try:
    response = requests.get(api_endpoint, timeout=5)
    print(f"   ✓ API is responding (status: {response.status_code})")
except requests.exceptions.ConnectionError:
    print(f"   ✗ Cannot connect to API at {base_url}")
    print("\n   → Start server with: python app.py")
    print("   → Then run this test again")
    exit(1)

# Test 2: Get current news count
print("\n2. Getting current news count...")
response = requests.get(api_endpoint)
current_news = response.json() if response.status_code == 200 else {"data": []}
initial_count = len(current_news.get("data", []))
print(f"   ✓ Currently have {initial_count} news items")

# Test 3: Post new multilingual news
print("\n3. Posting new multilingual news item...")
print(f"   Sending to {api_endpoint}")
print(f"   Payload:")
for key in ['title_uz', 'title_ru', 'title_en', 'title_kz', 'type', 'is_active']:
    print(f"     • {key}: {test_news[key]}")

try:
    response = requests.post(
        api_endpoint,
        json=test_news,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"\n   Response status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code in [200, 201]:
        print(f"   ✓ SUCCESS - News item created!")
        result_data = response.json()
    else:
        print(f"   ✗ FAILED - Status {response.status_code}")
        exit(1)
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test 4: Verify in database
print("\n4. Verifying data in database...")
try:
    conn = sqlite3.connect("database.sqlite3")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get latest news
    cursor.execute("""
        SELECT id, title, title_uz, title_ru, title_en, title_kz,
               content_uz, content_ru, content_en, content_kz,
               type, is_active
        FROM news 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    latest = cursor.fetchone()
    
    if latest:
        print(f"   ✓ Found latest news in DB:")
        print(f"     • ID: {latest['id']}")
        print(f"     • title: {latest['title']}")
        print(f"     • title_uz: {latest['title_uz']}")
        print(f"     • title_ru: {latest['title_ru']}")
        print(f"     • title_en: {latest['title_en']}")
        print(f"     • title_kz: {latest['title_kz']}")
        print(f"     • content_uz: {(latest['content_uz'] or '')[:40]}...")
        print(f"     • type: {latest['type']}")
        print(f"     • is_active: {latest['is_active']}")
        
        # Check if i18n fields populated
        i18n_fields_ok = all([
            latest['title_uz'],
            latest['title_ru'],
            latest['title_en'],
            latest['title_kz'],
        ])
        
        if i18n_fields_ok:
            print(f"   ✓ All i18n fields populated in database")
        else:
            print(f"   ✗ Some i18n fields missing in database!")
    else:
        print(f"   ✗ No news found in database")
    
    conn.close()
    
except Exception as e:
    print(f"   ✗ Database error: {e}")

# Test 5: Verify in JSON file
print("\n5. Verifying data in JSON file...")
json_path = "data/news.json"

if os.path.exists(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        news_items = json_data.get('news', [])
        
        if news_items:
            latest_json = news_items[-1] if len(news_items) > 0 else None
            
            if latest_json:
                print(f"   ✓ Found latest news in JSON:")
                print(f"     • ID: {latest_json.get('id')}")
                print(f"     • title: {latest_json.get('title')}")
                print(f"     • title_uz: {latest_json.get('title_uz')}")
                print(f"     • title_ru: {latest_json.get('title_ru')}")
                print(f"     • title_en: {latest_json.get('title_en')}")
                print(f"     • title_kz: {latest_json.get('title_kz')}")
                
                # Check if i18n fields exist in JSON
                i18n_in_json = all([
                    latest_json.get('title_uz'),
                    latest_json.get('title_ru'),
                    latest_json.get('title_en'),
                    latest_json.get('title_kz'),
                ])
                
                if i18n_in_json:
                    print(f"   ✓ All i18n fields synced to JSON file")
                else:
                    print(f"   ✗ Some i18n fields missing in JSON!")
        
        print(f"\n   Metadata:")
        meta = json_data.get('metadata', {})
        print(f"     • Total items: {meta.get('total_count')}")
        print(f"     • Active items: {meta.get('active_count')}")
        print(f"     • Version: {meta.get('version')}")
        print(f"     • Last updated: {meta.get('last_updated')}")
        
    except json.JSONDecodeError as e:
        print(f"   ✗ JSON parse error: {e}")
else:
    print(f"   ✗ JSON file not found at {json_path}")

# Summary
print("\n" + "="*70)
print("✓ TEST SUMMARY")
print("="*70)
print("""
If all checks above passed (✓):
1. Multilingual news creation is working
2. Database i18n fields are being populated
3. JSON sync is preserving i18n fields
4. Admin can now successfully add news with multiple languages

Next: Try adding news via admin panel at:
  http://localhost:5000/admin/news_management

""")
