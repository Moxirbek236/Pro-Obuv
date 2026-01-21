
import re
import os

APP_FILE = "app.py"

if not os.path.exists(APP_FILE):
    print(f"File {APP_FILE} not found!")
    exit(1)

with open(APP_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Regex to find routes
# Simple regex: @app.route("/api/...")
routes = re.findall(r'@app\.route\s*\(\s*["\'](/api/[^"\']+)["\']', content)
unique_routes = sorted(list(set(routes)))

print("Found API routes:")
for r in unique_routes:
    # Print clean route
    print(r)
