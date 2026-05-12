# Docker Deployment Guide

Complete guide for deploying the Academic Paper Analysis Tool using Docker and Docker Compose.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Steps](#deployment-steps)
5. [Health Check Verification](#health-check-verification)
6. [Troubleshooting](#troubleshooting)
7. [Log Management](#log-management)
8. [Updating Deployment](#updating-deployment)
9. [Production Considerations](#production-considerations)

---

## Quick Start

Get the application running in 3 simple steps:

```bash
# 1. Copy environment variable template
cp .env.example .env

# 2. (Optional) Edit .env to customize configuration
# vim .env  # or use your preferred editor

# 3. Start all services
docker-compose up -d

# 4. Verify health status
docker-compose ps
curl http://localhost:8000/api/health
curl http://localhost:3000
```

Expected output:
```
NAME                        COMMAND                  SERVICE             STATUS              PORTS
paper-analysis-backend      "uvicorn app.main:app…"  backend             running (healthy)   0.0.0.0:8000->8000/tcp
paper-analysis-frontend     "node server.js"         frontend            running             0.0.0.0:3000->3000/tcp
```

---

## Prerequisites

Before deploying, ensure you have the following installed:

### Required Software

- **Docker**: >= 20.10.0
  - Check version: `docker --version`
  - Install: https://docs.docker.com/get-docker/

- **Docker Compose**: >= 2.0.0
  - Check version: `docker-compose --version`
  - Included with Docker Desktop on Windows/Mac
  - Linux: https://docs.docker.com/compose/install/

### System Requirements

- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk**: 2 GB free space for Docker images
- **Network**: Internet access to pull base images and query OpenAlex API

---

## Environment Configuration

### Using Environment Files

The application supports three environment configurations:

| Environment | File | Use Case |
|-------------|------|----------|
| **Development** | `.env.development` | Local development with hot-reload |
| **Staging** | `.env.staging` | Pre-production testing |
| **Production** | `.env.production` | Production deployment |

### Configuration Steps

#### Option 1: Use Template (Recommended)

```bash
# Copy template
cp .env.example .env

# Edit values
vim .env
```

#### Option 2: Use Pre-configured Environment

```bash
# For development
cp .env.development .env

# For staging
cp .env.staging .env

# For production
cp .env.production .env
```

### Required Environment Variables

```bash
# Logging
LOG_LEVEL=info          # Options: debug, info, warning, error

# Backend
BACKEND_PORT=8000
OPENALEX_USER_AGENT=AcademicPaperAnalysis/1.0 (mailto:your@email.com)

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://backend:8000

# Node Environment
NODE_ENV=production     # Options: development, staging, production
```

**IMPORTANT**: Replace `your@email.com` with your actual email to access OpenAlex's polite pool (higher rate limits).

---

## Deployment Steps

### Production Deployment

```bash
# 1. Navigate to project root
cd /path/to/signal-paper-analysis

# 2. Set production environment
cp .env.production .env

# 3. Build images (first time or after code changes)
docker-compose build

# 4. Start services in detached mode
docker-compose up -d

# 5. Verify services are healthy
docker-compose ps

# 6. Test endpoints
curl http://localhost:8000/api/health  # Backend health
curl http://localhost:3000             # Frontend access
```

### Development Deployment with Hot-Reload

```bash
# 1. Set development environment
cp .env.development .env

# 2. Start services with development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 3. Services will auto-reload on code changes
# - Backend: Modify files in backend/app/
# - Frontend: Modify files in frontend/src/
```

### Staging Deployment

```bash
# 1. Set staging environment
cp .env.staging .env

# 2. Build and start services
docker-compose up -d --build

# 3. Run integration tests
# (Add your test commands here)
```

---

## Health Check Verification

### Backend Health Check

Docker automatically performs health checks every 10 seconds:

```bash
# View health status
docker-compose ps

# Manual health check
curl http://localhost:8000/api/health

# Expected response
{"status":"ok","version":"1.0.0"}
```

### Frontend Health Check

```bash
# Test frontend is accessible
curl http://localhost:3000

# Expected: HTML response with Next.js app
```

### Container Logs for Health Issues

```bash
# View backend health check logs
docker-compose logs backend | grep health

# View all container events
docker events --filter container=paper-analysis-backend
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Backend Container Fails Health Check

**Symptom**: `docker-compose ps` shows backend as "unhealthy"

**Causes**:
- Backend not responding on port 8000
- Health check timing out (< 10 seconds)
- Dependencies not installed

**Solutions**:

```bash
# Check backend logs
docker-compose logs backend

# Increase health check start period (in docker-compose.yml)
start_period: 30s  # Instead of 10s

# Rebuild backend image
docker-compose build backend
docker-compose up -d backend
```

#### 2. Frontend Cannot Reach Backend

**Symptom**: Frontend shows "Network error" or "Failed to fetch"

**Causes**:
- Backend not healthy
- Incorrect `NEXT_PUBLIC_API_URL`
- Network configuration issue

**Solutions**:

```bash
# Verify backend is healthy
docker-compose ps

# Check frontend environment variables
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL
# Should show: NEXT_PUBLIC_API_URL=http://backend:8000

# Test connectivity from frontend container
docker-compose exec frontend curl http://backend:8000/api/health

# Restart frontend
docker-compose restart frontend
```

#### 3. Port Already in Use

**Symptom**: `Error: bind: address already in use`

**Solutions**:

```bash
# Option 1: Stop conflicting service
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>

# Option 2: Change port in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

#### 4. Environment Variables Not Loaded

**Symptom**: Service fails to start with "Missing environment variable" error

**Solutions**:

```bash
# Ensure .env file exists
ls -la .env

# Verify .env format (no quotes around values)
cat .env

# Recreate containers to load new environment
docker-compose down
docker-compose up -d
```

#### 5. Docker Daemon Not Running

**Symptom**: `Cannot connect to Docker daemon`

**Solutions**:

```bash
# Start Docker Desktop (Windows/Mac)
# Or start Docker service (Linux)
sudo systemctl start docker

# Verify Docker is running
docker info
```

---

## Log Management

### Viewing Logs

```bash
# View all service logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# View last 50 lines
docker-compose logs --tail=50 backend

# View logs with timestamps
docker-compose logs -t backend
```

### Log Format

#### Development Mode (Human-Readable)

```
2025-12-28 10:30:45 - app.main - INFO - Application starting
2025-12-28 10:30:46 - app.api.routes - INFO - Search request: query='machine learning', limit=50
```

#### Production Mode (JSON)

```json
{"timestamp":"2025-12-28T10:30:45.123Z","level":"INFO","message":"Application starting","module":"main","function":"setup_app","line":15}
{"timestamp":"2025-12-28T10:30:46.456Z","level":"INFO","message":"Search request: query='machine learning', limit=50","module":"routes","function":"search_papers","line":154}
```

### Exporting Logs

```bash
# Export logs to file
docker-compose logs > app_logs.txt

# Export logs for specific timeframe
docker-compose logs --since 1h > last_hour.log
docker-compose logs --since 2025-12-28T10:00:00 > today.log

# Compress logs
docker-compose logs | gzip > logs_$(date +%Y%m%d).gz
```

---

## Updating Deployment

### Update Application Code

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild images
docker-compose build

# 3. Restart services (zero-downtime with rolling restart)
docker-compose up -d --build
```

### Update Dependencies

```bash
# Backend dependencies (requirements.txt changed)
docker-compose build backend
docker-compose up -d backend

# Frontend dependencies (package.json changed)
docker-compose build frontend
docker-compose up -d frontend
```

### Update Environment Variables

```bash
# 1. Edit .env file
vim .env

# 2. Recreate containers to apply changes
docker-compose down
docker-compose up -d
```

---

## Production Considerations

### Resource Limits

Current configuration (defined in `docker-compose.yml`):

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| Backend | 1.0 cores | 512 MB | 0.5 cores | 256 MB |
| Frontend | 0.5 cores | 256 MB | 0.25 cores | 128 MB |

### Monitoring Resource Usage

```bash
# Real-time resource monitoring
docker stats

# Expected output:
# CONTAINER          CPU %    MEM USAGE / LIMIT   NET I/O
# backend            2.5%     180MB / 512MB       1.2kB / 850B
# frontend           0.8%     95MB / 256MB        3.4kB / 2.1kB
```

### Scaling

For high traffic, consider:

```bash
# Run multiple backend instances
docker-compose up -d --scale backend=3

# Add load balancer (nginx/traefik)
# Update docker-compose.yml with reverse proxy configuration
```

### Security Best Practices

1. **Non-root containers**: Both backend and frontend run as non-root users (`appuser:1000`, `nextjs:1001`)

2. **Environment secrets**: Never commit `.env` files to version control

3. **Network isolation**: Services communicate via internal bridge network

4. **Health checks**: Automated health monitoring prevents unhealthy containers from serving traffic

5. **Update base images**: Regularly rebuild images to get security patches

```bash
# Pull latest base images
docker-compose pull

# Rebuild with latest bases
docker-compose build --no-cache
```

### Backup and Recovery

```bash
# Backup configuration
tar -czf backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml

# Stop services gracefully
docker-compose down

# Restore from backup
tar -xzf backup_20251228.tar.gz

# Restart services
docker-compose up -d
```

---

## Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose Documentation**: https://docs.docker.com/compose/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Next.js Production Deployment**: https://nextjs.org/docs/deployment
- **OpenAlex API**: https://docs.openalex.org/

---

**Last Updated**: 2025-12-28
**Document Version**: 1.0
**Maintainer**: Backend Development Team
