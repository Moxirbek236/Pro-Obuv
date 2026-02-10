with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 'api_bot_categories' in line:
            print(f"{i+1}: {line.strip()}")
