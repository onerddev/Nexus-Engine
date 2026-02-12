# Deployment Guide - NexusEngine Omega

## Environment Preparation

### Prerequisites

- Ubuntu 20.04+ or CentOS 8+
- CPU: 8+ cores recommended
- RAM: 16GB+ recommended  
- Storage: 100GB+ (for database)
- Docker 20.10+ and Docker Compose 1.29+

### System Requirements

```bash
# Check prerequisites
docker --version   # Should be >= 20.10
docker-compose --version  # Should be >= 1.29
python3 --version  # Should be >= 3.11

# Install Docker (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Post-install (add user to docker group)
sudo usermod -aG docker $USER
newgrp docker
```

## Pre-Deployment Checklist

```
[ ] Read README.md
[ ] Review SECURITY.md
[ ] Plan network topology
[ ] Prepare SSL certificates
[ ] Create backup plan
[ ] Test disaster recovery
[ ] Set up monitoring
[ ] Plan rollback strategy
```

## Network Architecture

### Single Server Deployment

```
┌──────────────────────────────┐
│    NexusEngine Deployment    │
├──────────────────────────────┤
│ ┌────────────────────────┐   │
│ │   Load Balancer        │   │
│ │   (Nginx/HAProxy)      │   │
│ └──────────┬─────────────┘   │
│            │                 │
│ ┌──────────┴──────────┐      │
│ │  Docker Network     │      │
│ ├─────────┬──────────┤      │
│ │API      │Database  │      │
│ │Services │Services  │      │
│ └─────────┴──────────┘      │
└──────────────────────────────┘
```

### Multi-Server Deployment (HA)

```
┌──────────────────────────────────────────┐
│         External Load Balancer           │
└──────────────┬───────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
┌───────▼──────┐  ┌───▼─────────┐
│ API Server 1 │  │ API Server 2 │
└────────┬─────┘  └──┬──────────┘
         │            │
    ┌────▼────────────▼──┐
    │  PostgreSQL Primary │
    │  PostgreSQL Replica │
    │  Shared Storage     │
    └─────────────────────┘
```

## Docker Compose Deployment

### Basic Setup

```bash
# Clone repository
git clone https://github.com/nexusengine/nexus-omega.git
cd NexusEngine

# Review and customize environment
cp .env.example .env
nano .env

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Verify health
docker-compose ps
curl http://localhost:8000/health
```

### Environment Configuration

Create `.env` file with production values:

```env
# Engine Tuning
ENGINE_THREADS=16
ENGINE_QUEUE_CAPACITY=100000
ENGINE_BATCH_SIZE=64

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_LOG_LEVEL=INFO

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=nexus_engine
DB_USER=nexus_admin
DB_PASSWORD=generate-secure-password-here
DB_SSL_MODE=require
DB_POOL_SIZE=20

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure-password-here

# Security
ENABLE_AUTH=true
API_KEY=generate-secure-api-key-here
ALLOWED_ORIGINS=https://yourdomain.com

# Monitoring
METRICS_ENABLED=true
TRACING_ENABLED=true
LOG_LEVEL=INFO
```

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: nexus_postgres
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - nexus_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: nexus_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - nexus_network
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    container_name: nexus_api
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - nexus_network
    restart: unless-stopped
    mem_limit: 8g
    cpus: '4.0'

  prometheus:
    image: prom/prometheus:latest
    container_name: nexus_prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - nexus_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: nexus_grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - nexus_network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  nexus_network:
    driver: bridge
```

## Kubernetes Deployment (Optional)

### Install Kubernetes

```bash
# Using kubeadm (Ubuntu)
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Join worker nodes
kubeadm join <control-plane-ip>:6443 --token ... --discovery-token-ca-cert-hash ...
```

### Helm Chart Values

```yaml
# values.yaml
replicaCount: 3

image:
  repository: nexus-engine/api
  tag: "1.0.0"
  pullPolicy: IfNotPresent

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 2000m
    memory: 4Gi

service:
  type: LoadBalancer
  port: 8000

database:
  host: postgres-service
  port: 5432
  user: nexus_admin

ingress:
  enabled: true
  host: api.nexusengine.com
```

## HTTPS/TLS Setup

### Using Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d api.nexusengine.com

# Update docker-compose to use certificate
# In your nginx/load balancer config:
ssl_certificate /etc/letsencrypt/live/api.nexusengine.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.nexusengine.com/privkey.pem;
```

### Self-Signed Certificate

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -out cert.pem -keyout key.pem -days 365

# Use in docker-compose
volumes:
  - ./certs/cert.pem:/etc/ssl/certs/server.crt:ro
  - ./certs/key.pem:/etc/ssl/private/server.key:ro
```

## Load Balancer Configuration

### Nginx Configuration

```nginx
upstream nexus_backend {
    server api:8000;
    server api2:8000;
    server api3:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.nexusengine.com;

    ssl_certificate /etc/letsencrypt/live/api.nexusengine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.nexusengine.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location /health {
        access_log off;
        proxy_pass http://nexus_backend;
    }

    location / {
        proxy_pass http://nexus_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=100 nodelay;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.nexusengine.com;
    return 301 https://$server_name$request_uri;
}
```

## Database Initialization

```bash
# Initialize PostgreSQL schema
docker exec nexus_postgres psql -U ${DB_USER} -d ${DB_NAME} < sql/schema.sql

# Verify initialization
docker exec nexus_postgres psql -U ${DB_USER} -d ${DB_NAME} -c "\dt"
```

## Monitoring & Logging

### View Logs

```bash
# All containers
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Real-time filtering
docker-compose logs -f api | grep ERROR
```

### Prometheus Queries

```promql
# Request rate
rate(http_request_total[5m])

# Latency p99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_request_total{status=~"5.."}[5m])
```

### Set Up Alerts

```yaml
# prometheus.yml
rule_files:
  - '/etc/prometheus/alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

## Backup & Recovery

### Database Backup

```bash
# Daily backup
docker exec nexus_postgres pg_dump -U ${DB_USER} ${DB_NAME} > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/nexus"
mkdir -p $BACKUP_DIR
docker exec nexus_postgres pg_dump -U ${DB_USER} ${DB_NAME} | \
    gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

### Database Restore

```bash
# Restore from backup
docker exec -i nexus_postgres psql -U ${DB_USER} ${DB_NAME} < backup_20240115.sql
```

## Scaling

### Horizontal Scaling (Add API Servers)

```bash
# Start additional API instance
docker run -d --name nexus_api2 \
  -e DATABASE_URL=postgresql://... \
  -p 8001:8000 \
  nexus_api:latest

# Update load balancer config
```

### Vertical Scaling (Increase Resources)

```bash
# Update docker-compose resource limits
cpus: '8.0'  # From 4.0
mem_limit: 16g  # From 8g

# Restart service
docker-compose up -d api
```

## Performance Tuning

### PostgreSQL Optimization

```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '64GB';

-- Connection pooling
ALTER SYSTEM SET max_connections = 1000;

-- Reload config
SELECT pg_reload_conf();
```

### API Server Tuning

```env
# Increase workers
API_WORKERS=8  # From 4

# Increase queue depth
ENGINE_QUEUE_CAPACITY=500000  # From 100000

# Enable profiling
ENABLE_PROFILING=true
```

## Upgrade Path

### Rolling Update

```bash
# 1. Build new image
docker build -t nexus_api:1.0.1 -f docker/Dockerfile.api .

# 2. Run database migrations
docker-compose run --rm api alembic upgrade head

# 3. Update to new version
docker-compose up -d api

# 4. Verify health
curl http://localhost:8000/health
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs nexus_api

# Verify health
docker exec nexus_api curl http://localhost:8000/health

# Check resource usage
docker stats
```

### High Database Load

```sql
-- Find slow queries
SELECT query, mean_exec_time FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;

-- Add missing indexes
CREATE INDEX idx_metrics_time ON metrics(timestamp DESC);

-- Vacuum tables
VACUUM ANALYZE metrics;
```

### Memory Leaks

```bash
# Monitor memory growth
watch 'docker stats --no-stream nexus_api'

# Profile with valgrind
docker run --rm -it nexus_api valgrind ./app
```

## Production Checklist

```
[ ] All containers running healthily
[ ] HTTPS/TLS configured
[ ] Database backups automated
[ ] Monitoring and alerts enabled
[ ] Log aggregation configured
[ ] Network segmentation applied
[ ] Rate limiting enabled
[ ] API authentication enabled
[ ] Disaster recovery tested
[ ] Performance baseline established
[ ] Security audit completed
[ ] Documentation updated
```

---

See [README.md](../README.md) for quick start and features.
