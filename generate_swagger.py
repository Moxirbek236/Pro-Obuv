
import json
import re

INPUT_FILE = "routes.json"
OUTPUT_FILE = "swagger.yaml"

try:
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        routes = json.load(f)
except FileNotFoundError:
    print("routes.json not found. Run scan_routes_advanced.py first.")
    exit(1)

# Base swagger content with schemas
swagger_content = """openapi: 3.0.3
info:
  title: Safety.uz API
  description: Automatically generated OpenAPI 3.0 specification for Safety.uz.
  version: 1.0.0
servers:
  - url: /
    description: Current server
tags:
  - name: api
    description: Public API endpoints
  - name: admin
    description: Admin panel endpoints
  - name: super-admin
    description: Super Admin endpoints
  - name: staff
    description: Staff endpoints
  - name: general
    description: General website pages
  - name: auth
    description: Authentication
  - name: cart
    description: Shopping Cart
  - name: orders
    description: Order management
  - name: products
    description: Product catalog
  - name: users
    description: User management

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    SessionAuth:
      type: apiKey
      in: cookie
      name: session
  schemas:
    ErrorResponse:
      type: object
      properties:
        success:
          type: boolean
        message:
          type: string
        code:
          type: integer
    AuthLoginRequest:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
      required: [email, password]
    AuthRegisterRequest:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
        first_name:
          type: string
        last_name:
          type: string
      required: [email, password]
    AuthStatusResponse:
      type: object
      properties:
        success:
          type: boolean
        logged_in:
          type: boolean
        user:
          $ref: '#/components/schemas/User'
    User:
      type: object
      properties:
        id:
          type: integer
        email:
          type: string
        first_name:
          type: string
        last_name:
          type: string
        phone:
          type: string
      required: [id, email]
    Product:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        description:
          type: string
        price:
          type: number
          format: float
        image_url:
          type: string
        category:
          type: string
        rating:
          type: number
          format: float
      required: [id, name]
    Category:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
    OrderItem:
      type: object
      properties:
        product_id:
          type: integer
        quantity:
          type: integer
        price:
          type: number
    Order:
      type: object
      properties:
        id:
          type: integer
        user_id:
          type: integer
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'
        total:
          type: number
    CartItem:
      type: object
      properties:
        itemId:
          type: integer
        product_id:
          type: integer
        quantity:
          type: integer
    Rating:
      type: object
      properties:
        id:
          type: integer
        product_id:
          type: integer
        user_id:
          type: integer
        rating:
          type: integer
        comment:
          type: string
    NewsItem:
      type: object
      properties:
        id:
          type: integer
        title:
          type: string
        content:
          type: string
        image_url:
          type: string
        is_active:
          type: boolean

paths:
"""

# Helper to convert flask path to swagger path
def flask_to_swagger(path):
    # /api/orders/<int:order_id> -> /api/orders/{order_id}
    # Handle int/string/path converters
    return re.sub(r'<[^:]*:?([^>]+)>', r'{\1}', path)

# Filter only JSON/API routes
filtered_routes = []
for r in routes:
    path = r['path']
    func = r['function']
    
    # Logic to identify API routes
    # 1. Starts with /api/
    # 2. Ends with .json
    # 3. Function name starts with api_
    # 4. Function name contains _json
    if path.startswith("/api/") or \
       path.endswith(".json") or \
       func.startswith("api_") or \
       "_json" in func or \
       r.get('returns_json', False) or \
       path == "/auth/login" or path == "/auth/register":
        filtered_routes.append(r)

print(f"Filtered {len(filtered_routes)} API routes from {len(routes)} total.")

# Group by swagger path
grouped_paths = {}
for r in filtered_routes:
    sw_path = flask_to_swagger(r['path'])
    if sw_path not in grouped_paths:
        grouped_paths[sw_path] = []
    grouped_paths[sw_path].append(r)

# Sort paths to keep file stable
sorted_paths = sorted(grouped_paths.keys())

for path in sorted_paths:
    group = grouped_paths[path]
    swagger_content += f"  {path}:\n"
    
    # Check for path parameters
    path_params = re.findall(r'\{([^}]+)\}', path)
    
    # Collect defined operations to avoid duplicates (e.g. same path/method in multiple route entries)
    defined_methods = set()

    for r in group:
        for method in r['methods']:
            m = method.lower()
            if m in defined_methods:
                continue
            defined_methods.add(m)

            swagger_content += f"    {m}:\n"
            # Refine tags based on path keywords
            tag = r['tag']
            if "super-admin" in path:
                tag = "super-admin"
            elif "/admin/" in path or "admin_" in r['function']: # Be careful not to tag generic /api/admin if it doesn't exist, but usually safe
                tag = "admin"
            elif "staff" in path:
                tag = "staff"

            swagger_content += f"      tags: [{tag}]\n"
            summary = r['function'].replace('_', ' ').capitalize()
            swagger_content += f"      summary: {summary}\n"
            swagger_content += f"      operationId: {r['function']}_{m}\n"
            
            # Parameters
            if path_params:
                swagger_content += "      parameters:\n"
                for param in path_params:
                    swagger_content += f"        - in: path\n"
                    swagger_content += f"          name: {param}\n"
                    swagger_content += f"          schema:\n"
                    # Simple heuristic for type
                    if "id" in param or "no" in param:
                        swagger_content += f"            type: integer\n"
                    else:
                        swagger_content += f"            type: string\n"
                    swagger_content += f"          required: true\n"

            # Security
            if r['role'] != 'public':
                swagger_content += "      security:\n"
                swagger_content += "        - SessionAuth: []\n"
                swagger_content += "        - BearerAuth: []\n"

            # Specific Request Bodies for Auth
            if path == "/api/auth/login" and m == "post":
                swagger_content += "      requestBody:\n"
                swagger_content += "        required: true\n"
                swagger_content += "        content:\n"
                swagger_content += "          application/json:\n"
                swagger_content += "            schema:\n"
                swagger_content += "              $ref: '#/components/schemas/AuthLoginRequest'\n"
            
            if path == "/api/auth/register" and m == "post":
                swagger_content += "      requestBody:\n"
                swagger_content += "        required: true\n"
                swagger_content += "        content:\n"
                swagger_content += "          application/json:\n"
                swagger_content += "            schema:\n"
                swagger_content += "              $ref: '#/components/schemas/AuthRegisterRequest'\n"


            swagger_content += "      responses:\n"
            swagger_content += "        '200':\n"
            swagger_content += "          description: Successful operation\n"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(swagger_content)

print(f"Generated {OUTPUT_FILE} with {len(grouped_paths)} paths.")

# Convert to JSON for Swagger UI
try:
    import yaml
    import json
    import os
    
    # Check if static folder exists
    if not os.path.exists("static"):
        os.makedirs("static")
        
    json_path = os.path.join("static", "openapi.json")
    
    # Parse the YAML string we just built
    spec = yaml.safe_load(swagger_content)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
        
    print(f"Generated {json_path} for use in Swagger UI.")
    
except ImportError:
    print("PyYAML not installed, could not generate static/openapi.json. Please install pyyaml.")
except Exception as e:
    print(f"Error generating JSON: {e}")
