Superadmin fields and where they are stored

This project stores super-admin configuration and profile data in the file `superadmin_settings.json` (project root).

Canonical fields supported by the application and how they are used:

- username: string — login username for super admin
- password: string — plaintext password stored here (used by app; if you change it, use the UI or reset flow)
- first_name: string — display first name
- last_name: string — display last name
- phone: string — phone number used by "forgot password" SMS flow
- email: string — contact email for super admin
- address: string — physical address or business address for display
- card_last4: string — only last 4 digits of a card are stored (for display); full card number is never stored
- avatar: string — URL path to avatar image (e.g. "/static/uploads/superadmin_xxx.png")

Example `superadmin_settings.json`:

{
"username": "admin",
"password": "changeme",
"first_name": "John",
"last_name": "Doe",
"phone": "+998901234567",
"email": "admin@example.com",
"address": "Toshkent, Amir Temur ko'chasi 1",
"card_last4": "1234",
"avatar": "/static/images/default-avatar.svg"
}

How to update values

- Web UI (recommended): Log in as super admin at `/super-admin-master-login-z9x4m`, open Super Admin → Profile, edit fields and save.
- Manual edit: Edit `superadmin_settings.json` directly and restart the app if necessary. Be careful with password values.

Security note

- The code intentionally stores only last 4 digits of any card number. Do not store full card numbers in this file.
- Passwords are stored in this JSON file for convenience in this app; for production you should use hashed passwords and secure storage.

If you want, I can:

- Add extra fields (company, VAT id, alternate phone) to the form and backend.
- Add server-side validation for phone/email formats and sanitize address input.
- Add a small unit test that reads/writes `superadmin_settings.json` to check persistence.
