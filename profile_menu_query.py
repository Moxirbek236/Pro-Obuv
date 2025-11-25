#!/usr/bin/env python3
"""
Profile the menu query to identify bottlenecks.
"""
import sqlite3
import time
import sys

DB_PATH = "database.sqlite3"

def profile_menu_query():
    """Profile the exact menu query being used."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 80)
    print("MENU QUERY PROFILING")
    print("=" * 80)
    
    # Check indexes
    print("\n1. CHECKING INDEXES ON menu_items AND ratings:\n")
    cur.execute("PRAGMA index_list(menu_items);")
    mi_indexes = cur.fetchall()
    print(f"Indexes on menu_items ({len(mi_indexes)}):")
    for idx in mi_indexes:
        print(f"  - {idx['name']}: unique={idx['unique']}")
        cur.execute(f"PRAGMA index_info({idx['name']});")
        cols = cur.fetchall()
        for col in cols:
            print(f"    Column: {col['name']} (seqno={col['seqno']})")
    
    cur.execute("PRAGMA index_list(ratings);")
    r_indexes = cur.fetchall()
    print(f"\nIndexes on ratings ({len(r_indexes)}):")
    for idx in r_indexes:
        print(f"  - {idx['name']}: unique={idx['unique']}")
        cur.execute(f"PRAGMA index_info({idx['name']});")
        cols = cur.fetchall()
        for col in cols:
            print(f"    Column: {col['name']} (seqno={col['seqno']})")
    
    # Check table sizes
    print("\n2. TABLE SIZES:\n")
    cur.execute("SELECT COUNT(*) as cnt FROM menu_items;")
    mi_count = cur.fetchone()['cnt']
    print(f"menu_items rows: {mi_count}")
    
    cur.execute("SELECT COUNT(*) as cnt FROM ratings;")
    r_count = cur.fetchone()['cnt']
    print(f"ratings rows: {r_count}")
    
    # Profile query
    print("\n3. QUERY PLAN (EXPLAIN QUERY PLAN):\n")
    query = """SELECT m.*, COALESCE(AVG(r.rating), 0) as avg_rating, COUNT(r.rating) as rating_count
               FROM menu_items m
               LEFT JOIN ratings r ON m.id = r.menu_item_id
               WHERE m.available = 1
               GROUP BY m.id
               ORDER BY m.category, m.orders_count DESC, m.name"""
    
    cur.execute(f"EXPLAIN QUERY PLAN\n{query}")
    plan = cur.fetchall()
    for line in plan:
        print(f"  {line[3]}")
    
    # Time the query
    print("\n4. EXECUTION TIME:\n")
    
    start = time.time()
    cur.execute(query)
    rows = cur.fetchall()
    elapsed = time.time() - start
    
    print(f"Query returned {len(rows)} rows in {elapsed:.3f}s")
    
    if rows:
        print(f"First row columns: {list(dict(rows[0]).keys())}")
        print(f"Sample first row: {dict(rows[0])}")
    
    # Check if index (menu_item_id, rating) would help
    print("\n5. MISSING INDEX ANALYSIS:\n")
    print("Current index on ratings: idx_ratings_menu_item(menu_item_id)")
    print("Recommended: CREATE INDEX idx_ratings_item_rating ON ratings(menu_item_id, rating)")
    print("This would optimize the LEFT JOIN + GROUP BY for AVG(rating) computation.")
    
    conn.close()

if __name__ == "__main__":
    profile_menu_query()
