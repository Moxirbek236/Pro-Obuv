import re
from collections import Counter

with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Match def function_name(
matches = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(', content)
counts = Counter(matches)

for name, count in counts.items():
    if count > 1:
        print(f"{name}: {count}")
