Staff subdomain setup (staff.safety.uz)

1) DNS
- Create an A or CNAME record for `staff` pointing to your server IP (or the host used for `safety.uz`).

2) Webserver (nginx) example

# Basic nginx server blocks — adjust paths and upstream as needed
server {
    listen 80;
    server_name staff.safety.uz;

    # Redirect HTTP -> HTTPS (optional)
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name staff.safety.uz;

    ssl_certificate /etc/letsencrypt/live/safety.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/safety.uz/privkey.pem;

    # Proxy to your WSGI server (gunicorn/uwsgi) or to the same backend as safety.uz
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000; # adjust to your upstream
    }
}

3) Flask notes
- This repository already uses `/staff` routes (e.g., `/staff/dashboard`).
- The code has a small before_request redirect that maps requests arriving at `staff.<domain>` to the existing `/staff...` paths, so no route renaming is required.
- If you prefer subdomain-aware URL generation, set `app.config['SERVER_NAME'] = 'safety.uz'` and register staff routes with `subdomain='staff'`, or use Blueprints with `subdomain` parameter.

4) Testing
- After DNS and nginx are configured, visit https://staff.safety.uz/ — you should be redirected to staff routes (e.g., `/staff/dashboard`).
- Ensure cookies/session settings work across subdomain if you need shared session (configure cookie `domain` in Flask session cookie settings).

5) Security
- Protect staff subdomain with HTTPS and consider IP allow-listing or an additional login gate if needed.
