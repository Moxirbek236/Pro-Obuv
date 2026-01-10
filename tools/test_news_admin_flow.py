#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test news admin flow to verify multilingual support works end-to-end
"""
import json
import os
import sys
import sqlite3
from datetime import datetime

def print_section(title):
    print(f"\n{'='*70}")
    print(f"✓ {title}")
    print(f"{'='*70}")

def print_step(step):
    print(f"  → {step}")

# Step 1: Check database structure
print_section("1. DATABASE STRUCTURE CHECK")

db_path = "database.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(news)")
    columns = cursor.fetchall()
    
    print_step(f"News table has {len(columns)} columns:")
    
    expected_cols = {
        'title': False, 'content': False,
        'title_uz': False, 'title_ru': False, 'title_en': False, 'title_kz': False,
        'content_uz': False, 'content_ru': False, 'content_en': False, 'content_kz': False,
    }
    
    for col in columns:
        col_name = col[1]
        if col_name in expected_cols:
            expected_cols[col_name] = True
        print(f"    • {col_name} ({col[2]})")
    
    # Check if i18n columns exist
    i18n_cols = [col for col, exists in expected_cols.items() if exists]
    print(f"\n  ✓ Found {len(i18n_cols)} language columns")
    
    if all(expected_cols.values()):
        print(f"  ✓ ALL required columns present (including i18n)")
    else:
        print(f"  ⚠ Missing columns: {[k for k,v in expected_cols.items() if not v]}")
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# Step 2: Check existing news data
print_section("2. EXISTING NEWS DATA IN DATABASE")

try:
    cursor.execute("SELECT COUNT(*) as cnt FROM news")
    count = cursor.fetchone()['cnt']
    print_step(f"Found {count} news items in database")
    
    if count > 0:
        cursor.execute("""
            SELECT id, title, title_uz, title_ru, title_en, title_kz, type, is_active 
            FROM news 
            ORDER BY display_order ASC, created_at DESC 
            LIMIT 3
        """)
        items = cursor.fetchall()
        
        for i, item in enumerate(items, 1):
            print(f"\n  Item {i}: ID={item['id']}")
            print(f"    Title (default): {item['title']}")
            print(f"    Title_uz: {item['title_uz'] or '(empty)'}")
            print(f"    Title_ru: {item['title_ru'] or '(empty)'}")
            print(f"    Title_en: {item['title_en'] or '(empty)'}")
            print(f"    Title_kz: {item['title_kz'] or '(empty)'}")
            print(f"    Type: {item['type']}, Active: {bool(item['is_active'])}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Step 3: Check JSON file
print_section("3. NEWS JSON FILE CHECK")

json_path = "data/news.json"
if os.path.exists(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print_step(f"✓ JSON file exists at {json_path}")
        
        # Check structure
        if 'metadata' in json_data:
            meta = json_data['metadata']
            print(f"  • Total items: {meta.get('total_count', '?')}")
            print(f"  • Active items: {meta.get('active_count', '?')}")
            print(f"  • Version: {meta.get('version', '?')}")
            print(f"  • Last updated: {meta.get('last_updated', '?')}")
        
        if 'news' in json_data:
            print(f"  • News array items: {len(json_data['news'])}")
            
            # Check if i18n fields exist in JSON
            if len(json_data['news']) > 0:
                first_item = json_data['news'][0]
                has_i18n = any(key in first_item for key in ['title_uz', 'title_ru', 'title_en', 'title_kz'])
                print(f"  • Has i18n fields: {'✓ YES' if has_i18n else '✗ NO'}")
                
                if has_i18n:
                    print(f"\n  Sample item fields:")
                    for key in ['id', 'title', 'title_uz', 'title_ru', 'title_en', 'title_kz', 'type']:
                        value = first_item.get(key)
                        if key.startswith('title'):
                            print(f"    • {key}: {value[:30] if value else '(empty)'}...")
                        else:
                            print(f"    • {key}: {value}")
                
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error: {e}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
else:
    print_step(f"⚠ JSON file NOT found at {json_path}")

# Step 4: Test API endpoint structure
print_section("4. API ENDPOINT STRUCTURE CHECK")

print_step("Checking /api/news POST endpoint expectations:")
print("  • Expected to accept JSON with:")
print("    - title (default), content (default)")
print("    - title_uz, title_ru, title_en, title_kz")
print("    - content_uz, content_ru, content_en, content_kz")
print("    - type, image_url, video_url, is_active, display_order")
print("\n  • Expected to sync to data/news.json with i18n fields")
print("  • Expected to return: {'success': True, ...}")

print_step("\nChecking /api/news/<id> PUT endpoint expectations:")
print("  • Expected to accept JSON with multilingual fields")
print("  • Expected to preserve all i18n fields in JSON sync")

print_step("\nChecking /api/news/<id> DELETE endpoint expectations:")
print("  • Expected to delete from DB and sync JSON")
print("  • Expected to preserve other items' i18n fields")

# Step 5: Admin form check
print_section("5. ADMIN FORM STRUCTURE CHECK")

html_path = "templates/admin/news_management.html"
if os.path.exists(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for multilingual input fields
    i18n_fields = ['newsTitle_uz', 'newsTitle_ru', 'newsTitle_en', 'newsTitle_kz',
                   'newsContent_uz', 'newsContent_ru', 'newsContent_en', 'newsContent_kz']
    
    found_fields = []
    for field in i18n_fields:
        if field in html_content:
            found_fields.append(field)
    
    print_step(f"Found {len(found_fields)} out of {len(i18n_fields)} expected multilingual fields")
    if found_fields:
        print(f"  • Found: {', '.join(found_fields[:4])}...")
    
    # Check for language tabs
    if 'class="nav-link"' in html_content and 'data-bs-target' in html_content:
        print_step("✓ Language tabs UI structure found")
    
    # Check for saveNews function
    if 'function saveNews()' in html_content:
        print_step("✓ saveNews() function found")
        
        # Check if it collects i18n fields
        if 'title_uz' in html_content and 'content_uz' in html_content:
            print(f"  • Function appears to collect i18n fields")
        
    # Check for openNewsModal function
    if 'function openNewsModal(' in html_content:
        print_step("✓ openNewsModal() function found")
        if 'title_uz' in html_content:
            print(f"  • Function appears to populate i18n fields")

# Step 6: Ready to test
print_section("6. READINESS CHECK")

checks = {
    "Database has i18n columns": all(expected_cols.values()) if 'expected_cols' in dir() else False,
    "JSON file exists": os.path.exists(json_path),
    "Admin form has i18n fields": len(found_fields) >= 4 if 'found_fields' in dir() else False,
    "Database has news data": count > 0 if 'count' in dir() else False,
}

all_ready = all(checks.values())

for check, status in checks.items():
    symbol = "✓" if status else "✗"
    print(f"  {symbol} {check}")

print()
if all_ready:
    print("✓✓✓ SYSTEM READY FOR TESTING ✓✓✓")
    print("\nNext steps:")
    print("  1. Start Flask server: python app.py")
    print("  2. Navigate to /admin/news_management")
    print("  3. Click 'Yangilik qo'sh'")
    print("  4. Fill in titles for ALL 4 languages (uz, ru, en, kz)")
    print("  5. Click 'Saqlash' and verify:")
    print("     - News appears in table")
    print("     - Check data/news.json has all language fields")
    print("     - Check database has all language fields")
else:
    print("✗ Some checks failed - review above")

conn.close()
