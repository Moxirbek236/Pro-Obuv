# How to Test the News API with CSRF Protection

## The Problem

You're getting a 403 FORBIDDEN error because you're testing via **Swagger UI** or an **API client** (like Postman), which doesn't have access to the CSRF token that's generated in the web page session.

The debug output shows:
```
X-CSRF-Token header: None
csrf_token in JSON: None
JSON body: {'title': 'string', 'content': 'string', ...}  ← Default Swagger values
```

## Solution 1: Test via the Actual News Form (RECOMMENDED)

This is the proper way to test since the form has all the CSRF token handling built-in:

1. **Navigate to** `http://localhost:5000/admin/news/new`
2. **Open DevTools Console** (F12)
3. **Fill in the form** with real data
4. **Click "Saqlash"**
5. **Check console** for the debug output showing the token

You should see:
```
=== CSRF Token Debug ===
From meta tag: OhZI3ftPw3...
Final token: OhZI3ftPw3SROoAqObbQQ6wJ63uvkcaZyhhidL9FcDM
CSRF Token being sent: OhZI3ftPw3SROoAqObbQQ6wJ63uvkcaZyhhidL9FcDM
```

## Solution 2: Get CSRF Token for Swagger/API Testing

If you want to test via Swagger UI or Postman:

### Step 1: Get the CSRF Token

1. Open `http://localhost:5000/admin/news/new` in your browser
2. Open DevTools Console (F12)
3. Run this command:
   ```javascript
   console.log(window.CSRF_TOKEN)
   ```
   Or:
   ```javascript
   console.log(document.querySelector('meta[name="csrf-token"]').content)
   ```
4. **Copy the token** (it will be ~43 characters long)

### Step 2: Add Token to Swagger Request

In Swagger UI, when making the POST request to `/api/news`:

**Option A: Add to Headers**
```
X-CSRF-Token: <paste-your-token-here>
```

**Option B: Add to JSON Body**
```json
{
  "csrf_token": "<paste-your-token-here>",
  "title": "Test News",
  "content": "Test content",
  "is_active": true
}
```

### Step 3: Make the Request

The request should now succeed!

## Solution 3: Temporarily Disable CSRF for API Testing (NOT RECOMMENDED)

⚠️ **WARNING**: Only do this in development, never in production!

You can temporarily comment out the `@csrf_protect` decorator:

```python
@app.route("/api/news", methods=["POST"])
@role_required("super_admin")
# @csrf_protect  ← Comment this out temporarily
def api_create_news():
    ...
```

**Remember to uncomment it when done testing!**

## Why This Happens

1. **CSRF tokens are session-based** - They're generated when you load a web page
2. **Swagger UI is separate** - It doesn't share the same session/cookies as your web pages
3. **API clients need the token** - You must manually provide it

## The Correct Flow

```
Browser loads /admin/news/new
    ↓
Server generates CSRF token in session
    ↓
Token is embedded in:
  - Meta tag: <meta name="csrf-token" content="...">
  - Config div: data-csrf-token="..."
  - BASE_CONFIG: window.BASE_CONFIG.csrf_token
    ↓
JavaScript reads token when form is submitted
    ↓
Token is sent in BOTH:
  - Header: X-CSRF-Token
  - Body: csrf_token field
    ↓
Server validates: token matches session
    ↓
✅ Request succeeds!
```

## Testing Checklist

### Via News Form (Recommended)
- [ ] Navigate to `/admin/news/new`
- [ ] Check console for token initialization
- [ ] Fill in form (minimum: title)
- [ ] Click "Saqlash"
- [ ] Check console for "=== CSRF Token Debug ==="
- [ ] Verify token is sent
- [ ] Check server logs for success (no CSRF FAIL)

### Via Swagger/API Client
- [ ] Get CSRF token from browser console
- [ ] Add token to request (header or body)
- [ ] Make POST request
- [ ] Verify 200/201 response (not 403)

## Expected Server Output (Success)

When the request succeeds, you should see:
```
✓ No CSRF FAIL message
✓ News item created successfully
```

When it fails, you'll see:
```
!!! CSRF FAIL: Recv=None, Sess=...
=== CSRF DEBUG: Full Request Analysis ===
X-CSRF-Token header: None
csrf_token in JSON: None
```

## Quick Test Script

Save this as `test_news_api.py`:

```python
import requests

# 1. Get a session and CSRF token
session = requests.Session()
response = session.get('http://localhost:5000/admin/news/new')

# Extract CSRF token from response
import re
match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
if match:
    csrf_token = match.group(1)
    print(f"Got CSRF token: {csrf_token[:20]}...")
    
    # 2. Make API request with token
    data = {
        "csrf_token": csrf_token,
        "title": "Test from Script",
        "content": "This is a test",
        "is_active": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf_token
    }
    
    response = session.post(
        'http://localhost:5000/api/news',
        json=data,
        headers=headers
    )
    
    print(f"Response: {response.status_code}")
    print(f"Body: {response.json()}")
else:
    print("Could not extract CSRF token")
```

Run with: `python test_news_api.py`
