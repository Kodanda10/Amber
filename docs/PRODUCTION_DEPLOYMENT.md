# Production Deployment Guide

This guide provides complete instructions for deploying Amber to production and setting up the Zoho Creator integration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Zoho Creator Setup](#zoho-creator-setup)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & Services
- GitHub repository access with Actions enabled
- Backend hosting (Render, Railway, or Heroku recommended)
- Frontend hosting (Vercel recommended)
- PostgreSQL database (production)
- Zoho Creator account with API access
- Twitter/X Developer account (optional, for live data)
- Meta Developer account (optional, for Facebook data)

### Required Tools
- Python 3.11+
- Node.js 20+
- Git
- GitHub CLI (optional)

---

## Environment Configuration

### Backend Environment Variables

**Required for Production:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/amber

# Authentication
ADMIN_JWT_SECRET=<generate-strong-secret>
ADMIN_JWT_TTL=3600
ADMIN_BOOTSTRAP_SECRET=<generate-strong-secret>
```

**Optional Features:**
```bash
# Twitter/X Integration
TWITTER_BEARER_TOKEN=<twitter_bearer_token>
TWITTER_ENABLED=1
X_INGEST_ENABLED=true
X_INGEST_LIMIT=10

# Facebook Integration
FACEBOOK_GRAPH_TOKEN=<meta_app_token>
FACEBOOK_GRAPH_ENABLED=1
FACEBOOK_GRAPH_LIMIT=5

# News Aggregation
NEWS_POST_LIMIT=6
```

**How to Generate Secrets:**
```bash
# Generate strong secrets for JWT
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**How to Get Twitter API Credentials:**
1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app or select existing one
3. Navigate to "Keys and tokens"
4. Generate a "Bearer Token" under "Authentication Tokens"
5. Copy the bearer token and set as `TWITTER_BEARER_TOKEN`

### Frontend Environment Variables

**Required for Production:**
```bash
# API Configuration
NEXT_PUBLIC_API_BASE=https://your-backend-domain.com

# Optional Feature Flags
NEXT_PUBLIC_FEATURE_FLAG_TWITTER=true
```

---

## Backend Deployment

### Option 1: Render (Recommended)

1. **Create Web Service:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

2. **Configure Service:**
   - **Name:** amber-backend
   - **Region:** Choose closest to your users
   - **Branch:** main
   - **Root Directory:** nextjs-app/backend
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:5000 app:app`

3. **Set Environment Variables:**
   - Navigate to "Environment" tab
   - Add all required backend environment variables (see above)

4. **Create PostgreSQL Database:**
   - In Render, click "New" → "PostgreSQL"
   - Copy the "Internal Database URL"
   - Set as `DATABASE_URL` in your web service

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note the service URL (e.g., `https://amber-backend.onrender.com`)

### Option 2: Railway

1. **Create New Project:**
   - Go to [Railway](https://railway.app/)
   - Click "New Project"
   - Select "Deploy from GitHub repo"

2. **Configure:**
   - Add PostgreSQL database service
   - Configure environment variables
   - Set start command: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`

### Option 3: Manual Deployment

```bash
# On your production server
cd /opt/amber
git clone https://github.com/Kodanda10/Amber.git
cd Amber/nextjs-app/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export ADMIN_JWT_SECRET="..."

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or with systemd service (recommended)
sudo systemctl start amber-backend
```

---

## Frontend Deployment

### Vercel (Recommended)

1. **Import Project:**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New" → "Project"
   - Import your GitHub repository

2. **Configure:**
   - **Framework Preset:** Next.js
   - **Root Directory:** nextjs-app
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)
   - **Install Command:** `npm ci` (default)

3. **Environment Variables:**
   - Add environment variables in Vercel project settings
   - Set `NEXT_PUBLIC_API_BASE` to your backend URL
   - Add any other frontend environment variables

4. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Visit your production URL

### Alternative: Static Export

```bash
cd nextjs-app
npm run build
npm run export  # If static export is configured

# Deploy the 'out' directory to any static hosting
```

---

## Zoho Creator Setup

### Step 1: Obtain Zoho API Credentials

1. **Create Zoho Creator Account:**
   - Go to [Zoho Creator](https://www.zoho.com/creator/)
   - Sign up or log in

2. **Get OAuth Credentials:**
   - Go to [Zoho API Console](https://api-console.zoho.com/)
   - Click "Add Client"
   - Select "Server-based Applications"
   - Fill in client details:
     - **Client Name:** Amber Bootstrap
     - **Homepage URL:** https://github.com/Kodanda10/Amber
     - **Authorized Redirect URI:** https://www.zoho.com/creator/
   - Note down **Client ID** and **Client Secret**

3. **Generate Refresh Token:**
   ```bash
   # Step 1: Get authorization code
   # Open this URL in browser (replace CLIENT_ID and DC):
   https://accounts.zoho.{DC}/oauth/v2/auth?scope=ZohoCreator.form.ALL,ZohoCreator.page.ALL&client_id={CLIENT_ID}&response_type=code&access_type=offline&redirect_uri=https://www.zoho.com/creator/

   # Step 2: Exchange code for refresh token
   curl -X POST "https://accounts.zoho.{DC}/oauth/v2/token" \
     -d "code={AUTHORIZATION_CODE}" \
     -d "client_id={CLIENT_ID}" \
     -d "client_secret={CLIENT_SECRET}" \
     -d "redirect_uri=https://www.zoho.com/creator/" \
     -d "grant_type=authorization_code"

   # Save the refresh_token from the response
   ```

   Replace `{DC}` with your data center domain:
   - US: `com`
   - EU: `eu`
   - IN: `in`
   - AU: `com.au`
   - JP: `jp`
   - CA: `com.ca`

### Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret" and add:

   - `ZOHO_CLIENT_ID`: Your Zoho OAuth Client ID
   - `ZOHO_CLIENT_SECRET`: Your Zoho OAuth Client Secret
   - `ZOHO_REFRESH_TOKEN`: Your Zoho refresh token
   - `ZOHO_OWNER`: Your Zoho Creator owner identifier (usually your email)
   - `ZOHO_APP_NAME`: "Amber-Experimental" (or custom name)
   - `ZOHO_APP_LINK_NAME`: "amber_experimental" (or custom link name)
   - `ZOHO_DC`: Your data center ("us", "eu", "in", "au", "jp", or "ca")

### Step 3: Run Bootstrap Workflow

1. **Dry Run (Recommended First):**
   - Go to Actions → "Zoho Creator Bootstrap"
   - Click "Run workflow"
   - Select branch: `main`
   - Set dry_run: `true`
   - Click "Run workflow"
   - Check logs to verify configuration

2. **Actual Bootstrap:**
   - Go to Actions → "Zoho Creator Bootstrap"
   - Click "Run workflow"
   - Select branch: `main`
   - Set dry_run: `false`
   - Click "Run workflow"
   - Wait for completion

3. **Verify App Creation:**
   - The workflow output will show the Zoho Creator app URL
   - Visit: `https://creator.zoho.{DC}/{owner}/amber_experimental/`
   - Verify the following were created:
     - Leaders form
     - Posts form
     - Dashboard page

### Step 4: Local Testing (Optional)

```bash
# Set environment variables
export ZOHO_CLIENT_ID="your_client_id"
export ZOHO_CLIENT_SECRET="your_client_secret"
export ZOHO_REFRESH_TOKEN="your_refresh_token"
export ZOHO_OWNER="your_email@example.com"
export ZOHO_DC="us"

# Dry run
python3 tools/zoho_creator/bootstrap_creator.py --dry-run

# Actual run
python3 tools/zoho_creator/bootstrap_creator.py
```

---

## Health Checks & Monitoring

### Health Check Endpoint

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-13T17:30:00.123456",
  "stats": {
    "leaders": 10,
    "posts": 150,
    "reviewItems": 5,
    "latestPostTimestamp": "2025-10-13T17:00:00",
    "totalIngests": 50,
    "lastIngestMs": 1234
  },
  "build": {
    "version": "1.0.0",
    "commit": "abc123"
  }
}
```

### Metrics Endpoint

**Endpoint:** `GET /api/metrics`

**Response:**
```json
{
  "ingest": {
    "totalIngests": 50,
    "lastIngestMs": 1234,
    "lastError": null
  },
  "uptimeSeconds": 86400
}
```

### Monitoring Setup

**Render:**
- Enable "Auto-Deploy" for automatic deployments on push
- Set up "Alerts" for service health
- Use built-in metrics dashboard

**External Monitoring:**
```bash
# Uptime monitoring
curl https://your-backend-url.com/api/health

# Metrics monitoring (can be integrated with Prometheus)
curl https://your-backend-url.com/api/metrics
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

The repository includes automated CI/CD:

**1. Main CI Pipeline** (`.github/workflows/ci.yml`)
- Frontend: Lint, type-check, build, tests
- Backend: Lint (ruff), tests with 80% coverage
- Security: Trivy vulnerability scan, Gitleaks secret detection
- E2E: Placeholder for future Playwright tests

**2. Zoho Bootstrap** (`.github/workflows/zoho-bootstrap.yml`)
- Manual trigger (workflow_dispatch)
- Provisions Zoho Creator app
- Supports dry-run mode

### Running CI Locally

**Frontend:**
```bash
cd nextjs-app
npm ci
npm run lint
npx tsc --noEmit
npm run test
npm run build
```

**Backend:**
```bash
cd nextjs-app/backend
pip install -r requirements.txt
ruff check .
pytest -q --maxfail=1 --disable-warnings --cov=. --cov-fail-under=80
```

---

## Troubleshooting

### Backend Issues

**Database Connection Errors:**
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:5432/dbname

# Test connection
python3 -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.connect()"
```

**Twitter API Errors:**
```bash
# Test bearer token
curl -H "Authorization: Bearer $TWITTER_BEARER_TOKEN" \
  https://api.twitter.com/2/tweets/search/recent?query=test

# Check rate limits
curl -H "Authorization: Bearer $TWITTER_BEARER_TOKEN" \
  https://api.twitter.com/2/tweets/rate_limit_status
```

### Frontend Issues

**API Connection:**
- Verify `NEXT_PUBLIC_API_BASE` is set correctly
- Check CORS is enabled on backend
- Test backend health endpoint: `curl https://backend-url/api/health`

### Zoho Creator Issues

**Authentication Errors:**
- Verify refresh token hasn't expired
- Check client ID and secret are correct
- Ensure correct data center is specified

**Bootstrap Failures:**
- Run with `--dry-run` to test configuration
- Check GitHub Actions logs for detailed error messages
- Verify owner identifier matches your Zoho account

---

## Production Checklist

Before going live:

- [ ] All CI checks passing
- [ ] Backend deployed with PostgreSQL
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] Zoho Creator app provisioned
- [ ] Health check endpoint responding
- [ ] Metrics endpoint responding
- [ ] Twitter integration tested (if enabled)
- [ ] Admin authentication working
- [ ] Database backups configured
- [ ] Monitoring and alerts set up
- [ ] Documentation updated with production URLs

---

## Support & Resources

- **Repository:** https://github.com/Kodanda10/Amber
- **Issues:** https://github.com/Kodanda10/Amber/issues
- **Documentation:** 
  - [README.md](../README.md)
  - [DEPLOYMENT.md](./DEPLOYMENT.md)
  - [Zoho Creator README](../tools/zoho_creator/README.md)
- **External APIs:**
  - [Twitter API Docs](https://developer.twitter.com/en/docs)
  - [Zoho Creator API](https://www.zoho.com/creator/help/api/)
  - [Render Docs](https://render.com/docs)
  - [Vercel Docs](https://vercel.com/docs)
