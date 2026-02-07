import json

# Read the current file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the JSON by removing the problematic comma and fixing structure
# Find the problematic line and fix it
lines = content.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    if '    "cat_consultation": "Konsultatsiya",\n    "payment_methods": "To\'lov usullari"' in line:
        # Remove the problematic comma
        fixed_line = line.replace('    "cat_consultation": "Konsultatsiya",\n    "payment_methods": "To\'lov usullari"', '    "cat_consultation": "Konsultatsiya",\n    "payment_methods": "To\'lov usullari"')
    else:
        fixed_line = line
    fixed_lines.append(fixed_line)

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print('JSON syntax fixed!')
