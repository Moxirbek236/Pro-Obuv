
import re

def find_templates(filepath):
    print(f"Scanning {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if 'render_template' in line:
                    print(f"Line {i}: {line.strip()}")
                elif 'template_folder' in line:
                    print(f"Line {i}: {line.strip()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_templates("d:/Safety.uz/backend/app.py")
