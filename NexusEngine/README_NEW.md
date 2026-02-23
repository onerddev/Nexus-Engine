# NexusEngine - Hybrid Computational Platform

**Version**: 1.0.0  
**Author**: Emanuel Felipe  
**License**: MIT  
**Status**: Development (see limitations)

---

## Overview

NexusEngine is a hybrid computational framework combining C++20 for performance-critical operations with Python/Cython for flexibility and accessibility. It provides components for:

- **Matrix operations** (linear algebra, transformations)
- **Binary operations** (bitwise operations, popcount)
- **Pseudo-quantum simulation** (probability-based qubit simulation, not actual quantum computing)
- **Hashing** (non-cryptographic fast hashing)
- **Thread pooling** (work distribution)
- **Memory pooling** (fixed-block allocation)
- **Metrics collection** (latency tracking, statistics)

## What This Project Is

A **learning/research implementation** demonstrating:
- C++20 features and modern concurrency patterns
- Python/C++ interoperability via Cython
- REST API design
- Performance monitoring basics

## What This Project Is NOT

- **Not production-ready** without additional testing and hardening
- **Not cryptographically secure** (see hash engine documentation)
- **Not quantum computing** (quantum_simulator is a classical probabilistic model)
- **Not a replacement** for established libraries (NumPy, Eigen, etc.)

---

## Architecture

### Component Structure

```
┌─────────────────────────────────────────────────────┐
│  REST API (FastAPI)                                 │
│  Routes: /engine, /compute, /metrics, /health       │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  Python/Cython Bindings (nexus_engine.pyx)         │
│  Exposes C++ classes to Python                     │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  C++ Core Components                                │
│  ├─ CoreEngine (orchestrator)                       │
│  ├─ MemoryPool (fixed-block allocator)             │
│  ├─ ThreadPool (task queue + workers)              │
│  ├─ MatrixEngine (linear algebra)                  │
│  ├─ BinaryProcessor (bitwise ops)                  │
│  ├─ QuantumSimulator (probability model)           │
│  ├─ HashEngine (fast non-crypto hashing)           │
│  ├─ MetricsCollector (statistics)                  │
│  └─ PluginLoader (dynamic loading stub)            │
└──────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| API | FastAPI | 0.104+ |
| Async Runtime | Uvicorn | 0.24+ |
| Python Bridge | Cython | 3.0+ |
| Core | C++20 | GCC/Clang |
| Database | PostgreSQL | 15+ (optional) |
| Monitoring | Prometheus | 2.x |
| Container | Docker | 20.x |

---

## Concurrency Model

### Definition

NexusEngine uses a **mutex-based thread pool with priority queue**:

1. **Main coordination**: `std::mutex` protects task queue
2. **Atomic metrics**: `std::atomic<T>` for lock-free statistics
3. **Synchronization**: `std::condition_variable` for worker wakeup
4. **NOT lock-free**: Uses mutex for simplicity and correctness

### Key Components

**ThreadPool**:
- Fixed number of worker threads
- Blocking work queue (priority levels)
- Condition variable signaling
- Thread-safe task submission/results via `std::future`

**MemoryPool**:
- Mutex-protected block allocation
- Atomic counters for statistics
- Not lock-free (simple linear search)

**MetricsCollector**:
- Atomic operations for lock-free stat updates
- No synchronization on sampling (eventual consistency)

### Important Notes

- [AVISO] **NOT lock-free**: Uses `std::mutex` for correctness
- [AVISO] **No work-stealing**: Uses simple FIFO queue per priority level
- [AVISO] **No auto-scaling**: Fixed thread count at startup
- ✓ **Straightforward**: Easy to reason about, verify, and debug

---

## Memory Model

### Allocation Strategy

**MemoryPool**:
- Pre-allocates fixed number of fixed-size blocks
- Ownership tracking via atomic flags
- O(n) allocation in worst case (linear search)
- No fragmentation (fixed blocks)

**Thread Safety**:
- All allocations protected by `std::mutex`
- Deallocation validates ownership
- Deallocating non-owned pointer: undefined behavior

### Important Limitations

- **Fixed block size**: Cannot accommodate variable sizes
- **Exhaustion**: Returns nullptr when pool depleted
- **No reallocation**: Fixed capacity at construction
- **Linear search**: O(n) for allocation

### Recommendations

- Pre-size pools based on workload analysis
- Profile allocation patterns
- Plan for exhaustion scenarios

---

## API Usage

### Basic Example

```python
from nexus_engine import PyCoreEngine, PyBinaryProcessor

# Initialize and start engine
engine = PyCoreEngine()
engine.start()

# Perform binary operation
result = PyBinaryProcessor.xor(0xFF, 0xAA)
print(f"0xFF XOR 0xAA = {result:#x}")

engine.stop()
```

### REST API Example

```bash
# Start engine
curl -X POST http://localhost:8000/engine/start \
  -H "Content-Type: application/json" \
  -d '{"threads": 4}'

# Perform computation
curl -X POST http://localhost:8000/compute/binary \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "xor",
    "value_a": 255,
    "value_b": 170
  }'

# Get metrics
curl http://localhost:8000/metrics/current

# Stop engine
curl -X POST http://localhost:8000/engine/stop
```

---

## Building

### Requirements

- C++20 compiler (GCC 11+ or Clang 14+)
- CMake 3.20+
- Python 3.11+
- Cython 3.0+

### From Source

```bash
# Clone repository
git clone https://github.com/onerddev/Nexus-Engine.git/docker-compose.yml up
```

---

## Limitations

### Known Issues

1. **Hash Functions**: Not cryptographically secure (see SECURITY_MODEL.md)
2. **Quantum Simulator**: Classical simulation, not actual QC
3. **ThreadPool**: 
   - No work-stealing (simpler)
   - No auto-scaling
   - Fixed capacity
4. **MemoryPool**:
   - O(n) allocation time
   - Fixed block size
   - Limited by pre-allocated capacity
5. **Performance**: Not optimized for extreme latency constraints

### Production Readiness

| Component | Status | Recommendation |
|-----------|--------|---|
| Core Engine | Functional | Add comprehensive tests |
| ThreadPool | Functional | Profile performance |
| MemoryPool | Functional | Validate for target workload |
| API | Functional | Add authentication, rate limiting |
| Crypto | [NAO] DO NOT USE | Never for security purposes |

---

## Testing

### Current Status

- C++ unit tests: Not yet integrated
- Integration tests: Manual only
- Sanitizers: AddressSanitizer/ThreadSanitizer not enabled

### Recommended

Before production use, ensure:

```bash
# Build with AddressSanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..

# Build with ThreadSanitizer  
cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread" ..

# Run comprehensive tests
pytest tests/ -v
```

---

## Performance Notes

### Measured Behavior

- MemoryPool: ~microsecond allocation (uncontended)
- ThreadPool: Task submission ~microseconds
- MatrixEngine: Standard `O(n³)` for multiplication
- Hashing: >100MB/sec on typical hardware

### Not Measured

- Latency percentiles (p50, p95, p99)
- Scaling to 100+ threads
- Memory fragmentation over time
- Cache behavior

### Benchmark Against Real World

For production workloads, profile against:
- Standard library allocators
- Boost.Asio thread pool
- Intel TBB task scheduler
- Established numerical libraries

---

## Security Model

### Threat Model

**This project is NOT suitable for:**
- Password hashing (not cryptographically secure)
- Digital signatures (wrong hash algorithm)
- HMAC operations (insecure hash)
- Encryption key derivation (weak hash)

**Suitable for:**
- Deduplication (non-adversarial)
- Hash tables (internal use)
- Load balancing (non-critical)
- Performance testing (internal benchmark)

### API Security

Current implementation provides:
- ✓ Input validation (bounds checking)  
- ✓ Exception handling (basic)
- ✗ Authentication (none)
- ✗ Authorization (none)
- ✗ Rate limiting (none)
- ✗ TLS/HTTPS (none)

**Production**: Add FastAPI middleware for:
- API key authentication
- Rate limiting per client
- HTTPS/TLS support
- Request logging

---

## Roadmap

### v1.1 (Next)
- [ ] Comprehensive unit tests (GoogleTest)
- [ ] AddressSanitizer integration
- [ ] ThreadSanitizer validation
- [ ] Benchmark suite with comparisons
- [ ] Documentation improvements

### v2.0 (Future)
- [ ] Lock-free queue alternative
- [ ] Work-stealing thread pool option
- [ ] GPU acceleration (CUDA) for matrix ops
- [ ] Distributed computing support
- [ ] Plugin system implementation

### Out of Scope
- Quantum computing simulation (use Qiskit instead)
- Cryptography (use OpenSSL/libsodium)
- Full distributed computing (use Apache Spark)

---

## Contributing

Development workflow:
1. Follow C++ Core Guidelines
2. Add tests for new features
3. Validate with AddressSanitizer
4. Document assumptions and limitations
5. Avoid marketing-speak in code comments

---

## Citation

If you use NexusEngine in research, please cite:

```bibtex
@software{nexusengine2024,
  author = {Emanuel Felipe},
  title = {NexusEngine: Hybrid Computational Platform},
  year = {2024},
  url = {https://github.com/...}
}
```

---

## License

MIT License - See LICENSE file for full text.

---

**Documentation Status**: Accurate as of v1.0.0  
**Last Updated**: 2026-02-22  
**Author**: Emanuel Felipe



