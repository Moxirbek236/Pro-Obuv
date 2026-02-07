
import re

PATTERNS = [
    (r'phone_number', "Potential misuse of 'phone_number' (use 'phone')"),
    (r'username', "Potential misuse of 'username' (use 'email')"),
    (r'is_admin', "Potential misuse of legacy 'is_admin'"),
]

def scan_file(filepath):
    print(f"Scanning {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                # skip comments
                if line.strip().startswith('#'):
                    continue
                
                for pattern, msg in PATTERNS:
                    if re.search(pattern, line):
                        # skip false positives like 'phone_number as phone' which handles aliases correctly usually,
                        # BUT in my case aliases were problematic in query execution if column doesn't exist.
                        # Also skip 'username' if it's just a variable name derived from email.
                        
                        clean_line = line.strip()
                        # Simple heuristics to reduce noise
                        if 'as username' in clean_line: continue # Aliasing is intentional
                        if "'username':" in clean_line: continue # Dict key is fine
                        if '.username' in clean_line: continue # Property access on object is fine
                        
                        print(f"Line {i}: {clean_line[:100]}... -> {msg}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_file("d:/Safety.uz/backend/app.py")
