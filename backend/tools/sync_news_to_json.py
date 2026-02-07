#!/usr/bin/env python3
"""
Sync news from database to data/news.json file
This script reads news from database and writes to JSON file
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.dirname(__file__))

from app import execute_query, get_current_time

def sync_news_to_json():
    """Sync news from database to JSON file"""
    print("\n" + "="*80)
    print("NEWS SYNCHRONIZATION - DATABASE TO JSON")
    print("="*80 + "\n")
    
    try:
        # Fetch all news from database
        query = """SELECT id, title, content, type, image_url, video_url, is_active, 
                          display_order, created_at, updated_at,
                          title_uz, title_ru, title_en, title_kz,
                          content_uz, content_ru, content_en, content_kz
                   FROM news 
                   ORDER BY display_order ASC, created_at DESC"""
        
        rows = execute_query(query, fetch_all=True)
        
        if not rows:
            print("✗ No news items found in database")
            return False
        
        print(f"✓ Found {len(rows)} news items in database\n")
        
        # Convert rows to JSON-serializable dicts
        items = []
        for row in rows:
            try:
                if isinstance(row, dict):
                    item = dict(row)
                else:
                    # Handle tuple/Row object
                    item = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'type': row[3],
                        'image_url': row[4],
                        'video_url': row[5],
                        'is_active': bool(row[6]),
                        'display_order': row[7],
                        'created_at': row[8],
                        'updated_at': row[9],
                        'title_uz': row[10],
                        'title_ru': row[11],
                        'title_en': row[12],
                        'title_kz': row[13],
                        'content_uz': row[14],
                        'content_ru': row[15],
                        'content_en': row[16],
                        'content_kz': row[17],
                    }
                
                # Ensure booleans
                item['is_active'] = bool(item.get('is_active', True))
                
                # Add youtube_embed URL if video is YouTube
                video_url = item.get('video_url', '')
                if video_url and ('youtube' in video_url or 'youtu.be' in video_url):
                    # Extract video ID and create embed URL
                    if 'youtube.com' in video_url:
                        video_id = video_url.split('v=')[1].split('&')[0] if 'v=' in video_url else ''
                    else:
                        video_id = video_url.split('/')[-1] if '/' in video_url else ''
                    
                    if video_id:
                        item['youtube_embed'] = f'https://www.youtube.com/embed/{video_id}'
                
                items.append(item)
                print(f"  ✓ Item {item['id']}: {item.get('title', 'Untitled')[:50]}")
            except Exception as e:
                print(f"  ✗ Error processing row: {e}")
                continue
        
        if not items:
            print("\n✗ No items could be processed")
            return False
        
        # Create JSON structure
        news_data = {
            'news': items,
            'metadata': {
                'total_count': len(items),
                'active_count': len([i for i in items if i.get('is_active')]),
                'last_updated': get_current_time().isoformat(),
                'version': '1.1'
            }
        }
        
        # Write to file
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Successfully synced {len(items)} news items to data/news.json")
        print(f"  Active: {news_data['metadata']['active_count']}")
        print(f"  Total: {news_data['metadata']['total_count']}")
        print(f"  Updated: {news_data['metadata']['last_updated']}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Sync failed: {e}")
        return False

if __name__ == "__main__":
    from app import app
    with app.app_context():
        success = sync_news_to_json()
        sys.exit(0 if success else 1)
