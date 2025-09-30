import ast
p=r'c:/Users/Moxir_Coder/OneDrive/Desktop/Pro-Obuv/app.py'
try:
    s=open(p,encoding='utf-8').read()
    ast.parse(s)
    print('PARSE_OK')
except SyntaxError as e:
    print('SYNTAX_ERROR', e.lineno, e.offset, e.msg)
    lines=s.splitlines()
    for i in range(max(0,e.lineno-5), min(len(lines), e.lineno+5)):
        print(f"{i+1}: {lines[i]}")
except Exception as e:
    print('ERROR', e)
