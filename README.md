<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Project Amber - Political Social Media Tracker

> A comprehensive platform for tracking and analyzing political leaders' social media activity with real-time sentiment analysis, multilingual support, and human-in-the-loop review capabilities.

[![CI Status](https://github.com/Kodanda10/Amber/actions/workflows/ci.yml/badge.svg)](https://github.com/Kodanda10/Amber/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Overview

Project Amber is a full-stack application designed to monitor, aggregate, and analyze social media content from political leaders. It combines automated data ingestion with AI-powered sentiment analysis and provides a human-in-the-loop review workflow for content validation.

### Key Features

- **Multi-Platform Ingestion**: Automated content fetching from Facebook, Twitter/X, and news sources
- **Real-time Sentiment Analysis**: AI-powered sentiment scoring using VADER and transformer models
- **Human Review Workflow**: Built-in content moderation and verification system
- **Multilingual Support**: Hindi localization with date formatting and language badges
- **Interactive Dashboard**: Rich data visualization with charts and leader roster management
- **Robust Testing**: Comprehensive test coverage with unit, integration, and E2E tests
- **Secure Admin Controls**: JWT-based authentication for protected endpoints
- **Twitter/X Integration**: Native Twitter API v2 client with rate limiting and pagination support

## 📋 Table of Contents

- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- Next.js 15 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- Recharts for data visualization
- Vitest for testing

**Backend:**
- Python 3.11+
- Flask with SQLAlchemy
- PyTorch & Transformers for NLP
- VADER Sentiment Analysis
- Pandas for data processing
- Pytest for testing

**Infrastructure:**
- GitHub Actions for CI/CD
- SQLite (development) / PostgreSQL (production)
- Docker support
- Vercel deployment ready

## 🚀 Getting Started

### Prerequisites

- Node.js 20+ 
- Python 3.11+
- npm or yarn
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kodanda10/Amber.git
   cd Amber/nextjs-app
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

4. **Set up environment variables**
   
   Create a `.env.local` file in the `nextjs-app` directory (see `.env.example` for all options):
   ```bash
   # Optional: Facebook Graph API Integration
   FACEBOOK_GRAPH_ENABLED=1
   FACEBOOK_GRAPH_TOKEN=your_meta_app_token
   FACEBOOK_GRAPH_LIMIT=5
   
   # Optional: Twitter/X API Integration
   # Get your bearer token from: https://developer.twitter.com/en/portal/dashboard
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   X_INGEST_ENABLED=false
   
   # Optional: Admin Authentication
   ADMIN_JWT_SECRET=your_secret_key
   ADMIN_BOOTSTRAP_SECRET=bootstrap_secret
   
   # Database (defaults to SQLite in development)
   DATABASE_URL=sqlite:///amber.db
   ```
   
   **Twitter/X API Setup:**
   - Visit [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
   - Create a new app or use an existing one
   - Navigate to "Keys and tokens" tab
   - Generate a "Bearer Token" (API v2 access)
   - Copy the token to your `.env.local` file as `TWITTER_BEARER_TOKEN`
   - Set `X_INGEST_ENABLED=true` when ready to enable X ingestion

5. **Run the development servers**
   
   Terminal 1 - Frontend:
   ```bash
   npm run dev
   ```
   
   Terminal 2 - Backend:
   ```bash
   cd backend
   python app.py
   ```

6. **Open the application**
   
   Navigate to [http://localhost:3000](http://localhost:3000)

## 💻 Development

### Project Structure

```
Amber/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── nextjs-app/            # Main application
│   ├── backend/           # Python Flask API
│   │   ├── app.py        # Main Flask application
│   │   ├── facebook_client.py  # Facebook Graph API client
│   │   ├── news_sources.py     # News aggregation
│   │   ├── sentiment.py        # Sentiment analysis
│   │   └── tests/              # Backend test suite
│   ├── src/
│   │   ├── app/          # Next.js app routes
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── lib/          # Utilities and constants
│   │   └── tests/        # Frontend test suite
│   └── public/           # Static assets
├── PRD.md                # Product Requirements Document
├── ToDoList.md          # Development roadmap
└── README.md            # This file
```

### Available Scripts

**Frontend:**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run test         # Run Vitest tests
```

**Backend:**
```bash
cd backend
python app.py                                    # Start Flask server
pytest                                           # Run all tests
pytest --cov=. --cov-report=term                # Run with coverage
ruff check .                                     # Lint Python code
ruff check . --fix                               # Auto-fix linting issues
```

## 🧪 Testing

### Running Tests

**Frontend Tests:**
```bash
npm run test                 # Run all frontend tests
npm run test -- --coverage   # Run with coverage report
```

**Backend Tests:**
```bash
cd backend
pytest -v                    # Run with verbose output
pytest -k test_auth          # Run specific test module
pytest --maxfail=1           # Stop after first failure

# Run specific test suites
pytest tests/test_checkpoint.py -v      # Checkpoint tests
pytest tests/test_http_retry_client.py -v  # Retry client tests
pytest tests/test_embed_token.py -v     # Embed token tests
```

**E2E Smoke Tests:**
```bash
# Test embed token flow (requires running backend)
./scripts/e2e_embed_smoke.sh

# With custom configuration
API_BASE_URL=http://localhost:5000 \
ADMIN_API_KEY=your-api-key \
./scripts/e2e_embed_smoke.sh
```

### Test Coverage

- Backend: 85%+ line coverage target (110+ tests)
- Frontend: Component and hook testing with Vitest
- E2E: Embed token smoke tests + Playwright tests (in progress)

## 🔒 Production Hardening

Project Amber includes production-ready features for reliable ingestion and secure embedding:

### Twitter/X Ingestion Hardening

**Retry Logic with Exponential Backoff:**
- Base delay: 500ms, exponential factor: 2.0, max delay: 60s
- Full jitter to prevent thundering herd
- Honors `Retry-After` header for rate limits
- Max 6 retries for transient errors

**Resumable Ingestion:**
- Checkpoint-based cursor persistence
- Resume from last position after interruption
- Idempotent writes with deduplication by tweet ID

**Dry-Run Mode:**
```bash
# Test ingestion without persisting
INGESTION_DRY_RUN=true python backend/app.py
```

### Secure Dashboard Embedding

**Short-Lived Signed Tokens:**
```bash
# Generate embed token (60s TTL)
curl -X POST http://localhost:5000/api/embed/token \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"dashboardId": "abc123", "allowedOrigins": ["https://trusted.com"]}'
```

**Features:**
- HMAC-signed tokens with HS256
- Default 60-second TTL (configurable)
- Origin validation
- Rate limiting (10 requests/minute per API key)
- Secure headers (CSP frame-ancestors)

### Observability

**Health Endpoint:**
```bash
curl http://localhost:5000/api/health
# Returns: status, database connectivity, stats, uptime
```

**Prometheus Metrics:**
```bash
# JSON format
curl http://localhost:5000/api/metrics

# Prometheus text format
curl -H "Accept: text/plain" http://localhost:5000/api/metrics
```

**Tracked Metrics:**
- `ingestion_processed` - Total posts processed
- `ingestion_failed` - Ingestion failures
- `ingestion_rate_limited` - Rate limit hits
- `embed_token_requested` - Token requests
- `embed_token_failed` - Token failures

### Required Environment Variables

```bash
# Production secrets (REQUIRED)
ADMIN_JWT_SECRET=your-strong-secret-key
EMBED_SIGNING_KEY=your-embed-key-min-32-chars  # Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_API_KEY=your-admin-api-key
TWITTER_BEARER_TOKEN=your-twitter-token

# Feature flags
EMBED_ENABLED=true
X_INGEST_ENABLED=true
INGESTION_DRY_RUN=false

# Embedding configuration
EMBED_ALLOWED_ORIGINS=https://example.com,https://trusted.com
EMBED_TOKEN_TTL=60
EMBED_RATE_LIMIT_REQUESTS=10

# Checkpoint storage
CHECKPOINT_DIR=./checkpoints
```

See `.env.example` for complete configuration.

## 🚢 Deployment

### Local Development

```bash
# Start backend
cd backend
python app.py

# Start frontend (separate terminal)
cd nextjs-app
npm run dev
```

### Production Build

```bash
# Build frontend
npm run build

# Backend deployment (example with gunicorn)
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Kubernetes Deployment

**Prerequisites:**
- Kubernetes cluster (1.19+)
- kubectl configured
- Container registry access

**Quick Deploy:**
```bash
# 1. Build and push image
docker build -t your-registry/amber-backend:latest backend/
docker push your-registry/amber-backend:latest

# 2. Create secrets
kubectl create secret generic amber-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=ADMIN_JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --from-literal=EMBED_SIGNING_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --from-literal=TWITTER_BEARER_TOKEN="your-token" \
  -n amber

# 3. Deploy
kubectl apply -f k8s/deployment.yaml

# 4. Check status
kubectl get pods -n amber
kubectl get svc -n amber
```

See [k8s/README.md](k8s/README.md) for detailed deployment guide including:
- AWS Secrets Manager integration
- Monitoring and alerting
- Scaling configuration
- Troubleshooting guide

### Environment Variables (Production)

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/amber
ADMIN_JWT_SECRET=production_secret_32_chars_min
EMBED_SIGNING_KEY=production_embed_key_32_chars
TWITTER_BEARER_TOKEN=production_token

# Optional
FACEBOOK_GRAPH_ENABLED=1
FACEBOOK_GRAPH_TOKEN=production_fb_token
EMBED_ENABLED=true
X_INGEST_ENABLED=true
```

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Frontend Job**: Lint, type-check, and build Next.js app
- **Backend Job**: Python tests with pytest (110+ tests) and coverage reporting
- **Security Job**: Trivy vulnerability scanning and Gitleaks secret detection
- **E2E Job**: Placeholder for Playwright end-to-end tests

All checks must pass before merging to main.

### Secrets Management

**For AWS:**
- Use AWS Secrets Manager or SSM Parameter Store
- Install External Secrets Operator for K8s integration

**For Google Cloud:**
- Use GCP Secret Manager
- Configure workload identity

**For Azure:**
- Use Azure Key Vault
- Configure managed identity

See config loader in `backend/config.py` for hooks.

### Rollback Plan

Zero-downtime rollback:
```bash
# Disable features via ConfigMap
kubectl patch configmap amber-config -n amber \
  -p '{"data":{"EMBED_ENABLED":"false","X_INGEST_ENABLED":"false"}}'

# Restart pods
kubectl rollout restart deployment amber-backend -n amber
```

## 📚 Documentation

- [Product Requirements Document](PRD.md) - Detailed feature specifications
- [Development Roadmap](ToDoList.md) - Task tracking and progress
- [API Documentation](nextjs-app/backend/README.md) - Backend API endpoints
- [Component Guide](nextjs-app/src/components/README.md) - Frontend components

## 🤝 Contributing

We follow the **Ironclad DevOps Rulebook v2.1** for all development:

1. **Test-Driven Development**: Write tests before implementation
2. **Atomic Tasks**: Break work into small, reviewable units
3. **Documentation**: Update docs with every significant change
4. **Coverage Gates**: Maintain minimum test coverage thresholds
5. **Conventional Commits**: Use semantic commit messages with task IDs

### Development Workflow

1. Create a feature branch: `feature/task-id-description`
2. Write failing tests
3. Implement minimal code to pass tests
4. Update documentation
5. Run linters and tests locally
6. Submit PR with detailed description
7. Address review feedback
8. Merge after CI passes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Next.js](https://nextjs.org) and [Flask](https://flask.palletsprojects.com)
- Sentiment analysis powered by [VADER](https://github.com/cjhutto/vaderSentiment)
- UI components styled with [Tailwind CSS](https://tailwindcss.com)
- Charts powered by [Recharts](https://recharts.org)

---

<div align="center">
Made with ❤️ by the Amber Team
</div>
