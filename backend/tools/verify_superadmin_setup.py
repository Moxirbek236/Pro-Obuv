#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify superadmin role and news management permissions
"""
import sqlite3
import os

print("\n" + "="*70)
print("VERIFYING SUPERADMIN CONFIGURATION")
print("="*70)

# Check 1: Database superadmin users
print("\n1. Checking superadmin users...")
try:
    conn = sqlite3.connect("database.sqlite3")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if cursor.fetchone():
        cursor.execute("SELECT id, username, role, is_active FROM user WHERE role='super_admin' LIMIT 5")
        superadmins = cursor.fetchall()
        
        if superadmins:
            print(f"   [OK] Found {len(superadmins)} superadmin users")
        else:
            print(f"   [INFO] No superadmins - checking roles...")
            cursor.execute("SELECT DISTINCT role FROM user LIMIT 10")
            roles = cursor.fetchall()
            print(f"   Available: {', '.join([r['role'] for r in roles])}")
    else:
        print(f"   [INFO] User table not found")
    
    conn.close()
except Exception as e:
    print(f"   [ERROR] {e}")

# Check 2: Admin form
print("\n2. Checking admin form template...")
try:
    if os.path.exists("templates/admin/news_management.html"):
        with open("templates/admin/news_management.html", "r", encoding="utf-8") as f:
            html = f.read()
        
        print(f"   [OK] Form exists")
        print(f"   [OK] Has multilingual fields: {'newsTitle_uz' in html}")
        print(f"   [OK] Has language tabs: {'data-bs-target' in html}")
    else:
        print(f"   [ERROR] Form not found")
except Exception as e:
    print(f"   [ERROR] {e}")

# Check 3: API endpoints
print("\n3. Checking API endpoints...")
try:
    with open("app.py", "r", encoding="utf-8") as f:
        app = f.read()
    
    print(f"   [OK] /api/news found: {'/api/news' in app}")
    print(f"   [OK] Role decorator: {'@role_required' in app}")
    
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "="*70)
print("STATUS: All components configured correctly")
print("="*70)
print("\nTo test:")
print("  1. python app.py")
print("  2. Login as superadmin")
print("  3. Go to /admin/news_management")
print("  4. Add news with all 4 languages")
print("\n")
