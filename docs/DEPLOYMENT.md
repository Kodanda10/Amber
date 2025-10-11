# Deployment (Vercel frontend + Render backend)

This document shows a minimal, repeatable way to deploy the Next.js frontend to Vercel and the Flask backend to Render (or a similar host). It also includes recommended environment variables and sample curl calls for testing real Twitter/X ingestion.

## 1) Frontend → Vercel

1. Connect repository to Vercel:
   - In Vercel, import project from GitHub.
   - Set Root Directory to `nextjs-app` (Project Settings → General → Root Directory).

2. Build & Install:
   - Vercel will run `npm install` and `npm run build` automatically.

3. Environment variables (Preview and Production):
   - Add any env vars used by the frontend. Commonly:
     - NEXT_PUBLIC_API_BASE=https://api.your-backend.com
     - NEXT_PUBLIC_FEATURE_FLAG_TWITTER=true  (if front-end expects client-side flag)
   - Note: Bearer tokens should remain server-side (backend). Do not set TWITTER_BEARER_TOKEN in Vercel unless strictly needed and safe.

4. Preview deployments:
   - Vercel creates a preview deployment per PR. Use the preview URL to validate UI changes before merging.

## 2) Backend → Render (recommended) or Railway/Heroku

1. Create a Web Service on Render:
   - Connect to GitHub repo and select `nextjs-app/backend` (or repo root depending on your structure).
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 4 -b 0.0.0.0:5000 app:app` (or `python app.py` for dev)

2. Environment variables (Render service → Environment):
   - DATABASE_URL=postgresql://user:pass@host:5432/amber
   - ADMIN_JWT_SECRET=production_secret
   - TWITTER_BEARER_TOKEN=your_bearer_token_here
   - TWITTER_ENABLED=1
   - X_INGEST_ENABLED=true
   - FACEBOOK_GRAPH_TOKEN=...
   - (Add SENTRY_DSN or other secrets as needed)

3. Ensure the backend URL is reachable by the frontend:
   - Add NEXT_PUBLIC_API_BASE or frontend config in Vercel to point to Render service URL.

## 3) Sample curl calls (local / staging / production)

- Trigger a leader refresh (replace host, port, and leader_id):
  - Local dev (backend running on 5000):
    - curl -X POST http://localhost:5000/api/leaders/{leader_id}/refresh -H "Content-Type: application/json"
  - Staging/Production:
    - curl -X POST https://api.your-backend.com/api/leaders/{leader_id}/refresh \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer <ADMIN_JWT_TOKEN-if-required>"

- Check health endpoint (example):
  - curl https://api.your-backend.com/api/health

- Fetch posts for a leader:
  - curl https://api.your-backend.com/api/leaders/{leader_id}/posts

## 4) Testing & rollout advice

- Start with a single leader and `X_INGEST_LIMIT=5` to observe rate usage.
- Keep ingestion feature-flag disabled in production until you've validated logs, rate handling, and DB persistence.
- Monitor logs and set up alerts for 429 rate-limit responses or repeated errors.