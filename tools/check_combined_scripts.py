from pathlib import Path
import re
p=Path('tools/combined_menu_rendered.html')
s=p.read_text(encoding='utf-8')
# Extract script blocks
scripts = re.findall(r"<script[^>]*>(.*?)</script>", s, flags=re.S|re.I)
print('Found', len(scripts), 'script blocks in combined file')
for i, sc in enumerate(scripts, start=1):
    # Trim leading/trailing whitespace
    sc_clean = sc.strip()
    # Check balance
    par=0; brace=0; brack=0
    first_bad=None
    for idx,ch in enumerate(sc_clean):
        if ch=='(':
            par+=1
        elif ch==')':
            par-=1
            if par<0 and first_bad is None:
                first_bad=('paren', idx)
                break
        elif ch=='{':
            brace+=1
        elif ch=='}':
            brace-=1
            if brace<0 and first_bad is None:
                first_bad=('brace', idx)
                break
        elif ch=='[':
            brack+=1
        elif ch==']':
            brack-=1
            if brack<0 and first_bad is None:
                first_bad=('brack', idx)
                break
    if first_bad:
        kind, pos = first_bad
        start=max(0,pos-120)
        end=min(len(sc_clean), pos+120)
        ctx = sc_clean[start:end].replace('\n','\\n')
        print(f'Block {i}: first early closing {kind} at pos {pos}')
        print('Context:', ctx)
        print('---')
        # If this is block 17 or 19, also write a small context file
        if i in (17,19):
            Path(f'tools/block_{i}_context.txt').write_text(sc_clean[start:end], encoding='utf-8')
            print(f'Wrote tools/block_{i}_context.txt')
    else:
        # report final deltas
        print(f'Block {i}: deltas par={sc_clean.count("(")-sc_clean.count(")")}, brace={sc_clean.count("{")-sc_clean.count("}")}, brack={sc_clean.count("[")-sc_clean.count("]")}')

# Save block 17 for manual inspection if it exists
if len(scripts) >= 17:
    Path('tools/script_block_17.js').write_text(scripts[16], encoding='utf-8')
    print('Wrote tools/script_block_17.js for inspection')
if len(scripts) >= 19:
    Path('tools/script_block_19.js').write_text(scripts[18], encoding='utf-8')
    print('Wrote tools/script_block_19.js for inspection')
