import sys

def find_all_defs(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if 'def api_bot_' in line:
                print(f"Line {i+1}: {line.strip()}")
            if '@app.route' in line and 'bot' in line:
                print(f"Line {i+1}: {line.strip()}")

if __name__ == "__main__":
    find_all_defs('app.py')
