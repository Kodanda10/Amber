# Production Hardening: Rate Limiting & X Ingestion

This document describes the production-ready rate limiting and X (Twitter) ingestion features implemented in Amber.

## Table of Contents

- [Rate Limiting](#rate-limiting)
- [X (Twitter) Ingestion](#x-twitter-ingestion)
- [Security Headers](#security-headers)
- [Health Checks](#health-checks)
- [Running Locally](#running-locally)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Rate Limiting

### Overview

Amber implements Redis-backed token bucket rate limiting to protect against abuse and ensure fair resource usage across all API consumers.

### Features

- **Token Bucket Algorithm**: Allows bursts while maintaining average rate
- **IP-based and User-based**: Different limits for authenticated vs anonymous users
- **HTTP 429 Responses**: Proper `Retry-After` and `X-RateLimit-*` headers
- **Fail-Open Design**: Allows requests when Redis is unavailable (graceful degradation)
- **Configurable Limits**: Set via environment variables

### Configuration

Environment variables (see `.env.example`):

```bash
REDIS_URL=redis://localhost:6379/0
RATE_LIMITING_ENABLED=true
REQUESTS_PER_MINUTE=60
BURST_SIZE=60
WINDOW_SECONDS=60
```

### Rate Limited Endpoints

The following endpoints have rate limiting applied:

- `POST /api/leaders/<id>/refresh` - 1 request per IP
- `GET /api/feed` - 1 request per IP
- Additional endpoints can be rate-limited by adding the `@rate_limit()` decorator

### Response Format

When rate limited, the API returns HTTP 429 with:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 30
}
```

Headers:
- `Retry-After`: Seconds to wait before retrying
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when the limit resets

### Architecture

```
Client Request
     ↓
Rate Limiter (checks Redis)
     ↓
Allowed? ──No──→ Return 429
     ↓
    Yes
     ↓
Process Request
```

The rate limiter uses Redis to store token bucket state with atomic operations to prevent race conditions.

## X (Twitter) Ingestion

### Overview

Amber automatically ingests posts from X (Twitter) for configured leaders on a scheduled basis.

### Features

- **Scheduled Ingestion**: Configurable via cron or interval
- **Circuit Breaker**: Protects against X API failures with automatic recovery
- **Deduplication**: Prevents duplicate posts using external IDs
- **Backfill Support**: Initial fetch of historical posts
- **Rate-Aware**: Respects X API rate limits with exponential backoff

### Configuration

Environment variables:

```bash
# Enable X ingestion
X_INGEST_ENABLED=true
TWITTER_BEARER_TOKEN=your_bearer_token

# Ingestion settings
X_INGEST_LIMIT=10                    # Posts per leader per run
X_BACKFILL_COUNT=50                  # Initial backfill count
X_INGEST_INTERVAL_MINUTES=30         # Run every 30 minutes

# Or use cron syntax
X_INGEST_CRON=*/30 * * * *          # Every 30 minutes
```

### Getting X API Credentials

1. Visit [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app or use an existing one
3. Navigate to "Keys and tokens" tab
4. Generate a "Bearer Token" (API v2 access)
5. Copy the token to your `.env.local` file as `TWITTER_BEARER_TOKEN`

### Manual Ingestion

Trigger a one-time ingestion via API (requires admin auth):

```bash
curl -X POST http://localhost:5000/api/ingestion/trigger \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backfill": false}'
```

### Monitoring Ingestion

Check ingestion status:

```bash
curl http://localhost:5000/api/ingestion/status
```

Response:
```json
{
  "enabled": true,
  "running": true,
  "circuit_breaker_state": "closed",
  "circuit_breaker_failures": 0,
  "jobs": [
    {
      "id": "x_ingestion_interval",
      "name": "X Post Ingestion (Interval)",
      "next_run": "2025-10-12T22:00:00",
      "trigger": "interval[0:30:00]"
    }
  ],
  "config": {
    "backfill_count": 50,
    "interval_minutes": 30,
    "cron": null
  }
}
```

### Circuit Breaker

The circuit breaker protects against X API failures:

- **Closed (Normal)**: Requests pass through
- **Open (Failing)**: After 5 consecutive failures, stops making requests for 5 minutes
- **Half-Open (Recovery)**: After timeout, tries one request to test recovery

### Data Model

Ingested X posts are stored with:
- Unique external ID (X post ID)
- Author information (handle, name, avatar)
- Post content and timestamp
- Media URLs
- Sentiment analysis
- Link to leader

## Security Headers

### Planned Headers

The following security headers will be added:

```python
Content-Security-Policy: default-src 'self'; script-src 'self' https://platform.twitter.com
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-Frame-Options: DENY
```

### CORS Configuration

Currently allows all origins for `/api/*`. For production:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

## Health Checks

### Endpoint

```bash
GET /api/health
```

### Response Format

```json
{
  "status": "ok",
  "timestamp": "2025-10-12T21:00:00",
  "checks": {
    "database": {
      "status": "ok",
      "stats": {
        "leaders": 10,
        "posts": 150,
        "reviewItems": 5
      }
    },
    "redis": {
      "status": "ok"
    },
    "ingestion_scheduler": {
      "status": "ok",
      "enabled": true,
      "circuit_breaker_state": "closed"
    }
  },
  "stats": {
    "totalIngests": 10,
    "lastIngestMs": 250
  },
  "build": {
    "version": "0.1.0",
    "commit": "abc123",
    "buildTime": "2025-10-12T20:00:00"
  }
}
```

Status codes:
- `200 OK`: All systems operational
- `503 Service Unavailable`: Critical components (database) are down

## Running Locally

### Prerequisites

- Python 3.11+
- Redis server
- Node.js 20+
- Twitter/X API bearer token (optional)

### Setup

1. **Start Redis**:
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

   Or install locally:
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Install Backend Dependencies**:
   ```bash
   cd nextjs-app/backend
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp nextjs-app/.env.example nextjs-app/.env.local
   # Edit .env.local with your credentials
   ```

4. **Run Backend**:
   ```bash
   cd nextjs-app/backend
   python app.py
   ```

5. **Run Frontend** (separate terminal):
   ```bash
   cd nextjs-app
   npm install
   npm run dev
   ```

### Running Tests

Backend tests:
```bash
cd nextjs-app/backend
pytest tests/test_rate_limiting.py -v
pytest tests/test_health.py -v
pytest  # Run all tests
```

With coverage:
```bash
pytest --cov=. --cov-report=term --cov-fail-under=80
```

### Manual Testing

1. **Test Rate Limiting**:
   ```bash
   # Make 11 rapid requests (limit is 10)
   for i in {1..11}; do
     curl -v http://localhost:5000/api/feed
   done
   # 11th request should return 429
   ```

2. **Test X Ingestion** (requires X_INGEST_ENABLED=true):
   ```bash
   # Trigger manual ingestion
   curl -X POST http://localhost:5000/api/ingestion/trigger \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   
   # Check status
   curl http://localhost:5000/api/ingestion/status
   
   # View ingested posts
   curl http://localhost:5000/api/feed?source=x
   ```

3. **Test Health Check**:
   ```bash
   curl http://localhost:5000/api/health | jq
   ```

## Deployment

### Environment Variables

Production environment must set:

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/amber
REDIS_URL=redis://prod-redis:6379/0
ADMIN_JWT_SECRET=<strong-random-secret>

# X Ingestion (if enabled)
X_INGEST_ENABLED=true
TWITTER_BEARER_TOKEN=<production-token>

# Rate Limiting
RATE_LIMITING_ENABLED=true
REQUESTS_PER_MINUTE=60
```

### Redis Setup

For production, use a managed Redis service:

- **AWS**: ElastiCache
- **Google Cloud**: Cloud Memorystore
- **Azure**: Azure Cache for Redis
- **Heroku**: Heroku Redis
- **Render**: Redis instance

Configure `REDIS_URL` with connection string.

### Database Migrations

If you add new fields to models, create and run migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Add new fields"

# Apply migration
alembic upgrade head
```

### Monitoring

Monitor the following metrics:

1. **Rate Limiting**:
   - Rate limit hit rate (429 responses)
   - Redis connection status
   - Average request latency

2. **X Ingestion**:
   - Circuit breaker state
   - Ingestion success/failure rate
   - Posts ingested per run
   - X API errors

3. **Health**:
   - Database connection
   - Redis availability
   - Scheduler status

## Troubleshooting

### Rate Limiting Not Working

1. Check Redis connection:
   ```bash
   redis-cli ping
   # Should return PONG
   ```

2. Verify env vars:
   ```bash
   echo $RATE_LIMITING_ENABLED
   echo $REDIS_URL
   ```

3. Check logs for Redis errors:
   ```bash
   tail -f logs/app.log | grep redis
   ```

### X Ingestion Not Running

1. Check ingestion status:
   ```bash
   curl http://localhost:5000/api/ingestion/status
   ```

2. Verify X_INGEST_ENABLED is true

3. Check logs for scheduler errors:
   ```bash
   tail -f logs/app.log | grep ingestion
   ```

4. Check circuit breaker state (should be "closed" for normal operation)

### Circuit Breaker Open

If circuit breaker is open:

1. Check X API credentials are valid
2. Wait 5 minutes for automatic recovery
3. Check X API status: https://api.twitterstat.us/
4. Verify rate limits not exceeded on X side

### Redis Connection Failures

If Redis is unavailable:

- Rate limiting will fail-open (allow all requests)
- Check `REDIS_URL` configuration
- Verify Redis server is running
- Check network connectivity

### Database Errors

1. Check database connection string
2. Verify database server is running
3. Run migrations if needed
4. Check disk space

## Architecture Notes

### Data Flow

```
X API
  ↓
Circuit Breaker
  ↓
Ingestion Scheduler (APScheduler)
  ↓
ingest_x_posts()
  ↓
Database (Post table)
  ↓
GET /api/feed
  ↓
Rate Limiter (Redis)
  ↓
Next.js Frontend
  ↓
PostEmbed Component
```

### Components

- **rate_limiter.py**: Token bucket rate limiting with Redis backend
- **ingestion_scheduler.py**: APScheduler-based periodic ingestion
- **x_client.py**: X API v2 client with rate limit handling
- **app.py**: Flask application with endpoints
- **PostEmbed.tsx**: (To be implemented) Client-side X post embedding

### Rate Limiting Strategy

Token bucket algorithm chosen for:
- Allows bursts (better UX)
- Smooth average rate
- Simple to implement
- Industry standard

Alternative considered: Leaky bucket (more strict, no bursts)

### Scheduling Strategy

APScheduler chosen for:
- Python-native
- Supports cron and interval triggers
- In-process (no external dependencies)
- Easy to test and monitor

Alternative considered: Celery (more complex, requires broker)

## Runbook

### Rotating X API Tokens

1. Generate new token in [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Update `TWITTER_BEARER_TOKEN` in production environment
3. Restart application or use hot-reload if supported
4. Verify ingestion still works

### When Rate-Limited by X

If you see X API rate limit errors:

1. Check current rate limit status in X Developer Portal
2. Circuit breaker will automatically open and pause requests
3. Wait for rate limit reset (typically 15 minutes)
4. Circuit breaker will automatically close and resume
5. Consider reducing `X_INGEST_INTERVAL_MINUTES` or `X_INGEST_LIMIT`

### Backfilling Historical Posts

To backfill posts for all leaders:

```bash
curl -X POST http://localhost:5000/api/ingestion/trigger \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backfill": true}'
```

This will fetch `X_BACKFILL_COUNT` posts per leader (default 50).

### Emergency: Disable X Ingestion

```bash
# Set in environment
X_INGEST_ENABLED=false

# Or via API (if implemented)
curl -X POST http://localhost:5000/api/ingestion/stop \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Clearing Rate Limit State

To reset rate limits for an IP:

```bash
redis-cli DEL "rate_limit:ip:192.168.1.1"
```

Or flush all rate limits (use with caution):

```bash
redis-cli KEYS "rate_limit:*" | xargs redis-cli DEL
```

---

For questions or issues, see [GitHub Issues](https://github.com/Kodanda10/Amber/issues).
