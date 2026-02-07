import os
import re

# Qaysi fayllarni tekshiramiz
EXTENSIONS = (".js", ".ts", ".py", ".php")

# Xavfli SQL belgilar (oddiy va samarali)
SQL_PATTERNS = [
    r"SELECT\s+.*\+.*FROM",          # JS/PHP string concat
    r"INSERT\s+.*\+.*INTO",
    r"UPDATE\s+.*\+.*SET",
    r"DELETE\s+.*\+.*FROM",

    r"SELECT\s+.*\{.*\}.*FROM",      # Python f-string
    r"INSERT\s+.*\{.*\}.*INTO",

    r"\.format\s*\(",                # Python .format()
    r"\$\{.*\}",                      # JS template literal

    r"WHERE\s+.*=.*['\"]\s*\+",
]

def scan_file(path):
    issues = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, start=1):
            for pattern in SQL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append((i, line.strip()))
    except Exception as e:
        pass
    return issues

def scan_project(root):
    results = {}

    for folder, _, files in os.walk(root):
        for file in files:
            if file.endswith(EXTENSIONS):
                full_path = os.path.join(folder, file)
                found = scan_file(full_path)
                if found:
                    results[full_path] = found

    return results

if __name__ == "__main__":
    project_path = input("📂 Loyiha papkasini kiriting: ").strip()
    report = scan_project(project_path)

    if not report:
        print("\n✅ Xavfli SQL query topilmadi. Yaxshi holat.")
    else:
        print("\n⚠️ EHTIMOLIY SQL XAVFLAR TOPILDI:\n")
        for file, issues in report.items():
            print(f"\n📄 {file}")
            for line_no, code in issues:
                print(f"  🔴 {line_no}-qatorda: {code}")

        print("\n🛠 Tavsiya:")
        print(" - Parameterized query ishlating (?, $1)")
        print(" - ORM yoki prepared statement qo‘llang")
