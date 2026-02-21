# Quick Start Guide - NexusEngine Omega

## Prerequisites (1 minute)

```bash
# Verify you have:
docker --version        # >= 20.10
docker-compose --version # >= 1.29
python3 --version       # >= 3.11
```

## 5-Minute Setup

### Step 1: Clone & Configure

```bash
# Clone
git clone Link do Projeto só copiar e colar para não ter risco!
cd NexusEngine

# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional - uses sensible defaults)
```

### Step 2: Start Services

```bash
# Start all services (PostgreSQL, Redis, API, Prometheus, Grafana)
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy
docker-compose ps

# Check API health
curl http://localhost:8000/health
```

### Step 3: Test the API

```bash
# Simple health check
curl http://localhost:8000/ping

# Start computation engine
curl -X POST http://localhost:8000/engine/start \
  -H "Content-Type: application/json" \
  -d '{"threads": 16, "queue_capacity": 100000}'

# Get engine status
curl http://localhost:8000/engine/status
```

## First Operations (2 minutes)

### Binary Operation

```bash
# XOR two numbers
curl -X POST http://localhost:8000/compute/binary \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "xor",
    "value_a": 255,
    "value_b": 127
  }' | jq
```

Output:
```json
{
  "operation": "xor",
  "result": 128,
  "execution_time_us": 1.2
}
```

### Hash Computation

```bash
# SHA256 hash
curl -X POST http://localhost:8000/compute/hash \
  -H "Content-Type: application/json" \
  -d '{
    "data": "hello world",
    "algorithm": "sha256",
    "format": "hex"
  }' | jq .hash
```

### Check Metrics

```bash
# Get real-time metrics
curl http://localhost:8000/metrics | jq '.latency_us'

# Should show: { "p50": 1.5, "p95": 8.2, "p99": 25.3 }
```

## Python CLI (2 minutes)

### Install CLI

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python python/cli/main.py --version
```

### CLI Commands

```bash
# Start engine
python python/cli/main.py start --threads 16

# Check status
python python/cli/main.py status

# Binary operations
python python/cli/main.py calc xor 101010 110011

# Matrix operations  
python python/cli/main.py matrix --size 256 --operation random

# Quantum simulation
python python/cli/main.py quantum --qubits 8 --operation superposition

# Run benchmarks
python python/cli/main.py bench --iterations 1000000

# Get metrics
python python/cli/main.py metrics --json

# Stress test
python python/cli/main.py stress --threads 32 --duration 60
```

## Dashboard Access (1 minute)

### Grafana

```bash
# Open in browser
http://localhost:3000

# Default credentials:
# Username: admin
# Password: admin (change on first login!)

# Key dashboards:
# - NexusEngine Overview
# - Performance Metrics
# - System Health
```

### Prometheus

```bash
# Metrics interface
http://localhost:9090

# Example queries:
# - engine_processed_items_total
# - engine_throughput_ops_per_sec
# - api_request_duration_seconds
```

### API Docs

```bash
# Interactive API documentation
http://localhost:8000/docs

# Try it out:
# 1. Click "engine/start" endpoint
# 2. Click "Try it out"
# 3. Click "Execute"
```

## Stopping Services

```bash
# Stop all services (keep data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Common Tasks

### Stream Logs

```bash
# All services
docker-compose logs -f

# Just API server
docker-compose logs -f api

# Just database
docker-compose logs -f postgres
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U nexus_admin -d nexus_engine

# List tables
\dt

# Query metrics
SELECT * FROM metrics LIMIT 5;
```

### Monitor Performance

```bash
# Real-time resource usage
docker stats --no-stream

# API performance
curl http://localhost:8000/metrics | jq '.throughput'
```

## Troubleshooting

### Services Won't Start?

```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build

# Restart everything
docker-compose down -v
docker-compose up -d
```

### API Not Responding?

```bash
# Check API container
docker ps | grep nexus_api

# View API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Verify health
curl -v http://localhost:8000/health
```

### Database Connection Error?

```bash
# Check PostgreSQL
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U nexus_admin -d nexus_engine -c "SELECT 1;"

# Check network
docker network ls
docker network inspect nexus_network
```

## Next Steps

1. **Read** [README.md](../README.md) - Full feature overview
2. **Explore** [API.md](docs/API.md) - Detailed endpoint reference  
3. **Optimize** [PERFORMANCE.md](docs/PERFORMANCE.md) - Tuning guide
4. **Deploy** [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production setup
5. **Secure** [SECURITY.md](docs/SECURITY.md) - Security hardening
6. **Contribute** [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide

## Performance Targets

After startup, you should see:

```
Binary Operations:    ~1M ops/sec
Matrix Multiplies:    ~500k ops/sec  
Hash Operations:      ~100k ops/sec
Full Stack Latency:   <100µs p99
```

## Architecture Overview

```
┌─────────────────────────────────┐
│   FastAPI (Port 8000)           │
│   ├─ /engine/* control          │
│   ├─ /compute/* operations      │
│   └─ /metrics/* monitoring      │
└────────────────┬────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│C++20   │  │Python  │  │Database│
│Core    │  │CLI     │  │PostgreSQL
└────────┘  └────────┘  └────────┘
```

## Support

- **Issues** - GitHub Issues
- **Discussions** - GitHub Discussions
- **Docs** - [docs/](docs/)

---

**You're all set! 🚀**

Start using NexusEngine Omega:

```bash
# API call
curl http://localhost:8000/engine/start

# CLI command
python python/cli/main.py start

# Web dashboard
http://localhost:3000
```


