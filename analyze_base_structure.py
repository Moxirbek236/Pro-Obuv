#!/usr/bin/env python
import re

with open('templates/base.html', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find all if/endif before line 807
for i, line in enumerate(lines[:807], 1):
    if '{% if ' in line or '{% endif %}' in line:
        print(f"Line {i}: {line.strip()[:100]}")
