from pathlib import Path
s=Path('tools/script_block_19.js').read_text(encoding='utf-8')
brace=0
paren=0
brack=0
for i,ch in enumerate(s):
    if ch=='{': brace+=1
    elif ch=='}':
        brace-=1
        if brace<0:
            start=max(0,i-120)
            end=min(len(s), i+120)
            print('Negative brace at index',i)
            print('Context:\n', s[start:end])
            break
    elif ch=='(': paren+=1
    elif ch==')':
        paren-=1
        if paren<0:
            start=max(0,i-120)
            end=min(len(s), i+120)
            print('Negative paren at index',i)
            print('Context:\n', s[start:end])
            break
else:
    print('No early negative counts; final deltas: brace',brace,'paren',paren,'brack',s.count('[')-s.count(']'))
