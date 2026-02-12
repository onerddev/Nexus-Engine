# Performance Tuning Guide - NexusEngine Omega

## Operating System Tuning

### Linux Kernel Parameters

```bash
# Increase network buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"

# Increase connection queue
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Increase file descriptors
ulimit -n 1000000
echo "* soft nofile 1000000" >> /etc/security/limits.conf
echo "* hard nofile 1000000" >> /etc/security/limits.conf

# CPU governor
echo "performance" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable C-states for latency
echo "1" > /sys/module/intel_idle/parameters/max_cstate
```

### NUMA Configuration

```bash
# Bind process to NUMA node
numactl --cpubind=0 --membind=0 ./nexus_engine

# Check NUMA topology
numastat
```

## C++ Optimization Flags

```cmake
# CMakeLists.txt
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -flto -fno-semantic-interposition")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -ffast-math -funroll-loops")

# For specific CPU architectures
# AMD EPYC: -march=znver3
# Intel Xeon: -march=skylake-avx512
# ARM: -march=armv8-a+sve
```

## Thread Pool Tuning

```cpp
// Optimal thread count
uint32_t optimal_threads = std::thread::hardware_concurrency();

// For NUMA systems
uint32_t threads_per_numa = optimal_threads / numa_nodes;

// Lock-free queue tuning
constexpr uint32_t QUEUE_CAPACITY = 1 << 20;  // 1M entries
constexpr uint32_t BATCH_SIZE = 64;            // Prefetch-friendly
```

## Memory Optimization

### Pre-allocation Strategy

```cpp
// Reserve upfront
std::vector<Task> tasks;
tasks.reserve(QUEUE_CAPACITY);

// Use memory pool
MemoryPool pool(sizeof(DataBlock), 1000000);
void* block = pool.allocate();  // O(1) constant time
```

### Cache-line Alignment

```cpp
struct alignas(64) CacheLinePadded {  // Intel: 64 bytes
    std::atomic<uint64_t> value;
    uint8_t padding[56];
};
```

### NUMA-Aware Allocation

```cpp
// Bind memory to NUMA node
void* addr = numa_alloc_onnode(size, numa_node);

// First-touch policy
// Write to pages in parallel on NUMA node
#pragma omp parallel for
for (int i = 0; i < size; i++) {
    memory[i] = 0;
}
```

## Latency Optimization

### Reduce GIL Contention

```python
# Cython: Release GIL
cdef extern from "...":
    # Computations release GIL
    with nogil:
        c_engine.start()
```

### Batch Processing

```cpp
// Process in batches for cache efficiency
constexpr size_t BATCH_SIZE = 4096;
for (size_t i = 0; i < total; i += BATCH_SIZE) {
    process_batch(&data[i], BATCH_SIZE);
}
```

### Minimize Allocations

```cpp
// Avoid allocations in hot path
thread_local std::vector<Result> results;
results.clear();  // Reuse
process(results);  // Fill
```

## Database Optimization

### PostgreSQL Tuning

```sql
-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '64GB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '1GB';

-- Parallel query
ALTER SYSTEM SET max_parallel_workers_per_gather = 8;
ALTER SYSTEM SET max_parallel_workers = 16;

-- Maintenance work memory
ALTER SYSTEM SET maintenance_work_mem = '4GB';

-- WAL settings for throughput
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET max_wal_size = '4GB';

-- Apply changes
SELECT pg_reload_conf();
```

### Connection Pooling

```python
# PgBouncer config
[databases]
nexus_engine = host=localhost port=5432 dbname=nexus_engine

[pgbouncer]
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
```

### Index Strategy

```sql
-- Time-series optimizations
CREATE INDEX CONCURRENTLY idx_metrics_time 
    ON metrics (timestamp DESC) WHERE timestamp > now() - interval '7 days';

-- Partial indexes
CREATE INDEX idx_active_ops 
    ON operations_log (operation_type) 
    WHERE status = 'ACTIVE';

-- Composite indexes
CREATE INDEX idx_metrics_composite 
    ON metrics (metric_name, timestamp DESC);

-- BRIN for time-series
CREATE INDEX idx_metrics_brin 
    ON metrics USING BRIN (timestamp);
```

## API Optimization

### Response Caching

```python
from functools import lru_cache
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

@app.get("/metrics")
@cache_response(ttl=5)
async def get_metrics():
    return compute_metrics()
```

### Async Processing

```python
@app.post("/compute/matrix")
async def compute_matrix(request: MatrixRequest, 
                        background_tasks: BackgroundTasks):
    # Return immediately
    background_tasks.add_task(heavy_computation, request)
    return {"status": "processing"}
```

### Connection Pooling

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    echo_pool=False
)
```

## Rate Limiting Strategy

```python
# Token bucket algorithm
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Global limit
@app.post("/compute/binary")
@limiter.limit("1000/minute")
async def binary_op(request):
    pass

# Custom limits per endpoint
limiter.limit("100/minute")(heavy_endpoint)
```

## Monitoring Performance

### Key Metrics

```python
# Track in real-time
metrics = {
    "latency_p99": 5.2,        # Target: <10µs
    "throughput": 1_000_000,   # ops/sec
    "error_rate": 0.0001,      # <0.01%
    "queue_depth": 150,        # Monitor saturation
    "cpu_usage": 75,           # Balance vs latency  
    "memory_usage": 4.2        # GB
}
```

### Profiling

```bash
# CPU profiling with perf
perf record -g ./nexus_engine
perf report

# Memory profiling
valgrind --tool=massif ./nexus_engine

# Flame graphs
perf record -g -F 99 ./nexus_engine
perf script | stackcollapse-perf.pl | flamegraph.pl > graph.html
```

## Benchmarking

### Baseline Measurement

```bash
# Single-threaded baseline
nexus benchmark --threads 1

# Multi-threaded scaling
for t in 1 2 4 8 16; do
    nexus benchmark --threads $t
done
```

### Load Testing

```bash
# Sustained load
nexus stress --threads 32 --duration 300 --ops-per-thread 100000

# Burst traffic
for i in {1..100}; do
    nexus stress --threads 64 --duration 10 &
done
```

## Containerization Optimization

### Docker Build Optimization

```dockerfile
# Multi-stage build
FROM ubuntu:22.04 as builder
# Build dependencies installed here only

FROM ubuntu:22.04
# Only runtime dependencies
COPY --from=builder /opt/nexus /opt/nexus
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  nexus_api:
    mem_limit: 8gb
    memswap_limit: 8gb
    cpus: "4.0"
    cpu_shares: 1024
```

## Benchmarking Results

### Expected Performance

| Operation | Throughput | Latency (p99) | Bottleneck |
|-----------|-----------|--------------|-----------|
| Binary XOR | 10M ops/sec | <2µs | CPU |
| Matrix 512x512 | 100k ops/sec | <50µs | Memory BW |
| SHA256 | 1M ops/sec | <30µs | CPU |
| Full Stack | 500k req/s | <100µs | API Layer |

### Scaling Profile

```
Threads:     1      4      8      16     32
Throughput:  1x    3.8x   7.5x   14.8x  25x (sublinear due to contention)
Efficiency:  100%  95%    94%    93%    78%
```

## Troubleshooting Performance

### High Latency
1. Check CPU usage - if <50%, likely I/O bound
2. Monitor queue depth - saturation?
3. Profile hot paths - 80/20 rule applies
4. Check GC pressure (Python)

### Low Throughput
1. Verify thread count matches CPU cores
2. Check for lock contention (profiling)
3. Ensure memory pre-allocation
4. Monitor network bandwidth (API)

### Memory Leaks
1. Use valgrind/ASAN
2. Enable PostgreSQL logging
3. Monitor connection pools
4. Check circular references (Python)

---

See [Architecture Guide](ARCHITECTURE.md) for system design details.
