"""Sync news from data/news.json into the SQLite `news` table.

Usage: python scripts/sync_news_from_json.py

The script will:
- Back up the current `database.sqlite3` to `backups/database.sqlite3.YYYYMMDD_HHMMSS.bak`.
- Read `data/news.json` and insert its items into the `news` table.
- The script attempts to preserve DB schema by inspecting available columns and populating them when present.
- It runs a DELETE FROM news and reinserts the JSON items (clean replacement).

Run this from repository root.
"""
import sqlite3
import json
import os
import shutil
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(REPO_ROOT, "database.sqlite3")
JSON_PATH = os.path.join(REPO_ROOT, "data", "news.json")
BACKUP_DIR = os.path.join(REPO_ROOT, "backups")


def backup_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"database.sqlite3.{ts}.bak")
    shutil.copy2(DB_PATH, dest)
    return dest


def get_table_columns(conn, table_name="news"):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = [r[1] for r in cur.fetchall()]
    return cols


def normalize_item(it):
    # Prepare mapping of JSON fields to DB fields
    title = (it.get("title") or it.get("name") or "").strip()
    # prefer per-language title if available; store main title as provided
    content = (it.get("content") or it.get("description") or "").strip()
    image_url = it.get("image_url") or it.get("image") or None
    video_url = it.get("video_url") or it.get("video") or it.get("youtube_url") or None
    is_active = 1 if it.get("is_active", it.get("published", True)) else 0
    display_order = int(it.get("display_order", 0) or 0)
    show_in_ticker = 1 if it.get("show_in_ticker") or it.get("in_ticker") else 0
    # per-language fields
    title_uz = (it.get("title_uz") or "").strip()
    title_ru = (it.get("title_ru") or "").strip()
    title_en = (it.get("title_en") or "").strip()
    title_kz = (it.get("title_kz") or "").strip()
    content_uz = (it.get("content_uz") or "").strip()
    content_ru = (it.get("content_ru") or "").strip()
    content_en = (it.get("content_en") or "").strip()
    content_kz = (it.get("content_kz") or "").strip()

    return {
        "title": title,
        "content": content,
        "image_url": image_url,
        "video_url": video_url,
        "is_active": is_active,
        "display_order": display_order,
        "show_in_ticker": show_in_ticker,
        "title_uz": title_uz,
        "title_ru": title_ru,
        "title_en": title_en,
        "title_kz": title_kz,
        "content_uz": content_uz,
        "content_ru": content_ru,
        "content_en": content_en,
        "content_kz": content_kz,
    }


def sync_news(backup=True):
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"News JSON not found at {JSON_PATH}")

    if backup:
        b = backup_db()
        print(f"Database backed up to: {b}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    items = raw.get("news") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("news.json does not contain a list under 'news' key")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cols = get_table_columns(conn, "news")
    # We'll remove all rows then insert fresh ones.
    try:
        cur.execute("BEGIN")
        cur.execute("DELETE FROM news")

        # Build insert query based on available columns
        # We'll prefer to insert columns that exist in the table
        insert_cols = [c for c in [
            "title",
            "content",
            "type",
            "image_url",
            "video_url",
            "is_active",
            "display_order",
            "show_in_ticker",
            "title_uz",
            "title_ru",
            "title_en",
            "title_kz",
            "content_uz",
            "content_ru",
            "content_en",
            "content_kz",
            "created_at",
            "updated_at",
        ] if c in cols]

        placeholders = ",".join(["?" for _ in insert_cols])
        insert_sql = f"INSERT INTO news ({','.join(insert_cols)}) VALUES ({placeholders})"

        now = datetime.utcnow().isoformat() + "Z"
        inserted = 0
        for i, it in enumerate(items):
            try:
                n = normalize_item(it)
                # Provide values in same order as insert_cols
                values = []
                for c in insert_cols:
                    if c == "type":
                        # try to get type from JSON
                        values.append(it.get("type") or ("advertisement" if it.get("is_ad") else "news"))
                    elif c == "created_at" or c == "updated_at":
                        values.append(now)
                    else:
                        values.append(n.get(c))
                cur.execute(insert_sql, values)
                inserted += 1
            except Exception as e:
                print(f"Failed inserting item {i}: {e}")
                continue

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return {"inserted": inserted, "total": len(items)}


if __name__ == "__main__":
    try:
        print("Starting sync of news.json -> news table")
        result = sync_news(backup=True)
        print(f"Sync completed: inserted {result['inserted']} of {result['total']} items")
    except Exception as e:
        print("Sync failed:", str(e))
        raise
