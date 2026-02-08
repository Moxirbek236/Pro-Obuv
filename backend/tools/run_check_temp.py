from app import app

with app.test_client() as c:
    r = c.get('/menu')
    html = r.get_data(as_text=True)
    found_key = 'menu.all_products' in html
    found_phone_display = '+998 97 719 57 70' in html
    print('status_code=', r.status_code)
    print('menu.all_products literal present:', found_key)
    print('phone display present:', found_phone_display)
    start = html.find('<div class="menu-container"')
    print(html[start:start+400])
