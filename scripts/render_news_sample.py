import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, extract_youtube_embed, find_youtube_url_in_text
from flask import render_template

news = {
    'id': 9999,
    'title': 'Video yangilik',
    'content': 'Bu yangilikda video bor: https://youtu.be/dQw4w9WgXcQ',
    'image_url': None,
    'video_url': None,
    'created_at': '2025-10-23T12:00:00'
}

with app.test_request_context(f"/news/{news['id']}"):
    # emulate compute youtube_embed like server
    vid = news.get('video_url') or find_youtube_url_in_text(news.get('content') or '')
    print('found vid src:', vid)
    print('embed:', extract_youtube_embed(vid or ''))
    s = render_template('news_detail.html', news={**news, 'youtube_embed': extract_youtube_embed(vid or '')}, seo_data={'page_title': news['title']})
    print('len', len(s))
    print('iframe idx', s.find('<iframe'))
    if s.find('<iframe')!=-1:
        i = s.find('<iframe')
        print(s[i:i+200])
