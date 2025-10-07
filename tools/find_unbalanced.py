import re
from pathlib import Path
p = Path(r"c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates\menu.html")
s = p.read_text(encoding='utf-8')
# find script blocks
scripts = re.findall(r"<script[^>]*>(.*?)</script>", s, flags=re.S|re.I)
print('Found', len(scripts), 'script blocks')
# check each block for parentheses balance
for i, sc in enumerate(scripts, start=1):
    par = 0
    first_bad = None
    for idx,ch in enumerate(sc):
        if ch == '(':
            par += 1
        elif ch == ')':
            par -= 1
            if par < 0:
                first_bad = idx
                break
    if first_bad is not None:
        start = max(0, first_bad-120)
        end = min(len(sc), first_bad+120)
        ctx = sc[start:end].replace('\n','\\n')
        print(f'Block {i}: first excess ) at pos {first_bad}')
        print('Context:')
        print(ctx)
        break
else:
    print('No script block had an excess )')
# Also check whole file for overall deltas
print('Whole file paren delta:', s.count('(')-s.count(')'))
print('Whole file brace delta:', s.count('{')-s.count('}'))
print('Whole file bracket delta:', s.count('[')-s.count(']'))
