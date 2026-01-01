# CSRF Token Debugging Guide

## Current Status
✓ CSRF token generation is working correctly (verified by test_csrf_token.py)
✗ CSRF token is still being received as `None` in POST requests to `/api/news`

## What We've Fixed

### 1. Added Multiple Token Sources
The news form now retrieves the CSRF token from **three sources** (in order of priority):

1. **Meta tag** (most reliable):
   ```html
   <meta name="csrf-token" content="{{ csrf_token }}">
   ```

2. **Config div**:
   ```html
   <div id="news-form-config" data-csrf-token="{{ csrf_token }}">
   ```

3. **BASE_CONFIG** (global fallback):
   ```javascript
   window.BASE_CONFIG.csrf_token
   ```

### 2. Enhanced Debugging
Added console logging to help diagnose the issue:
- Logs which source the token was loaded from
- Logs the actual token value
- Warns if the token is empty

### 3. Dual Token Submission
The token is sent in **both**:
- HTTP Header: `X-CSRF-Token`
- Request Body: `csrf_token` field

## Next Steps to Debug

### Step 1: Check Browser Console
Open the news form at `/admin/news/new` and check the console for:

```
CSRF Token initialized from: meta-tag
Token value: <some-long-string>
```

**If you see "WARNING: CSRF Token is empty!":**
- The template is not receiving the `csrf_token` variable
- Check if you're logged in as super_admin
- Check server logs for template rendering errors

### Step 2: Check Network Request
When you click "Saqlash", open DevTools > Network tab and check the POST request to `/api/news`:

**Headers tab - look for:**
```
X-CSRF-Token: <token-value>
```

**Payload tab - look for:**
```json
{
  "csrf_token": "<token-value>",
  "title": "...",
  ...
}
```

**If the token is missing from the request:**
- The JavaScript isn't reading the token correctly
- Check console for the "CSRF Token being sent" log

### Step 3: Check Session Cookie
The error shows different session IDs between requests:
- First error: `Sess=e3NEarIdND8JhUzyIivKXDUyKqWilo2LSOK8N0jQRG0`
- Second error: `Sess=OhZI3ftPw3SROoAqObbQQ6wJ63uvkcaZyhhidL9FcDM`

**This suggests:**
1. The session cookie is being regenerated between page load and POST
2. The CSRF token was generated in one session but validated in another

**To check:**
1. Open DevTools > Application > Cookies
2. Look for the `session` cookie
3. Note its value when the page loads
4. Check if it changes when you submit the form

**Possible causes:**
- Browser is blocking cookies (check for SameSite issues)
- Session is expiring too quickly
- Multiple tabs/windows with different sessions
- Incognito mode or privacy settings

### Step 4: Verify Template Rendering
Check that the template is actually receiving the `csrf_token`:

1. View page source (Ctrl+U)
2. Search for `csrf-token`
3. Verify the meta tag has a value:
   ```html
   <meta name="csrf-token" content="<SHOULD-BE-A-LONG-STRING>">
   ```

**If the content is empty:**
- The context processor isn't running
- Check app.py line 2495-2498

## Common Issues and Solutions

### Issue 1: Empty Token in Meta Tag
**Symptom:** `<meta name="csrf-token" content="">`

**Solution:**
- Verify you're logged in as super_admin
- Check that `inject_csrf_token()` context processor is registered
- Restart the Flask app

### Issue 2: Token Present but Still Failing
**Symptom:** Token is in the request but server says it's `None`

**Solution:**
- Check if the session cookie is being sent with the request
- Verify `credentials: 'same-origin'` is in the fetch options
- Check for CORS issues if using a different domain

### Issue 3: Session Mismatch
**Symptom:** Different session IDs in error messages

**Solution:**
- Clear all cookies for the site
- Close all tabs and open a fresh session
- Check browser cookie settings (allow cookies for localhost)
- Disable browser extensions that might interfere with cookies

## Testing Checklist

- [ ] Open `/admin/news/new` in browser
- [ ] Check console for "CSRF Token initialized from: meta-tag"
- [ ] Check console for token value (should be ~43 characters)
- [ ] View page source and verify meta tag has content
- [ ] Check Application > Cookies > session cookie exists
- [ ] Fill in form and click "Saqlash"
- [ ] Check console for "CSRF Token being sent: <token>"
- [ ] Check Network tab for POST request
- [ ] Verify X-CSRF-Token header is present
- [ ] Verify csrf_token is in request body
- [ ] Check that session cookie is sent with request
- [ ] Verify no CSRF errors in server logs

## Files to Check

1. `templates/admin/news_form.html` - Form template with token sources
2. `app.py` line 2495-2498 - Context processor that injects token
3. `app.py` line 329-350 - CSRF protection decorator
4. `app.py` line 21689-21725 - `/api/news` POST handler

## Server-Side Debugging

Add this to `app.py` line 343 (in csrf_protect decorator):

```python
print(f"!!! CSRF DEBUG: Headers={dict(request.headers)}")
print(f"!!! CSRF DEBUG: JSON={request.get_json(silent=True)}")
print(f"!!! CSRF DEBUG: Form={dict(request.form)}")
```

This will show exactly what the server is receiving.
