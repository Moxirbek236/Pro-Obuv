#!/usr/bin/env python3
"""
convert_db_images_to_webp.py

Scan the project's SQLite database for text columns that look like they store image paths
and propose (or apply) changes substituting .jpg/.jpeg/.png -> .webp when the corresponding
.webp file exists in the project's static directory.

Usage:
  python tools/convert_db_images_to_webp.py         # dry-run (report only)
  python tools/convert_db_images_to_webp.py --apply # actually update the DB

This script is non-destructive by default and prints a CSV-like report of proposed changes.
"""
import os
import sqlite3
import argparse
import sys
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT, 'database.sqlite3')
STATIC_ROOT = os.path.join(ROOT, 'static')

EXTS = ['.webp', '.jpg', '.jpeg', '.png']

def normalize_to_static_path(value):
    """Given a DB value, try to extract a local /static/... path if possible."""
    if not value:
        return None
    v = str(value).strip()
    # If full URL, try to find /static/ fragment
    if v.startswith('http://') or v.startswith('https://'):
        parsed = urlparse(v)
        path = parsed.path or ''
        if '/static/' in path:
            i = path.find('/static/')
            return path[i:]
        return None
    # If starts with /static or static
    if v.startswith('/static/'):
        return v
    if v.startswith('static/'):
        return '/' + v
    # Sometimes values stored as relative like uploads/...
    if v.startswith('uploads/') or v.startswith('images/'):
        return '/static/' + v
    # If it contains /static/ somewhere, extract
    if '/static/' in v:
        i = v.find('/static/')
        return v[i:]
    return None


def fs_path_for_static_url(url_path):
    # url_path like '/static/uploads/abc.jpg' -> filesystem path
    if not url_path:
        return None
    rel = url_path.lstrip('/')
    return os.path.join(ROOT, rel.replace('/', os.sep))


def find_image_columns(conn):
    """Return list of (table, column) where column name looks like it stores images (heuristic)."""
    cur = conn.cursor()
    tables = []
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    for name, sql in cur.fetchall():
        tables.append(name)
    cols = []
    for t in tables:
        try:
            cur.execute(f"PRAGMA table_info('{t}')")
            for row in cur.fetchall():
                # row: cid, name, type, notnull, dflt_value, pk
                colname = row[1]
                coltype = (row[2] or '').upper()
                if coltype in ('TEXT', ''):
                    lname = colname.lower()
                    if any(k in lname for k in ('image', 'img', 'media', 'avatar', 'photo', 'picture')):
                        cols.append((t, colname))
        except Exception:
            continue
    return cols


def scan_and_report(apply=False):
    if not os.path.exists(DB_PATH):
        print('Database not found at', DB_PATH)
        return 2
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cols = find_image_columns(conn)
    if not cols:
        print('No candidate image columns found in DB (heuristic).')
        return 0
    changes = []
    cur = conn.cursor()
    for table, col in cols:
        try:
            cur.execute(f"SELECT rowid, {col} FROM '{table}' WHERE {col} IS NOT NULL AND {col} != ''")
        except Exception:
            # older SQLite may require quoting differently
            try:
                cur.execute(f"SELECT rowid, \"{col}\" FROM \"{table}\" WHERE \"{col}\" IS NOT NULL AND \"{col}\" != ''")
            except Exception:
                continue
        for row in cur.fetchall():
            rid = row['rowid'] if 'rowid' in row.keys() else None
            val = row[ col ]
            s = normalize_to_static_path(val)
            if not s:
                continue
            base, ext = os.path.splitext(s)
            ext_lower = ext.lower()
            if ext_lower == '.webp':
                continue
            # Proposed new path
            new_url = base + '.webp'
            new_fs = fs_path_for_static_url(new_url)
            if new_fs and os.path.exists(new_fs):
                changes.append((table, col, rid, val, new_url))
    # Print report
    if not changes:
        print('No DB image paths found that have a corresponding .webp file on disk. Nothing to do.')
        return 0
    print('Table,Column,RowID,OldValue,NewValue')
    for t,c,r,old,new in changes:
        print(f'{t},{c},{r},{old},{new}')
    if apply:
        print('\nApplying changes to DB (this will modify the sqlite file).')
        for t,c,r,old,new in changes:
            try:
                cur.execute(f"UPDATE '{t}' SET {c} = ? WHERE rowid = ?", (new, r))
            except Exception:
                try:
                    cur.execute(f"UPDATE \"{t}\" SET \"{c}\" = ? WHERE rowid = ?", (new, r))
                except Exception as e:
                    print('Failed to update', t, c, r, e)
        conn.commit()
        print('Applied', len(changes), 'changes.')
    else:
        print('\nDry-run complete. Re-run with --apply to modify the database.')
    conn.close()
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true', help='Actually write changes to the database')
    args = p.parse_args()
    return scan_and_report(apply=args.apply)

if __name__ == '__main__':
    sys.exit(main())
