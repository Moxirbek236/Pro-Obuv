import re
from collections import Counter

def find_duplicates(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    route_pattern = re.compile(r"@app\.route\(['\"]([^'\"]+)['\"]")
    func_pattern = re.compile(r"def\s+([a-zA-Z0-9_]+)\s*\(")
    
    routes = []
    funcs = []
    
    for i, line in enumerate(lines):
        route_match = route_pattern.search(line)
        if route_match:
            routes.append((route_match.group(1), i + 1))
            
        func_match = func_pattern.search(line)
        if func_match:
            # Check if it has a route decorator before it
            if i > 0 and "@app.route" in lines[i-1]:
                funcs.append((func_match.group(1), i + 1))

    print("--- Duplicate Routes ---")
    route_counts = Counter([r[0] for r in routes])
    for r, count in route_counts.items():
        if count > 1:
            locs = [loc[1] for loc in routes if loc[0] == r]
            print(f"Route '{r}' found at lines: {locs}")

    print("\n--- Duplicate Functions (with @app.route) ---")
    func_counts = Counter([f[0] for f in funcs])
    for f, count in func_counts.items():
        if count > 1:
            locs = [loc[1] for loc in funcs if loc[0] == f]
            print(f"Function '{f}' found at lines: {locs}")

if __name__ == "__main__":
    find_duplicates('app.py')
