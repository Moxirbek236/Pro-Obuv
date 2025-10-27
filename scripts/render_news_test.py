import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, load_news
from flask import render_template

with app.test_request_context('/news'):
    news = load_news()
    print('Loaded news count:', len(news))
    s = render_template('news.html', news=news)
    print('news.html length', len(s))
    # Find first iframe occurrence
    idx = s.find('<iframe')
    print('iframe idx in list:', idx)

# try render first news detail
if news:
    nid = news[0].get('id')
    with app.test_request_context(f'/news/{nid}'):
        s2 = render_template('news_detail.html', news=news[0], seo_data={'page_title':news[0].get('title')})
        print('news_detail length', len(s2))
        print('iframe idx in detail:', s2.find('<iframe'))
