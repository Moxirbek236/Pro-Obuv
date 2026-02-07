from pathlib import Path
import re
base_path = Path(r"c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates\base.html")
menu_path = Path(r"c:\Users\Moxir_Coder\OneDrive\Desktop\Pro-Obuv\templates\menu.html")
base = base_path.read_text(encoding='utf-8')
menu = menu_path.read_text(encoding='utf-8')
# extract the entire block content including tags from menu
m = re.search(r"({%\s*block\s+content\s*%})(.*?)(\{%\s*endblock\s*%\})", menu, flags=re.S)
if not m:
    print('menu block content not found')
    raise SystemExit(1)
menu_block_full = m.group(0)
menu_block_inner = m.group(2)
# find block in base and replace inner content only
b = re.search(r"({%\s*block\s+content\s*%})(.*?)(\{%\s*endblock\s*%\})", base, flags=re.S)
if not b:
    print('base block content not found')
    raise SystemExit(1)
start, end = b.start(2), b.end(2)
new = base[:start] + menu_block_inner + base[end:]
out = Path('tools/combined_menu_rendered.html')
out.write_text(new, encoding='utf-8')
print('combined length:', len(new))
lines = new.splitlines()
ln = 8324
start = max(0, ln-10)
end = min(len(lines), ln+10)
print('Total lines:', len(lines))
for i in range(start, end):
    print(f'{i+1:6d}: {lines[i]}')
