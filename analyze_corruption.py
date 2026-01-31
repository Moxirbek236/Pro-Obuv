#!/usr/bin/env python

# Read the corrupted base.html
with open('templates/base.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# The problem is likely duplicate content. Let's find the pattern where it might have duplicated
# Look for suspicious patterns like triple endif or repeated large sections

lines = content.split('\n')
print(f"Total lines: {len(lines)}")

# Find all {% if and {% endif %} to check balance
if_count = 0
endif_count = 0
for i, line in enumerate(lines):
    if '{% if ' in line:
        if_count += 1
    if '{% endif %}' in line:
        endif_count += 1

print(f"if count: {if_count}")
print(f"endif count: {endif_count}")
print(f"Difference: {if_count - endif_count} (should be 0)")

# Show lines with issues around 800
print("\nLines 800-830:")
for i in range(800, min(830, len(lines))):
    if '{% if' in lines[i] or '{% endif' in lines[i]:
        print(f"Line {i+1}: {lines[i][:100]}")
