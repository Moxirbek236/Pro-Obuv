
with open('backend/app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'CORS(' in line:
            print(f"{i+1}: {line.strip()}")
