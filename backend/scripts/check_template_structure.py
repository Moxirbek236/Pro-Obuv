#!/usr/bin/env python
import re

with open('templates/base.html', 'r') as f:
    lines = f.readlines()

# Track if/endif balance
stack = []
for i, line in enumerate(lines, 1):
    if '{% if ' in line:
        match = re.search(r'{% if ([^%]*)', line)
        condition = match.group(1).strip() if match else "unknown"
        stack.append((i, condition))
        print(f"Line {i:4d} IF:   {condition[:60]}")
    elif '{% endif %}' in line:
        if stack:
            start_line, start_cond = stack.pop()
            print(f"Line {i:4d} ENDIF: closes line {start_line} ({start_cond[:40]})")
        else:
            print(f"Line {i:4d} ENDIF: UNMATCHED!")
    elif '{% else' in line or '{% elif ' in line:
        if stack:
            start_line, start_cond = stack[-1]
            print(f"Line {i:4d} ELSE:  in block from line {start_line}")

print(f"\nUnclosed blocks: {len(stack)}")
for start_line, cond in stack:
    print(f"  Line {start_line}: {cond[:60]}")
