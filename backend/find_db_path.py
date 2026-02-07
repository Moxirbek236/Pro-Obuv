
with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'DB_PATH =' in line:
            print(f"{i+1}: {line.strip()}")
