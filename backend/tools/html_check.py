from html.parser import HTMLParser
import re
p = HTMLParser()
text = open(r"c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates\base.html","r",encoding='utf-8').read()
clean = re.sub(r"\{\%.*?\%\}|\{\{.*?\}\}","",text,flags=re.S)
try:
    p.feed(clean)
    print('HTML parse OK')
except Exception as e:
    print('HTML parse ERROR:', e)
