import os
from collections import defaultdict
root = 'templates'
blocks = defaultdict(lambda: defaultdict(int))
for dirpath, dirs, files in os.walk(root):
    for f in files:
        if not f.endswith('.html'): continue
        p = os.path.join(dirpath, f)
        with open(p, 'r', encoding='utf-8') as fh:
            txt = fh.read()
        blocks[p]['block head'] = txt.count('{% block head')
        blocks[p]['block content'] = txt.count('{% block content')
        blocks[p]['endblock'] = txt.count('{% endblock')
for p, cnts in blocks.items():
    if cnts['block head'] or cnts['block content']:
        print(p, dict(cnts))
