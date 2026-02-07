import re
import sys
p='d:/Safety.uz/templates/product.html'
with open(p, 'r', encoding='utf-8') as f:
    lines=f.readlines()
stack=[]
pattern=re.compile(r"({%\s*(if|elif|else|endif).*?%})")
for i,line in enumerate(lines, start=1):
    for m in pattern.finditer(line):
        token=m.group(0)
        kind=m.group(2)
        print(i, token)
        if kind=='if':
            stack.append((i, token))
        elif kind in ('elif','else'):
            if not stack:
                print('UNMATCHED', kind, 'at', i)
        elif kind=='endif':
            if not stack:
                print('UNMATCHED endif at', i)
            else:
                stack.pop()

if stack:
    print('\nUnclosed if blocks:')
    for ln,tok in stack:
        print(ln, tok)
    sys.exit(2)
else:
    print('\nAll if/endif balanced')
    sys.exit(0)
