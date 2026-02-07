# CSRF Token Fix for News API

## Problem
The `/api/news` POST endpoint was failing with CSRF validation errors:
```
!!! CSRF FAIL: Recv=None, Sess=e3NEarIdND8JhUzyIivKXDUyKqWilo2LSOK8N0jQRG0, Path=/api/news
ERROR: CSRF DEBUG: Received='None', Session='e3NEarIdND8JhUzyIivKXDUyKqWilo2LSOK8N0jQRG0'
```

## Root Cause
The JavaScript in `templates/admin/news_form.html` was not consistently reading and sending the CSRF token. The token was being initialized in `window.CSRF_TOKEN` but the fetch calls were using inconsistent patterns to retrieve it.

## Solution Applied

### 1. **CRITICAL FIX: Token Retrieved at Submission Time**
The main issue was that the CSRF token was being assigned to `formData.csrf_token` using a variable that might be `undefined` at the time the object was created. 

**Fixed by:**
```javascript
// Get CSRF token at submission time from all possible sources
const metaTag = document.querySelector('meta[name="csrf-token"]');
const tokenFromMeta = metaTag ? metaTag.getAttribute('content') : '';
const tokenFromWindow = window.CSRF_TOKEN || '';
const tokenFromVar = (typeof CSRF_TOKEN !== 'undefined') ? CSRF_TOKEN : '';
const tokenFromBase = (window.BASE_CONFIG && window.BASE_CONFIG.csrf_token) || '';

const csrfToken = tokenFromMeta || tokenFromWindow || tokenFromVar || tokenFromBase || '';

// Early return if no token found
if (!csrfToken) {
  console.error('CRITICAL: No CSRF token available from any source!');
  showNotification('Xatolik: CSRF token topilmadi. Sahifani yangilang.', 'error');
  return;
}

// Use the fresh token in formData
const formData = {
  csrf_token: csrfToken,  // ← Now guaranteed to have a value
  title: ...,
  ...
};
```

### 2. Multiple Token Sources with Fallbacks
Added a **meta tag** in the HTML head and updated JavaScript to check **three sources** in order of reliability:

```html
<!-- In extra_head block -->
<meta name="csrf-token" content="{{ csrf_token }}">
```

```javascript
// Token initialization with multiple fallbacks
const metaTag = document.querySelector('meta[name="csrf-token"]');
const tokenFromMeta = metaTag ? metaTag.getAttribute('content') : '';

const config = document.getElementById('news-form-config');
const tokenFromConfig = config ? config.getAttribute('data-csrf-token') : '';

const tokenFromBase = (window.BASE_CONFIG && window.BASE_CONFIG.csrf_token) || '';

// Use the first non-empty token we find
window.CSRF_TOKEN = tokenFromMeta || tokenFromConfig || tokenFromBase || '';
```

**Why this works:**
- **Meta tag** is in the `<head>` and always available when scripts run
- **Config div** provides a page-specific token
- **BASE_CONFIG** is a global fallback from base.html

### 2. Standardized CSRF Token Retrieval
Updated all fetch calls in `news_form.html` to use a consistent pattern:
```javascript
const csrfToken = window.CSRF_TOKEN || CSRF_TOKEN || '';
```

This ensures the token is read from the correct source with proper fallbacks.

### 3. Updated Functions
Fixed CSRF token handling in three key functions:

#### a. `saveNewsPage()` (line 475)
- Added CSRF token to request body (`csrf_token` field)
- Added CSRF token to request headers (`X-CSRF-Token`)
- Added console logging for debugging

#### b. `uploadMediaFile()` (line 498)
- Standardized CSRF token retrieval
- Ensured token is sent in headers for file uploads

#### c. Fallback edit fetch (line 560)
- Updated client-side news fetch to use consistent token pattern

### 3. Dual Token Submission
The CSRF token is now sent in **both** locations:
1. **Request Headers**: `X-CSRF-Token: <token>`
2. **Request Body**: `csrf_token: <token>`

This ensures compatibility with the `csrf_protect` decorator which checks both locations:
```python
# From app.py line 329-350
def csrf_protect(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            # Check token in header first, then json body, then form
            header = request.headers.get("X-CSRF-Token")
            token = (
                header
                or (request.get_json(silent=True) or {}).get("csrf_token")
                or request.form.get("csrf_token")
            )
```

## Files Modified
- `templates/admin/news_form.html`
  - Added meta tag in `extra_head` block
  - Enhanced CSRF token initialization with 3 fallback sources
  - Updated 3 fetch calls to use consistent token retrieval
  - Added debug logging

## Testing
To verify the fix:
1. Open the news form at `/admin/news/new`
2. Open browser DevTools Console
3. Fill in the form and click "Saqlash"
4. Check console for: `CSRF Token being sent: <token-value>`
5. Verify the POST request succeeds without CSRF errors

## Technical Details

### Token Initialization
The CSRF token is initialized in the template via:
```html
<div id="news-form-config"
     data-csrf-token="{{ csrf_token if csrf_token is defined else '' }}"
     ...>
</div>

<script>
  const config = document.getElementById('news-form-config');
  window.CSRF_TOKEN = config ? config.getAttribute('data-csrf-token') : '';
  var CSRF_TOKEN = window.CSRF_TOKEN;
</script>
```

### Context Processor
The `csrf_token` is injected into all templates via the context processor at `app.py:2495`:
```python
@app.context_processor
def inject_csrf_token():
    """Ensure csrf_token is available in all templates."""
    return dict(csrf_token=generate_csrf_token())
```

## Expected Behavior After Fix
- News creation/editing should work without CSRF errors
- Console will show the CSRF token being sent
- Server logs will no longer show "CSRF FAIL" messages for `/api/news`
