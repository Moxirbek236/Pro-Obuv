from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

tpl_dir = r'c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates'
env = Environment(loader=FileSystemLoader(tpl_dir), autoescape=select_autoescape(['html','xml','jinja']))
try:
    tpl = env.get_template('product.html')
    ctx = {
        'item': {'id':123,'name':'Test Shoe','description':'Test','image_url':'/static/defoult.png','rating':4.2,'orders_count':5,'sizes':'40,41','colors':'black,white'},
        'media': [],
        'is_staff': False,
        'is_super_admin': False,
        'marketplaces': {'olx':'https://olx.example/item/1','uzum':'https://uzum.example/item/1','custom_shop':'https://example.com/product/1'},
        'comments':[],
        'user_profile':{},
    }
    out = tpl.render(**ctx)
    print('RENDER_OK')
except Exception as e:
    print('RENDER_ERROR')
    import traceback
    traceback.print_exc()
