# Zoho Creator Bootstrap

This tool provisions an experimental Zoho Creator app for Amber (no changes to Next.js).

## Prereqs

- Zoho OAuth refresh token, client id/secret
- Creator owner name (typically your Zoho email or org identifier)
- Regional DC (us, eu, in, au, jp, ca)

## Environment

Set GitHub Actions secrets:
- ZOHO_CLIENT_ID
- ZOHO_CLIENT_SECRET
- ZOHO_REFRESH_TOKEN
- ZOHO_OWNER
- ZOHO_APP_NAME (default: Amber-Experimental)
- ZOHO_APP_LINK_NAME (default: amber_experimental)
- ZOHO_DC (default: us)

## Local run

```bash
export ZOHO_CLIENT_ID=...
export ZOHO_CLIENT_SECRET=...
export ZOHO_REFRESH_TOKEN=...
export ZOHO_OWNER=you@example.com
python3 tools/zoho_creator/bootstrap_creator.py --dry-run
python3 tools/zoho_creator/bootstrap_creator.py
```

## What it does

- Ensures the app exists (creates if missing)
- Upserts Leaders and Posts forms from blueprints
- Upserts a minimal Dashboard page
- Idempotent; safe to re-run
