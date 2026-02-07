import json
from collections import Counter

def check_duplicates(ordered_pairs):
    keys = [k for k, v in ordered_pairs]
    counts = Counter(keys)
    duplicates = [k for k, count in counts.items() if count > 1]
    if duplicates:
        print(f"Duplicates found: {duplicates}")
    return dict(ordered_pairs)

try:
    with open(r'd:\Safety.uz\data\translations.json', encoding='utf-8') as f:
        data = json.load(f, object_pairs_hook=check_duplicates)
    print("No duplicates found in top level or nested objects (with one-level check).")
except Exception as e:
    print(f"Error: {e}")
