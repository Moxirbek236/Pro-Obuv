import sqlite3
import os
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB = REPO_ROOT / 'database.sqlite3'
OUT = REPO_ROOT / 'tools' / 'product_media_report.csv'

def main():
    if not DB.exists():
        print('Database not found:', DB)
        return
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, menu_item_id, media_type, media_url FROM product_media')
        rows = cur.fetchall()
    except Exception as e:
        print('Error reading product_media:', e)
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id','menu_item_id','media_type','media_url','file_exists'])
        for r in rows:
            url = (r['media_url'] or '').strip()
            fs = ''
            exists = False
            if url:
                if url.startswith('/'):
                    fs = REPO_ROOT / url.lstrip('/')
                else:
                    fs = REPO_ROOT / url
                exists = fs.exists()
            w.writerow([r['id'], r['menu_item_id'], r['media_type'], url, exists])

    print('Wrote', OUT)

if __name__ == '__main__':
    main()