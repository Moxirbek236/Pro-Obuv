import re,os,sys
root=r'd:/Safety.uz'
pat=re.compile(r'<script[^>]*>(.*?)</script>', re.S|re.I)
errs=[]
for dirpath,dirs,files in os.walk(root):
    for fn in files:
        if not fn.endswith('.html'): continue
        path=os.path.join(dirpath,fn)
        try:
            txt=open(path,'r',encoding='utf-8').read()
        except Exception as e:
            continue
        for m in pat.finditer(txt):
            script=m.group(1)
            stack=[]
            pairs={'(':')','[':']','{':'}'}
            opens=set(pairs.keys())
            closes={v:k for k,v in pairs.items()}
            for i,ch in enumerate(script):
                if ch in opens:
                    stack.append((ch,i))
                elif ch in closes:
                    if stack and stack[-1][0]==closes[ch]:
                        stack.pop()
                    else:
                        prefix=script[:i]
                        line = prefix.count('\n')+1
                        errs.append((path,line,ch,'unmatched_close'))
            if stack:
                for op,idx in stack:
                    line = script[:idx].count('\n')+1
                    errs.append((path,line,op,'unmatched_open'))
if not errs:
    print('No unmatched parentheses/braces/brackets found in inline <script> blocks.')
else:
    for e in errs[:200]:
        print(e[0], 'line', e[1], e[2], e[3])
