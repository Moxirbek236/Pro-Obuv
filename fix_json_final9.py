import json

# Read of file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the specific JSON syntax error
# The issue is with line 391 where there's a missing comma
lines = content.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    # Check if this is the problematic line and fix it
    if i == 390 and '"privacy": "Maxfiylik siyosati"' in line:
        # Replace the next line to add the missing comma
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.startswith('      "terms":'):
                fixed_lines[i + 1] = '      "terms": "Foydalanish shartlari",'
                fixed_lines.append('      "cookies": "Cookie siyosati"')
    else:
        fixed_lines.append(line)

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print('JSON syntax error fixed!')
