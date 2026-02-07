#!/usr/bin/env python3
"""
Convert product_media image files to WebP and update the database rows.

Usage: run from repository root (or the script will compute repo root automatically):
    python tools/convert_product_media_to_webp.py

What it does:
- Backups database.sqlite3 to backups/database.sqlite3.YYYYmmdd_HHMMSS
- Scans product_media rows where media_type='image'
- For each row: tries to find the referenced file under the repo's static/ tree
  or under uploads; converts it to WebP (same dirname, .webp extension)
  and updates the media_url in the DB to point to the new .webp path.
- If the file cannot be found, sets the media_url to /static/defoult.webp (configurable)

This script is cautious: it creates a DB backup before making changes and
only updates rows once a converted WebP file has been produced (or a fallback used).
"""
import os
import sys
import sqlite3
import shutil
import datetime
import glob
from pathlib import Path

try:
    from PIL import Image
except Exception:
    Image = None


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "database.sqlite3"
BACKUPS_DIR = REPO_ROOT / "backups"
STATIC_DIR = REPO_ROOT / "static"
DEFAULT_WEBP = "/static/defoult.webp"


def make_backup(db_path: Path) -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / f"database.sqlite3.{ts}.backup"
    shutil.copy2(db_path, dest)
    return dest


def find_file_for_url(url: str) -> Path:
    """Given a media_url (often starting with /static/...), try to locate the file on disk.
    Returns a Path if found, otherwise None.
    """
    if not url:
        return None

    # Normalize
    u = url.split("?")[0]

    # If it's an absolute URL, attempt to extract /static/... part
    if u.startswith("http://") or u.startswith("https://"):
        idx = u.find("/static/")
        if idx != -1:
            u = u[idx:]
        else:
            return None

    if u.startswith("/"):
        u = u[1:]

    # Direct candidate
    candidate = REPO_ROOT / u
    if candidate.exists():
        return candidate

    # If extension is not webp, try same basename with other common extensions in a few places
    base = os.path.splitext(os.path.basename(u))[0]
    # Search static uploads for matching basename
    patterns = [
        f"static/uploads/products/{base}.*",
        f"static/uploads/{base}.*",
        f"static/{base}.*",
        f"**/{base}.*",
    ]
    for p in patterns:
        for match in REPO_ROOT.glob(p):
            if match.is_file():
                return match

    # Nothing found
    return None


def convert_to_webp(src: Path, dest: Path) -> bool:
    """Convert src image to webp saved at dest. Returns True on success."""
    if src.resolve() == dest.resolve():
        # same file (already webp probably)
        return True

    if Image is None:
        print("Pillow not installed. Cannot convert images. Install pillow and re-run.")
        return False

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as im:
            # Convert transparent images appropriately
            if im.mode in ("RGBA", "LA"):
                # For RGBA use lossless webp to preserve transparency
                im.save(dest, format="WEBP", lossless=True, quality=100)
            else:
                im = im.convert("RGB")
                im.save(dest, format="WEBP", quality=85, method=6)
        return True
    except Exception as e:
        print(f"Failed converting {src} -> {dest}: {e}")
        return False


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    print("Creating DB backup...")
    backup = make_backup(DB_PATH)
    print(f"Backup created: {backup}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure product_media table exists
    try:
        cur.execute("SELECT id, menu_item_id, media_type, media_url FROM product_media")
        rows = cur.fetchall()
    except Exception as e:
        print(f"Error reading product_media: {e}")
        conn.close()
        sys.exit(1)

    converted = 0
    skipped = 0
    updated_to_default = 0
    errors = 0

    for r in rows:
        mid = r["id"]
        media_type = (r["media_type"] or "").lower()
        media_url = r["media_url"] or ""

        if media_type != "image":
            skipped += 1
            continue

        # If already ends with .webp, skip
        if media_url.lower().endswith(".webp"):
            skipped += 1
            continue

        src = find_file_for_url(media_url)
        if not src:
            # set to default
            try:
                cur.execute("UPDATE product_media SET media_url = ? WHERE id = ?", (DEFAULT_WEBP, mid))
                conn.commit()
                updated_to_default += 1
                print(f"Row {mid}: source not found, set to default {DEFAULT_WEBP}")
            except Exception as e:
                print(f"Failed updating row {mid} to default: {e}")
                errors += 1
            continue

        # Compute dest path (same directory, webp extension)
        dest = src.with_suffix('.webp')

        # If dest already exists, just update DB to point to it
        if dest.exists():
            rel = '/' + str(dest.relative_to(REPO_ROOT)).replace('\\', '/')
            try:
                cur.execute("UPDATE product_media SET media_url = ? WHERE id = ?", (rel, mid))
                conn.commit()
                converted += 1
                print(f"Row {mid}: updated DB to existing webp {rel}")
            except Exception as e:
                print(f"Failed updating row {mid} to existing webp {rel}: {e}")
                errors += 1
            continue

        # Try to convert
        ok = convert_to_webp(src, dest)
        if not ok:
            print(f"Row {mid}: conversion failed for {src}")
            errors += 1
            continue

        # Update DB
        rel = '/' + str(dest.relative_to(REPO_ROOT)).replace('\\', '/')
        try:
            cur.execute("UPDATE product_media SET media_url = ? WHERE id = ?", (rel, mid))
            conn.commit()
            converted += 1
            print(f"Row {mid}: converted {src} -> {rel}")
        except Exception as e:
            print(f"Row {mid}: conversion succeeded but DB update failed: {e}")
            errors += 1

    conn.close()

    print("--- Summary ---")
    print(f"Total rows scanned: {len(rows)}")
    print(f"Converted/updated: {converted}")
    print(f"Set to default (missing source): {updated_to_default}")
    print(f"Skipped (non-image or already webp): {skipped}")
    print(f"Errors: {errors}")
    print(f"DB backup: {backup}")


if __name__ == '__main__':
    main()
