x#!/usr/bin/env python
"""Check if/endif and block/endblock balance in base.html"""

with open('templates/base.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []  # Stack to track open if/for/block tags
line_num = 0

for line_num, line in enumerate(lines, 1):
    # Skip comments
    if '{#' in line:
        # Remove comments for analysis
        line = line[:line.find('{#')] + line[line.find('#}') + 2:]
    
    # Find if/for/block declarations
    import re
    
    # Count if/for/block opening tags
    ifs = len(re.findall(r'{%\s*if\s', line))
    fors = len(re.findall(r'{%\s*for\s', line))
    blocks = len(re.findall(r'{%\s*block\s', line))
    withs = len(re.findall(r'{%\s*with\s', line))
    
    # Count endif/endfor/endblock/endwith closing tags
    endifs = len(re.findall(r'{%\s*endif\s*%}', line))
    endfors = len(re.findall(r'{%\s*endfor\s*%}', line))
    endblocks = len(re.findall(r'{%\s*endblock\s*%}', line))
    endwiths = len(re.findall(r'{%\s*endwith\s*%}', line))
    
    for _ in range(ifs):
        stack.append(('if', line_num, line.strip()[:80]))
    for _ in range(fors):
        stack.append(('for', line_num, line.strip()[:80]))
    for _ in range(blocks):
        stack.append(('block', line_num, line.strip()[:80]))
    for _ in range(withs):
        stack.append(('with', line_num, line.strip()[:80]))
    
    for _ in range(endifs):
        if stack and stack[-1][0] == 'if':
            stack.pop()
        else:
            print(f"ERROR at line {line_num}: Found {% endif %} but expected to close {stack[-1][0] if stack else 'NOTHING'}")
            if stack:
                print(f"       Last opened {stack[-1][0]} was at line {stack[-1][1]}: {stack[-1][2]}")
    
    for _ in range(endfors):
        if stack and stack[-1][0] == 'for':
            stack.pop()
        else:
            print(f"ERROR at line {line_num}: Found {% endfor %} but expected to close {stack[-1][0] if stack else 'NOTHING'}")
            if stack:
                print(f"       Last opened {stack[-1][0]} was at line {stack[-1][1]}: {stack[-1][2]}")
    
    for _ in range(endblocks):
        if stack and stack[-1][0] == 'block':
            stack.pop()
        else:
            print(f"ERROR at line {line_num}: Found {% endblock %} but expected to close {stack[-1][0] if stack else 'NOTHING'}")
            if stack:
                print(f"       Last opened {stack[-1][0]} was at line {stack[-1][1]}: {stack[-1][2]}")
    
    for _ in range(endwiths):
        if stack and stack[-1][0] == 'with':
            stack.pop()
        else:
            print(f"ERROR at line {line_num}: Found {% endwith %} but expected to close {stack[-1][0] if stack else 'NOTHING'}")
            if stack:
                print(f"       Last opened {stack[-1][0]} was at line {stack[-1][1]}: {stack[-1][2]}")

print(f"\n\nFinal stack (unclosed tags):")
for tag_type, tag_line, tag_text in stack:
    print(f"  {tag_type:8s} at line {tag_line:5d}: {tag_text}")
