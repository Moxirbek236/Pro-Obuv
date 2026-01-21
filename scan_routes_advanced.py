
import re
import json
import os

APP_FILE = "app.py"

routes = []
# Ensure paths list works for stacked decorators
current_paths = []
current_role = "public"

route_regex = re.compile(r'@app\.route\s*\(\s*["\']([^"\']+)["\'](.*)\)')
methods_regex = re.compile(r'methods\s*=\s*\[(.*?)\]')
role_regex = re.compile(r'@role_required\s*\(\s*["\']([^"\']+)["\']\)')
def_regex = re.compile(r'^def\s+([a-zA-Z0-9_]+)\s*\(')

# Regex to capture app.add_url_rule calls
# Pattern: app.add_url_rule('/api/auth/login', 'stub_auth_login', _stub_auth_login, methods=['POST', 'OPTIONS'])
add_url_rule_regex = re.compile(r'app\.add_url_rule\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*,\s*([a-zA-Z0-9_]+)\s*,\s*methods\s*=\s*\[(.*?)\]')

# Track the last added route(s) to check for jsonify in their body
last_added_routes = []

# Helper to categorize tags
def categorise_tag(path):
    tag = "general"
    if path.startswith("/api/"):
        tag = "api"
        if "cart" in path: tag = "cart"
        elif "auth" in path: tag = "auth"
        elif "order" in path: tag = "orders"
        elif "product" in path: tag = "products"
        elif "user" in path: tag = "users"
    elif path.startswith("/admin"):
        tag = "admin"
    elif path.startswith("/super-admin"):
        tag = "super-admin"
    elif path.startswith("/staff"):
        tag = "staff"
    return tag

with open(APP_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line_strip = line.strip()
        
        # 1. @app.route
        m_route = route_regex.search(line_strip)
        if m_route:
            # If we were tracking a function, and we hit a new route, stop tracking the old one
            last_added_routes = []
            
            path = m_route.group(1)
            # Parse methods
            m_methods = methods_regex.search(line_strip)
            methods = ["GET"] # Default
            if m_methods:
                raw_methods = m_methods.group(1).replace("'", "").replace('"', "")
                methods = [m.strip() for m in raw_methods.split(',') if m.strip()]
            
            current_paths.append({"path": path, "methods": methods})
            continue

        # 2. @role_required
        m_role = role_regex.search(line_strip)
        if m_role:
            current_role = m_role.group(1)
            continue

        # 3. app.add_url_rule
        m_add_rule = add_url_rule_regex.search(line_strip)
        if m_add_rule:
            path = m_add_rule.group(1)
            # endpoint = m_add_rule.group(2) # not used directly
            func_name = m_add_rule.group(3)
            raw_methods = m_add_rule.group(4).replace("'", "").replace('"', "")
            methods = [m.strip() for m in raw_methods.split(',') if m.strip()]
            
            route_obj = {
                "path": path,
                "methods": methods,
                "role": "public", # Assume public for manual rules unless context implies otherwise
                "function": func_name,
                "tag": categorise_tag(path),
                "returns_json": True # Manual rules like these stubs usually return JSON
            }
            routes.append(route_obj)
            continue


        # 4. Function definition - triggers saving
        m_def = def_regex.match(line_strip)
        if m_def:
            func_name = m_def.group(1)
            if current_paths:
                for p in current_paths:
                    route_obj = {
                        "path": p["path"],
                        "methods": p["methods"],
                        "role": current_role,
                        "function": func_name,
                        "tag": categorise_tag(p["path"]),
                        "returns_json": False # Default
                    }
                    routes.append(route_obj)
                    last_added_routes.append(route_obj)
                    
                # Reset for next block
                current_paths = []
                current_role = "public"
            else:
                 # It's a def but not for a captured route (or we missed the route)
                 last_added_routes = []
            continue
            
        # 5. Check for jsonify in function body
        if last_added_routes:
            if "jsonify" in line:
                for r in last_added_routes:
                    r["returns_json"] = True
            
        
with open("routes.json", "w", encoding="utf-8") as f:
    json.dump(routes, f, indent=2)
