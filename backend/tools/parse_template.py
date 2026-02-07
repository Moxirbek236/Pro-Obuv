from jinja2 import Environment, FileSystemLoader
import traceback
env = Environment(loader=FileSystemLoader('templates'))
try:
    t = env.get_template('super_admin_login.html')
    print('Rendering super_admin_login.html ...')
    out = t.render()
    print('Rendered length:', len(out))
except Exception as e:
    print('Error:', type(e), e)
    traceback.print_exc()
