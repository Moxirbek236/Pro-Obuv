from app import app, api_menu_search

with app.test_request_context('/api/menu-search?limit=2&q=Cross'):
    resp = api_menu_search()
    print(resp.get_data(as_text=True))
