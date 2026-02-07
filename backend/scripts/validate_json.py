import json

# Read the current file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Write back with proper formatting
with open('data/translations.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('JSON file has been validated and saved!')
