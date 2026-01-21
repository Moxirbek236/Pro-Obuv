import json

# Read the file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create a clean, properly structured JSON
clean_data = {}

# Only keep the main language sections
for lang in ['ru', 'uz', 'en']:
    if lang in data:
        clean_data[lang] = data[lang]

# Write back to file
with open('data/translations.json', 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, ensure_ascii=False, indent=2)

print('JSON file has been cleaned and fixed!')
