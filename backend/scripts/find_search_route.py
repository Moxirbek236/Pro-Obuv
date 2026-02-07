
import re

def find_keywords(filepath):
    print(f"Scanning {filepath} for @app.route and search...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if '@app.route' in line and 'search' in line:
                    print(f"Line {i}: {line.strip()}")
                elif 'def search' in line:
                    print(f"Line {i}: {line.strip()}")
                elif 'keyword' in line.lower():
                    # For keyword enhancement
                    pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_keywords("d:/Safety.uz/backend/app.py")
