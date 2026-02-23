# Architecture Design - NexusEngine

**Version**: 1.0.0  
**Author**: Emanuel Felipe  
**Purpose**: System design, rationale, and constraints

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      REST API Layer                          │
│                (FastAPI + Uvicorn)                          │
│  /engine  /compute  /metrics  /health                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Python Service Layer                            │
│  - Request validation (Pydantic)                            │
│  - Business logic (services.py)                             │
│  - Metrics aggregation                                      │
└────────────────────┬────────────────────────────────────────┘
                     │ Cython / C++ FFI
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           C++ Core Components (nexus namespace)             │
│                                                              │
│  CoreEngine (Orchestrator)                                  │
│    ├─ ThreadPool (Task scheduling)                         │
│    ├─ MemoryPool (Fixed-size allocation)                   │
│    └─ MetricsCollector (Statistics)                        │
│                                                              │
│  Computational Engines                                      │
│    ├─ MatrixEngine (Linear algebra)                        │
│    ├─ BinaryProcessor (Bitwise ops)                        │
│    ├─ QuantumSimulator (Probability model)                 │
│    └─ HashEngine (Non-crypto hashing)                      │
│                                                              │
│  Support                                                    │
│    ├─ PluginLoader (Dynamic loading)                       │
│    └─ LockFreeQueue (Task queue)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Separation of Concerns

- **API Layer**: Routes, validation, HTTP concerns
- **Service Layer**: Business logic, orchestration
- **Core Layer**: Computation, synchronization

**Benefit**: Changes in one layer don't affect others.

### 2. Interface Over Implementation

- Define interfaces for extensible components (Plugin)
- Use abstract base classes where appropriate
- Enable testing with mocks

### 3. Explicit Over Implicit

- Clear concurrency model (mutex-based, not lock-free)
- Explicit memory ownership (RAII)
- Explicit error handling (exceptions)

### 4. Simplicity Over Optimality

- Use standard containers (std::vector, std::priority_queue)
- Use standard synchronization (std::mutex, std::atomic)
- Avoid micro-optimizations

---

## Component Responsibilities

### API Layer (Python/FastAPI)

**Responsibility**: HTTP handling and validation

**Components**:
- `api/main.py` - FastAPI application
- `api/routers/routes.py` - Endpoint definitions
- `api/models/schemas.py` - Pydantic models
- `api/middleware/middleware.py` - Cross-cutting concerns
- `api/services/services.py` - Business logic
- `api/validation.py` - Input validation (NEW)

**Ownership**: Request is API's responsibility until passing to C++

**Constraints**:
- Stateless (no memory between requests)
- Timeout-protected (prevent hanging)
- Rate-limited (prevent resource exhaustion)

### Cython Bridge (docker/cython/nexus_engine.pyx)

**Responsibility**: Python ↔ C++ translation

**Features**:
- Type conversion (int ↔ uint64_t, str ↔ std::string)
- Memory management (PyObject ↔ C++ pointers)
- Exception mapping (C++ exceptions → Python)

**Key Classes**:
- `PyCoreEngine` - Wraps CoreEngine
- `PyBinaryProcessor` - Wraps BinaryProcessor
- `PyQuantumSimulator` - Wraps QuantumSimulator
- `PyMatrixEngine` - Wraps MatrixEngine

### C++ Core (cpp/)

#### CoreEngine (Orchestrator)

**Responsibility**: Centralized engine state management

**State Machine**:
```
STOPPED ──start──→ RUNNING
                      ↑↓
   PAUSED ←pause/resume→
   
   ←stop←─── at any state
```

**Fields**:
- `state_` - Current operational state
- `worker_threads_` - Pool of worker threads
- `metrics_` - Aggregated statistics
- `config_` - Configuration (immutable once started)

**Operations**:
- `start()` - Create workers
- `stop()` - Shutdown gracefully
- `pause()` - Suspend processing
- `resume()` - Continue processing

#### ThreadPool (Task Scheduling)

**Responsibility**: Distribute tasks to multiple workers

**Design**:
```
Main Thread                         Worker Threads
    │                                    │
    ├─ submit(fn, args)                 ├─ Listen for tasks
    │   ↓                                │
    ├─ Lock queue_mutex               │ Acquire queue_mutex
    │   ├─ Push to priority_queue      │ Get task from queue
    │   └─ Unlock                       │ Release queue_mutex
    │   ├─ Notify via condition_var    │ Execute task (no lock)
    │                                   │ Update stats (atomic)
    └─ Get std::future                 └─ Repeat
        ↓
    Wait for result
```

**Key Fields**:
- `task_queue_` - std::priority_queue<Task>
- `queue_mutex_` - Protects queue access
- `queue_cv_` - Wakes workers on new task
- `workers_` - std::vector<std::thread>
- `stats_` - Task statistics (atomic)

**Priority Levels**:
- HIGH (2): Urgent tasks
- NORMAL (1): Regular tasks
- LOW (0): Background tasks

#### MemoryPool (Fixed-Size Allocator)

**Responsibility**: Pre-allocated block allocation

**Design**:
```
Pre-allocation Phase:
    MemoryPool(4096, 1000)
    ↓
    Allocates 1000 × 4096 byte blocks
    ↓
    Total: 4MB allocated upfront

Runtime:
    allocate() → O(n) linear search
    deallocate(ptr) → O(n) linear search
    has_free_blocks() → O(1) atomic check
```

**Configuration**:
- Block size: Fixed at construction
- Block count: Fixed at construction
- No dynamic reallocation

**Use Case**:
- Fixed-size objects (metadata, caches)
- Predictable allocation patterns
- Bounded memory usage

#### MatrixEngine (Linear Algebra)

**Responsibility**: Matrix computations

**Algorithms**:
- `multiply()` - O(n³) with Strassen optimization (partially implemented)
- `transpose()` - O(n²) in-place or out-of-place
- `inverse()` - Gaussian elimination O(n³)
- `qr_decomposition()` - Householder reflections
- `svd()` - Singular value decomposition

**Data Layout**:
```cpp
using Matrix = std::vector<std::vector<double>>;

// Row-major storage
Matrix m(rows, std::vector<double>(cols));
// Good: Cache-friendly row access
// Bad: Not SIMD-friendly (column-major is better)
```

**Thread Safety**: Operations are thread-safe (no shared state), but results not verified.

#### BinaryProcessor (Bitwise Operations)

**Responsibility**: Fast bitwise operations

**Operations**:
- `xor_op()`, `and_op()`, `or_op()`, `not_op()`
- `popcount()` - Count set bits (uses __builtin_popcount)
- `hamming_distance()` - Bit differences
- Vector variants for batch operations

**Performance**: < 10 cycles per operation

#### QuantumSimulator (Probability-Based Simulation)

**Responsibility**: Classical simulation of quantum behavior

**Important**: NOT actual quantum computing

**Model**:
- Qubits represented as complex amplitudes
- Single-qubit gates (Hadamard, Pauli-X/Y/Z)
- Multi-qubit gates (CNOT, SWAP)
- Measurement (probabilistic collapse)
- Entanglement (Bell pairs)

**Limitation**: Exponential state space O(2^n), practical up to ~20 qubits

#### HashEngine (Non-Cryptographic Hashing)

**Responsibility**: Fast hashing for non-security use

**Algorithms**:
- `xxhash64` - Ultra-fast (1-2 GB/s)
- `murmur3_64` - Good distribution (500-800 MB/s)
- `sha256_mock` - Fast but NOT secure
- `blake2b_256_mock` - Fast but NOT secure

**NOT SUITABLE FOR**:
- Cryptography
- Password hashing
- Signature generation
- Key derivation

**SUITABLE FOR**:
- Hash tables
- Deduplication
- Load balancing
- Checksums (non-security)

#### MetricsCollector (Statistics)

**Responsibility**: Performance metrics aggregation

**Metrics Tracked**:
- Latency (min, max, sum)
- Throughput (tasks/sec)
- Error count and rate
- Queue depth
- CPU/memory usage

**Thread Safety**: Atomic operations, eventual consistency

**Output**: JSON serialization for monitoring systems

#### PluginLoader (Extension System)

**Responsibility**: Load and manage plugins dynamically

**Status**: Stub/not implemented

**Design Intent**:
```cpp
// Load plugin
Plugin* plugin = loader.get_plugin("my_plugin");

// Execute
if (plugin) {
    plugin->initialize();
    plugin->execute();
    plugin->shutdown();
}
```

---

## Data Flow

### Compute Request Flow

```
1. HTTP POST /compute/binary
   {operation: "xor", value_a: 255, value_b: 170}
   
2. FastAPI Route Handler
   ├─ Validate with Pydantic schema
   ├─ Forward to HostService via language boundary
   └─ Return JSON response
   
3. Service Layer (Python)
   ├─ Call C++ function via Cython
   ├─ Handle C++ exceptions
   └─ Aggregate metrics
   
4. C++ Computation
   ├─ Execute operation (fast, no allocation)
   ├─ Update metrics (atomic, lock-free)
   └─ Return result
   
5. Response Assembly
   ├─ Convert result to JSON
   ├─ Add metadata (timestamp, operation)
   └─ Send to client
```

### Task Submission Flow

```
1. Application Code
   auto future = threadpool.submit(compute_task, arg1, arg2);
   
2. ThreadPool::submit_with_priority()
   ├─ Create std::promise<Result>
   ├─ Capture callable + arguments
   ├─ Create wrapper task
   └─ Call enqueue_task()
   
3. ThreadPool::enqueue_task()
   ├─ Acquire queue_mutex (LOCK)
   ├─ stats_.total_tasks++
   ├─ task_queue_.push({NORMAL, task})
   ├─ Release queue_mutex (UNLOCK)
   └─ queue_cv_.notify_one()
   
4. Worker Thread (concurrently)
   ├─ Wake up from condition_variable
   ├─ Acquire queue_mutex (LOCK)
   ├─ Get task from queue_mutex
   ├─ Release queue_mutex (UNLOCK)
   ├─ Execute task (no lock held)
   │  └─ promise.set_value(result)
   ├─ stats_.completed_tasks++ (atomic)
   └─ Loop back to wait
   
5. Main Thread (async)
   auto result = future.get();  // Blocks until ready
   // Now has result from worker
```

---

## Error Handling Strategy

### C++ Layer

**Throwing Exceptions**:
```cpp
// Suitable for throwing
throw std::invalid_argument("block_size must be > 0");
throw std::runtime_error("Failed to start engine");

// Exception safety: Strong guarantee
// If partial construction fails, all resources released
```

**Checked Exceptions**:
```cpp
// Return error code instead of throwing
void* ptr = pool.allocate();
if (!ptr) {
    // Handle exhaustion gracefully
}
```

### Python/API Layer

**Pydantic Validation**:
```python
# Automatic validation
try:
    request = EngineStartRequest(threads=5, queue_capacity=100000)
except ValidationError as e:
    # Return 422 Unprocessable Entity
```

**Exception Mapping**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500)
```

### Graceful Degradation

**When Resource Exhausted**:
```cpp
void* ptr = pool.allocate();
if (!ptr) {
    // Log and return error
    // Don't allocate from fallback (prevents hiding problems)
    return nullptr;
}
```

---

## Scalability Constraints

### Horizontal Scaling (Multiple Servers)

**Current**: Not supported

**Would require**:
- Distributed task queue (RabbitMQ, Kafka)
- Load balancer (nginx, HAProxy)
- Shared state management (Redis, etcd)
- State synchronization protocol

### Vertical Scaling (More Cores)

**Currently supported** for ThreadPool:
- Configurable thread count
- No auto-scaling (manual configuration)
- Mutex contention increases linearly

**Bottleneck**: `queue_mutex` becomes contention point with 100+ threads

**Solution** (future): Per-core work-stealing queues

### Memory Scaling

**MemoryPool constraints**:
- Fixed at construction
- No dynamic growth
- Must pre-size for peak load

**Container constraints** (vectors in MetricsCollector):
- Unbounded latency sample collection
- Potential memory leak if not cleared

---

## Deployment Architecture

### Single-Machine Deployment

```
┌────────────┐
│ HTTP Client│
└─────┬──────┘
      │ http://localhost:8000
      ↓
┌────────────────────────────┐
│ Uvicorn (1 worker)         │ ← ASGI server
│ ├─ Event loop              │
│ └─ FastAPI app             │
└─────┬──────────────────────┘
      │
      ↓
┌────────────────────────────┐
│ ThreadPool (8 workers)     │ ← C++ computation
│ └─ task_queue (mutex)      │
└────────────────────────────┘
```

### Docker Deployment

```dockerfile
FROM python:3.11
RUN apt-get install build-essential cmake
COPY . /app
WORKDIR /app
RUN pip install -e . --no-build-isolation
    # Builds C++ + Cython bindings
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

---

## Extension Points

### 1. Custom Computations

Adding new operation in MatrixEngine:

```cpp
// In matrix_engine.hpp
static Matrix custom_transform(const Matrix& m);

// In matrix_engine.cpp
Matrix MatrixEngine::custom_transform(const Matrix& m) {
    // Implementation
}
```

### 2. Custom Metrics

Adding new metric in MetricsCollector:

```cpp
void record_custom_event(const std::string& event_name, uint64_t value);
```

### 3. Plugins

Plugin interface supports dynamic loading (not implemented):

```cpp
class MyPlugin : public Plugin {
    void initialize() override { /* ... */ }
    void execute() override { /* ... */ }
    void shutdown() override { /* ... */ }
};
```

---

## Known Limitations

1. **Single-machine only**: No distributed computing
2. **Fixed memory pools**: No dynamic sizing
3. **Mutex-based**: Lock contention with 100+ threads
4. **No work-stealing**: Load imbalance possible
5. **No auto-scaling**: Manual thread configuration
6. **Hash insecurity**: Never use for cryptography

---

## Comparison with Alternatives

| Aspect | NexusEngine | Boost | TBB | Akka |
|--------|-------------|-------|-----|------|
| **Language** | C++ | C++ | C++ | Scala |
| **Concurrency** | Mutex | Varies | Lock-free | Actor |
| **Learning Curve** | Easy | Medium | Medium | Hard |
| **Production Ready** | No | Yes | Yes | Yes |

**Recommendation**: NexusEngine for learning, established libs for production.

---

**Document**: ARCHITECTURE.md  
**Author**: Emanuel Felipe  
**Last Updated**: 2026-02-22



