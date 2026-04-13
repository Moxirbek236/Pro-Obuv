# Production checklist

## Repository hygiene
- Never commit `.env` or real credentials.
- Keep only `.env.example` in the repository.
- Do not commit `*.bak`, `*.out`, traceback dumps, or temporary debug files.
- Keep local media/uploads outside Git, unless they are intentional sample assets.

## Before every push
- Review `git status`.
- Verify secrets are not staged.
- Remove temporary debug scripts and log outputs.
- Keep database files and local runtime files out of Git.

## Recommended folders
- `app/` or `src/` for application code
- `templates/` for HTML templates
- `static/` for static assets
- `scripts/` only for reusable operational scripts
- `docs/` for deployment and maintenance notes

## Safe examples for `.gitignore`
- `.env`
- `.env.*`
- `*.bak`
- `*.out`
- `*.db`
- `*.sqlite3`
- `attached_assets/`
- `uploads/`
- `media/`
