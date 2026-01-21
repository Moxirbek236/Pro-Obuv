import json

# Read of file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the specific JSON syntax error
# The issue is with line 391 where there's a missing comma
fixed_content = content.replace(
    '      "privacy": "Maxfiylik siyosati",\n      "terms": "Foydalanish shartlari",\n      "cookies": "Cookie siyosati"\n    },',
    '      "privacy": "Maxfiylik siyosati",\n      "terms": "Foydalanish shartlari",\n      "cookies": "Cookie siyosati",\n    },'
)

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print('JSON syntax error fixed!')
