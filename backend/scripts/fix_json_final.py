import json

# Read the current file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the JSON by removing the problematic comma
fixed_content = content.replace('    "cat_consultation": "Konsultatsiya",\n    "payment_methods": "To\'lov usullari"')

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print('JSON syntax fixed!')
