from pathlib import Path
import re
base = Path(r"c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates\base.html").read_text(encoding='utf-8')
menu = Path(r"c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates\menu.html").read_text(encoding='utf-8')
# extract content between block content in menu
m = re.search(r"{%\s*block\s+content\s*%}(.*){%\s*endblock\s*%}", menu, flags=re.S)
if not m:
    print('menu block content not found')
    exit(1)
menu_content = m.group(1)
# replace content block in base
new = re.sub(r"{%\s*block\s+content\s*%}(.*){%\s*endblock\s*%}", "{% block content %}" + menu_content + "{% endblock %}", base, flags=re.S)
# write to temp file
out = Path('tools/combined_menu_rendered.html')
out.write_text(new, encoding='utf-8')
print('combined length:', len(new))
# print around line 8324
lines = new.splitlines()
ln = 8324
start = max(0, ln-10)
end = min(len(lines), ln+10)
print('Total lines:', len(lines))
for i in range(start, end):
    print(f'{i+1:6d}: {lines[i]}')
