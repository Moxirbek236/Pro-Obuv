import json

# Read the file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the JSON structure
# Remove all extra commas and fix structure
lines = content.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    # Remove problematic commas
    if '    "about": "Ilova haqida"' in line and i < len(lines) - 1:
        next_line = lines[i + 1] if i + 1 < len(lines) else ''
        if next_line.startswith('  ,') or next_line.startswith('    ,'):
            fixed_lines.append(line.rstrip(','))
        else:
            fixed_lines.append(line)
    elif line.strip() == '  ,' or line.strip() == '    ,':
        continue  # Skip extra comma lines
    else:
        fixed_lines.append(line)

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print('JSON structure fixed!')
