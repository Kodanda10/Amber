# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Amber backend with production hardening features.

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured to access your cluster
- A container registry (Docker Hub, GCR, ECR, etc.)
- PostgreSQL database (or use SQLite for testing)

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build backend image
cd nextjs-app/backend
docker build -t your-registry/amber-backend:latest .
docker push your-registry/amber-backend:latest
```

### 2. Update Secrets

**⚠️ IMPORTANT: Never commit real secrets to Git!**

Create secrets using kubectl:

```bash
# Generate strong secrets
ADMIN_JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
EMBED_SIGNING_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ADMIN_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Create secret
kubectl create secret generic amber-secrets \
  --from-literal=DATABASE_URL="postgresql://user:pass@postgres:5432/amber" \
  --from-literal=ADMIN_JWT_SECRET="$ADMIN_JWT_SECRET" \
  --from-literal=ADMIN_BOOTSTRAP_SECRET="$ADMIN_JWT_SECRET" \
  --from-literal=ADMIN_API_KEY="$ADMIN_API_KEY" \
  --from-literal=TWITTER_BEARER_TOKEN="your-twitter-token" \
  --from-literal=X_API_BEARER="your-twitter-token" \
  --from-literal=EMBED_SIGNING_KEY="$EMBED_SIGNING_KEY" \
  --from-literal=FACEBOOK_GRAPH_TOKEN="" \
  -n amber
```

### 3. Update ConfigMap

Edit `k8s/deployment.yaml` to configure:
- Feature flags (EMBED_ENABLED, X_INGEST_ENABLED)
- Allowed origins for embedding
- Rate limits
- Ingestion limits

### 4. Deploy

```bash
# Deploy all resources
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -n amber
kubectl get svc -n amber
kubectl get ingress -n amber
```

### 5. Verify Health

```bash
# Port-forward to test locally
kubectl port-forward -n amber svc/amber-backend 5000:5000

# Check health endpoint
curl http://localhost:5000/api/health

# Check metrics
curl http://localhost:5000/api/metrics
```

## Using AWS Secrets Manager

To use AWS Secrets Manager instead of Kubernetes secrets:

1. Create secrets in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name amber/prod/twitter-token \
  --secret-string "your-twitter-bearer-token"
```

2. Install External Secrets Operator:
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
   external-secrets/external-secrets \
   -n external-secrets-system \
   --create-namespace
```

3. Create ExternalSecret resource:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: amber-secrets
  namespace: amber
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: amber-secrets
  data:
  - secretKey: TWITTER_BEARER_TOKEN
    remoteRef:
      key: amber/prod/twitter-token
```

## Resource Configuration

The deployment includes:

- **CPU Requests**: 100m (0.1 CPU cores)
- **CPU Limits**: 1000m (1 CPU core)
- **Memory Requests**: 256Mi
- **Memory Limits**: 1Gi
- **Replicas**: 2 (for high availability)

Adjust based on your workload:
- Small deployment: 1 replica, 128Mi memory
- Medium deployment: 2 replicas, 512Mi memory
- Large deployment: 3+ replicas, 1Gi+ memory

## Health Checks

### Liveness Probe
- Path: `/api/health`
- Initial Delay: 30s
- Period: 10s
- Checks if the application is running

### Readiness Probe
- Path: `/api/health`
- Initial Delay: 10s
- Period: 5s
- Checks if the application is ready to serve traffic

## Monitoring

### Prometheus Integration

Add ServiceMonitor for Prometheus:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: amber-backend
  namespace: amber
spec:
  selector:
    matchLabels:
      app: amber
      component: backend
  endpoints:
  - port: http
    path: /api/metrics
    interval: 30s
```

### Key Metrics

Monitor these metrics:
- `ingestion_processed` - Total posts processed
- `ingestion_failed` - Total ingestion failures
- `ingestion_rate_limited` - Rate limit hits
- `embed_token_requested` - Token requests
- `embed_token_failed` - Token failures

### Alerting Rules

Recommended alerts:

```yaml
groups:
- name: amber
  rules:
  - alert: HighIngestionFailureRate
    expr: rate(ingestion_failed[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High ingestion failure rate"
  
  - alert: HighRateLimitHits
    expr: rate(ingestion_rate_limited[5m]) > 0.5
    for: 5m
    annotations:
      summary: "Frequent rate limiting"
  
  - alert: HealthCheckFailing
    expr: up{job="amber-backend"} == 0
    for: 2m
    annotations:
      summary: "Health check failing"
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: amber-backend
  namespace: amber
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: amber-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Troubleshooting

### Check Pod Logs

```bash
# Get pod name
kubectl get pods -n amber

# View logs
kubectl logs -n amber amber-backend-xxxxx-yyy

# Follow logs
kubectl logs -n amber amber-backend-xxxxx-yyy -f
```

### Check Events

```bash
kubectl get events -n amber --sort-by='.lastTimestamp'
```

### Debug Pod

```bash
# Exec into pod
kubectl exec -it -n amber amber-backend-xxxxx-yyy -- /bin/sh

# Check environment
env | grep -E "(DATABASE|TWITTER|EMBED)"

# Test health locally
curl localhost:5000/api/health
```

### Common Issues

1. **Pod CrashLoopBackOff**
   - Check secrets are correctly configured
   - View logs for startup errors
   - Verify DATABASE_URL is accessible

2. **Health Check Failing**
   - Check database connectivity
   - Verify required environment variables are set
   - Review application logs

3. **Rate Limiting Too Aggressive**
   - Adjust EMBED_RATE_LIMIT_REQUESTS in ConfigMap
   - Update and restart pods

## Secrets Rotation

To rotate secrets without downtime:

```bash
# Update secret
kubectl create secret generic amber-secrets-new \
  --from-literal=EMBED_SIGNING_KEY="new-key" \
  ... \
  -n amber

# Update deployment to use new secret
kubectl patch deployment amber-backend -n amber \
  -p '{"spec":{"template":{"spec":{"volumes":[{"name":"secrets","secret":{"secretName":"amber-secrets-new"}}]}}}}'

# Rolling update will happen automatically
# Old tokens will continue to work during TTL window
```

## Security Best Practices

1. **Use namespace isolation**
2. **Enable RBAC** - Restrict access to secrets
3. **Run as non-root** - Already configured in deployment
4. **Use read-only root filesystem** when possible
5. **Enable network policies** to restrict pod-to-pod communication
6. **Scan images** for vulnerabilities
7. **Rotate secrets regularly** (quarterly recommended)
8. **Use TLS/HTTPS** for all external traffic
9. **Enable audit logging**
10. **Monitor and alert** on security metrics

## Backup and Recovery

### Backup Checkpoints

```bash
# Backup checkpoint data
kubectl exec -n amber amber-backend-xxxxx-yyy -- \
  tar czf /tmp/checkpoints.tar.gz /app/data/checkpoints

kubectl cp amber/amber-backend-xxxxx-yyy:/tmp/checkpoints.tar.gz \
  ./checkpoints-backup-$(date +%Y%m%d).tar.gz
```

### Restore Checkpoints

```bash
# Restore checkpoint data
kubectl cp ./checkpoints-backup.tar.gz \
  amber/amber-backend-xxxxx-yyy:/tmp/checkpoints.tar.gz

kubectl exec -n amber amber-backend-xxxxx-yyy -- \
  tar xzf /tmp/checkpoints.tar.gz -C /app/data/
```
