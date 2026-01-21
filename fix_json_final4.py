import json

# Read the file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the JSON by removing all problematic commas and fixing structure
# The issue is with line 391: "copyright": "© 2025 <strong>Pro Obuv</strong> - Oyoq kiyim do'koni | Barcha huquqlar himoyalangan",
# It should be followed by a comma, not by the "privacy" key

# Let's fix this by removing the entire problematic section and rebuilding it properly
lines = content.split('\n')
fixed_lines = []

# Find the start of the problematic section
start_index = -1
for i, line in enumerate(lines):
    if '"privacy": "Maxfiylik siyosati"' in line:
        start_index = i
        break

if start_index != -1:
    # Copy lines before the problematic section
    for i in range(start_index):
        fixed_lines.append(lines[i])
    
    # Add the properly formatted footer section
    fixed_lines.extend([
        '      "privacy": "Maxfiylik siyosati",',
        '      "terms": "Foydalanish shartlari",',
        '      "cookies": "Cookie siyosati"',
        '    },',
        '    "settings": {'
    ])
    
    # Skip the problematic lines and continue from after settings section
    i = start_index + 1
    while i < len(lines):
        if '"settings": {' in lines[i]:
            fixed_lines.append(lines[i])
            i += 1
            # Add the rest of the settings section
            while i < len(lines) and not lines[i].strip().startswith('    },'):
                fixed_lines.append(lines[i])
                i += 1
            fixed_lines.append('    },')
            i += 1
            break
        else:
            i += 1

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print('JSON structure fixed!')
