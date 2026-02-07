from pathlib import Path
s=Path('tools/script_block_17.js').read_text(encoding='utf-8')
pos=1225
start=max(0,pos-80)
end=min(len(s), pos+80)
print('len',len(s))
print('Context around',pos,':')
print(repr(s[start:end]))
print('\n--- lines around ---\n')
lines=s[:pos+80].splitlines()
for i,l in enumerate(lines[-8:], start=len(lines)-7):
    print(i, l)
