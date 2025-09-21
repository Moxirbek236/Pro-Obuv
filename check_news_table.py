#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_and_create_news_table():
    db_path = "database.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if news table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
        news_table = cursor.fetchone()
        
        if news_table:
            print("✅ News table exists")
            
            # Show table structure
            cursor.execute("PRAGMA table_info(news)")
            columns = cursor.fetchall()
            print("News table columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
            # Count records
            cursor.execute("SELECT COUNT(*) FROM news")
            count = cursor.fetchone()[0]
            print(f"News records count: {count}")
            
        else:
            print("❌ News table does not exist. Creating it...")
            
            # Create news table
            create_table_sql = '''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT DEFAULT 'news' CHECK (type IN ('news', 'advertisement')),
                is_active BOOLEAN DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                image_url TEXT,
                video_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            '''
            
            cursor.execute(create_table_sql)
            conn.commit()
            print("✅ News table created successfully")
            
            # Insert sample data
            now = "2024-01-15T10:00:00Z"
            sample_news = [
                ("🎉 Yangi Kolleksiya Keldi!", "2024 yilgi eng yangi poyafzal kolleksiyasi do'konimizga keldi.", "news", 1, 1, None, None, now, now),
                ("🔥 50% Chegirma!", "Barcha qishki poyafzallarga 50% gacha chegirma!", "advertisement", 1, 2, None, None, now, now),
                ("🚚 Bepul Yetkazib Berish", "100,000 so'mdan yuqori xaridlarga bepul yetkazib berish.", "advertisement", 1, 3, None, None, now, now),
            ]
            
            cursor.executemany("""
                INSERT INTO news (title, content, type, is_active, display_order, image_url, video_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_news)
            
            conn.commit()
            print("✅ Sample news data inserted")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_and_create_news_table()