#!/usr/bin/env python3
"""
Generate sitemap.xml for the Pro-Obuv project.

Heuristics:
- Looks for sqlite DB at repository root (database.sqlite3).
- Finds a table that looks like a product/menu items table (id + name/title +/- slug).
- Produces sitemap.xml with site root and common static pages and product pages.

Usage:
  python tools/generate_sitemap.py [base_url]

If base_url is not provided, https://example.com will be used and should be replaced
with your real domain before submitting sitemap to search engines.
"""

import sqlite3
import os
import sys
import xml.etree.ElementTree as ET
import datetime

BASES_ARG = sys.argv[1] if len(sys.argv) > 1 else 'https://example.com'
# Accept comma-separated list of base domains; first is primary
BASES = [b.strip().rstrip('/') for b in BASES_ARG.split(',') if b.strip()]
if not BASES:
    BASES = ['https://example.com']
PRIMARY = BASES[0]
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(REPO, 'database.sqlite3')
OUT = os.path.join(REPO, 'sitemap.xml')

print('Repo:', REPO)
print('DB path:', DB, 'exists=', os.path.exists(DB))
products = []

if os.path.exists(DB):
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print('Tables found:', tables)
        # candidate table names commonly used
        candidates = ['menu_items', 'products', 'items', 'menu_item', 'menu']
        found_table = None
        for c in candidates:
            if c in tables:
                found_table = c
                break
        if not found_table:
            # fallback: first table with id + name/title
            for t in tables:
                try:
                    cols = [r[1] for r in cur.execute(f"PRAGMA table_info({t})").fetchall()]
                except Exception:
                    continue
                if 'id' in cols and ('name' in cols or 'title' in cols):
                    found_table = t
                    break
        if found_table:
            print('Using table:', found_table)
            cols = [r[1] for r in cur.execute(f"PRAGMA table_info({found_table})").fetchall()]
            has_slug = 'slug' in cols
            try:
                if has_slug:
                    rows = cur.execute(f"SELECT id, name, slug FROM {found_table}").fetchall()
                else:
                    rows = cur.execute(f"SELECT id, name FROM {found_table}").fetchall()
            except Exception:
                # try safer select
                rows = cur.execute(f"SELECT * FROM {found_table} LIMIT 1000").fetchall()
            for r in rows:
                if has_slug and len(r) >= 3:
                    products.append({'id': r[0], 'name': r[1], 'slug': r[2]})
                elif len(r) >= 2:
                    products.append({'id': r[0], 'name': r[1], 'slug': None})
        else:
            print('No suitable product table found; sitemap will contain only static pages')
        conn.close()
    except Exception as e:
        print('Error reading DB:', e)
else:
    print('DB not present at', DB)

# static/common pages
pages = [
    '/',
    '/menu',
    '/news',
    '/about',
    '/contact',
    '/downloads',
    '/favorites'
]

urls = []
# include pages for each base domain requested (primary + aliases)
for base in BASES:
    urls.extend([base + p for p in pages])
for p in products:
    path = f"/product/{p['id']}" + (f"/{p['slug']}" if p.get('slug') else "")
    for base in BASES:
        urls.append(base + path)

print('Total urls:', len(urls))

urlset = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
now = datetime.datetime.utcnow().date().isoformat()
for u in urls:
    url = ET.SubElement(urlset, 'url')
    ET.SubElement(url, 'loc').text = u
    ET.SubElement(url, 'lastmod').text = now
    ET.SubElement(url, 'changefreq').text = 'weekly'
    ET.SubElement(url, 'priority').text = '0.6'

ET.ElementTree(urlset).write(OUT, encoding='utf-8', xml_declaration=True)
print('Wrote', OUT)
print('Please review sitemap.xml. Primary domain used:', PRIMARY)
