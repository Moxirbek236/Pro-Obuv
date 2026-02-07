
import re

PATTERNS = [
    (r"\?", "Invalid placeholder '?' found (use '%s' for PostgreSQL)"),
]

SQL_KEYWORDS = ["SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "JOIN", "ORDER BY", "GROUP BY", "LIMIT", "OFFSET"]

def is_sql_line(line):
    upper = line.upper()
    return any(k in upper for k in SQL_KEYWORDS)

def scan_file(filepath):
    print(f"Scanning {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                # skip comments
                if line.strip().startswith('#'):
                    continue
                
                # Simple heuristic: if line contains SQL keyword and '?', flag it
                if is_sql_line(line) and '?' in line:
                    # Ignore legitimate uses of '?' (e.g. URL query strings, regex, ternary operators)
                    # Ternary: a if b else c (no ?)
                    # URL: ?foo=bar inside string is okay but usually not with SQL keywords
                    clean_line = line.strip()
                    print(f"Line {i}: {clean_line[:100]}... -> Potential invalid '?' usage")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_file("d:/Safety.uz/backend/app.py")
