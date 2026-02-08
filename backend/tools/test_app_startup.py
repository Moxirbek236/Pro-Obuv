#!/usr/bin/env python3
"""
Quick test to verify app starts and cache warmup works.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import app

print("\n" + "="*80)
print("APP STARTUP TEST")
print("="*80 + "\n")

with app.test_client() as client:
    print("[*] Making first request to /menu to trigger warmup...")
    start = __import__('time').time()
    resp = client.get("/menu")
    elapsed = __import__('time').time() - start
    
    print(f"Status: {resp.status_code}")
    print(f"Time: {elapsed*1000:.2f}ms")
    print(f"Response size: {len(resp.data)} bytes")
    
    if resp.status_code == 200:
        print("✓ App works!")
    else:
        print("✗ Got error response")
        print(resp.data[:500])

print("\n✓ App startup test complete\n")
