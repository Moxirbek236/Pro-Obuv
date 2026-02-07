from pathlib import Path
p=Path('d:/Safety.uz/static/css/menu-modern.css')
s=p.read_text(encoding='utf-8')
brace=0
first_unb=None
for i,ch in enumerate(s, start=1):
    if ch=='{': brace+=1
    if ch=='}':
        brace-=1
        if brace<0 and first_unb is None:
            first_unb=i
print('first_unbalanced_close_line:',first_unb)
print('final_balance:',brace)
print('count_open_comment:', s.count('/*'), 'count_close_comment:', s.count('*/'))
