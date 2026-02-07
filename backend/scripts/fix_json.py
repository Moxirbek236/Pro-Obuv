import json

# Read the current file
with open('data/translations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create a clean, properly structured JSON
clean_data = {
    "ru": data["ru"],
    "uz": data["uz"], 
    "en": data["en"]
}

# Write back to file with proper formatting
with open('data/translations.json', 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, ensure_ascii=False, indent=2)

print("JSON file has been cleaned and fixed!")
