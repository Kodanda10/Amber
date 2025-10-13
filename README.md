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
```

### Test Coverage

- Backend: 85%+ line coverage target
- Frontend: Component and hook testing with Vitest
- E2E: Playwright tests (in progress)

## 🚢 Deployment

For comprehensive production deployment instructions, see:
- **[Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)** - Complete setup including Render, Vercel, and Zoho Creator
- **[Original Deployment Notes](docs/DEPLOYMENT.md)** - Backend and frontend deployment basics

### Quick Start Production Build

```bash
# Build frontend
cd nextjs-app
npm run build

# Backend deployment (example with gunicorn)
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Key Environment Variables

```bash
# Backend (Required)
DATABASE_URL=postgresql://user:pass@host:5432/amber
ADMIN_JWT_SECRET=production_secret

# Backend (Optional Features)
TWITTER_BEARER_TOKEN=your_bearer_token
X_INGEST_ENABLED=true
FACEBOOK_GRAPH_TOKEN=production_token
FACEBOOK_GRAPH_ENABLED=1

# Frontend
NEXT_PUBLIC_API_BASE=https://your-backend-url.com
```

### Production Endpoints

Once deployed, your backend will expose:
- **Health Check:** `GET /api/health` - Service status and statistics
- **Metrics:** `GET /api/metrics` - Performance and ingestion metrics
- **Dashboard API:** `GET /api/dashboard` - Main dashboard data
- **Leaders API:** `GET /api/leaders` - Leader roster management

### Zoho Creator Integration

The repository includes automated Zoho Creator app provisioning:

1. Configure GitHub Secrets (see [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md#zoho-creator-setup))
2. Run the "Zoho Creator Bootstrap" workflow from GitHub Actions
3. Access your app at: `https://creator.zoho.com/{owner}/amber_experimental/`

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Frontend Job**: Lint, type-check, and build Next.js app
- **Backend Job**: Python tests with pytest and 80% coverage requirement
- **Security Job**: Trivy vulnerability scanning and Gitleaks secret detection
- **Zoho Bootstrap**: Manual workflow for Creator app provisioning
- **E2E Job**: Placeholder for Playwright end-to-end tests

All checks must pass before merging to main.

## 📚 Documentation

### Core Documentation
- **[Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)** - Complete production setup (Render, Vercel, Zoho Creator)
- **[Deployment Notes](docs/DEPLOYMENT.md)** - Backend and frontend deployment basics
- **[Zoho Creator Bootstrap](tools/zoho_creator/README.md)** - Zoho Creator API integration details
- **[Product Requirements Document](PRD.md)** - Detailed feature specifications
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
