# Pro-Obuv

Production-ready cleanup baseline for the Pro-Obuv project.

## Goals
- keep the repository clean and safe for deployment
- avoid committing secrets and local artifacts
- make server deployment easier and repeatable

## Repository rules
- keep only `.env.example` in Git
- never commit real `.env`
- do not commit `*.bak`, logs, debug dumps, sqlite runtime files, or local uploads

## Quick start

### 1. Clone
```bash
git clone https://github.com/Moxirbek236/Pro-Obuv.git
cd Pro-Obuv
```

### 2. Create environment file
```bash
cp .env.example .env
```
Fill the values in `.env` before starting the server.

### 3. Install dependencies
Use the package manager and install flow required by this project.

### 4. Run locally
Start the application with the project's normal local run command.

## Recommended production structure
- `templates/` — html templates
- `static/` — css/js/images that are part of the app
- `scripts/` — reusable operational scripts only
- `docs/` — deployment and maintenance notes
- `attached_assets/`, `uploads/`, `media/` — should stay outside Git for real environments

## Deployment
This repository now includes:
- `.env.example`
- `deploy/nginx.conf`
- `deploy/gunicorn.service`
- `docs/PRODUCTION_CHECKLIST.md`

## Security notes
- rotate any secrets that were previously exposed
- use strong secret values in production
- store secrets in server environment variables or a protected `.env`

## Recommended next cleanup
- move temporary one-off debug scripts out of the root
- keep only reusable migration/maintenance scripts
- add app-specific startup command documentation for your exact backend stack
