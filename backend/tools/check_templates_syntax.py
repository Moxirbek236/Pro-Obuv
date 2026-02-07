import os
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

errors = []
for t in env.list_templates(extensions=['html']):
    try:
        src = env.loader.get_source(env, t)[0]
        env.parse(src)
    except TemplateSyntaxError as e:
        errors.append((t, e.lineno, e.message))

if not errors:
    print('No Jinja syntax errors detected in templates')
else:
    for t, ln, msg in errors:
        print(f"Template error in {t} at line {ln}: {msg}")
    raise SystemExit(1)
