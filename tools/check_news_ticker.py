import os
import sys
# ensure project root is on sys.path so we can import app
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app

with app.test_client() as c:
    import os, json
    json_path = os.path.join(os.getcwd(), "data", "news.json")
    print('cwd=', os.getcwd())
    print('json_path=', json_path, 'exists=', os.path.exists(json_path))
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                blob = json.load(f)
            items = blob.get('news') if isinstance(blob, dict) else blob
            print('news ids in file=', [int(x.get('id')) for x in items])
        except Exception as e:
            print('failed to read json:', e)

    r = c.get('/news/2')
    print('status_code=', r.status_code)
    body = r.get_data(as_text=True)
    snippet = body[:1000]
    print('body_snippet=')
    print(snippet)
    # Replicate the server-side loop to see if any exceptions occur while processing items
    print('\n-- Replicating server-side processing for debugging --')
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                blob = json.load(f)
            items = blob.get('news') if isinstance(blob, dict) else blob
            for idx, n in enumerate(items or []):
                try:
                    nid = int(n.get('id', 0))
                    print(f'Item #{idx} id={nid} is_active={n.get("is_active")}')
                    if int(n.get('id', 0)) == 2:
                        # simulate localized title/content computation
                        preferred_lang = None
                        try:
                            preferred_lang = None or 'uz'
                            localized_title = n.get(f'title_{preferred_lang}') or n.get('title') or ''
                            localized_content = n.get(f'content_{preferred_lang}') or n.get('content') or n.get('description') or ''
                            print('localized_title sample=', localized_title[:60])
                            # Attempt to render the template to catch Jinja errors that may occur in the real route
                            try:
                                with app.test_request_context(f'/news/{nid}'):
                                    from flask import render_template

                                    seo = {
                                        "page_title": f"{localized_title} - Yangiliklar - Safety.uz",
                                        "meta_description": (localized_content or '')[:160],
                                    }
                                    html = render_template('news_detail.html', news=n, seo_data=seo)
                                    print('rendered length=', len(html))
                            except Exception as render_e:
                                import traceback as _tb

                                print('render exception:')
                                print(_tb.format_exc())
                        except Exception as inner_e:
                            print('inner exception during localization:', inner_e)
                except Exception as e:
                    print('exception while processing item', idx, e)
    except Exception as e:
        print('exception during replication:', e)
