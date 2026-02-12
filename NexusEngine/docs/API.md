# API Reference - NexusEngine Omega

## Overview

NexusEngine Omega provides a comprehensive RESTful API for all computational operations. All requests/responses use JSON format with UTF-8 encoding.

## Base URL

```
http://localhost:8000
```

## Authentication

Optional API key authentication (when enabled):

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/engine/status
```

## Response Format

### Success Response (2xx)

```json
{
    "status": "success",
    "data": { /* operation-specific data */ },
    "timestamp": "2024-01-15T10:30:45.123Z",
    "request_id": "req-uuid-here"
}
```

### Error Response (4xx, 5xx)

```json
{
    "status": "error",
    "error": {
        "code": "INVALID_INPUT",
        "message": "Operation must be one of: xor, and, or, not",
        "details": {
            "field": "operation",
            "constraint": "enum"
        }
    },
    "timestamp": "2024-01-15T10:30:45.123Z",
    "request_id": "req-uuid-here"
}
```

## Endpoints

### Health & Status

#### GET /health
Check API health status.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 3600,
    "database": "connected",
    "cache": "connected"
}
```

**Code:** 200 OK

---

#### GET /ping
Simple ping endpoint for load balancing.

**Response:** `"pong"`

**Code:** 200 OK

---

#### GET /version
Get API version information.

**Response:**
```json
{
    "version": "1.0.0",
    "build_date": "2024-01-15",
    "commit_sha": "abc123def456"
}
```

**Code:** 200 OK

---

### Engine Control

#### POST /engine/start
Start the computation engine.

**Request:**
```json
{
    "threads": 16,
    "queue_capacity": 100000,
    "enable_metrics": true
}
```

**Response:**
```json
{
    "status": "started",
    "threads": 16,
    "queue_capacity": 100000,
    "timestamp": "2024-01-15T10:30:45Z"
}
```

**Codes:**
- 200: Engine started
- 409: Already running
- 422: Invalid parameters

---

#### POST /engine/stop
Stop the computation engine gracefully.

**Response:**
```json
{
    "status": "stopped",
    "processed_items": 150000,
    "uptime_seconds": 300
}
```

**Codes:**
- 200: Engine stopped
- 409: Not running
- 503: Timeout during shutdown

---

#### GET /engine/status
Get current engine status.

**Response:**
```json
{
    "state": "running",
    "threads": 16,
    "queue_depth": 250,
    "processed_items": 150000,
    "throughput": 500000,
    "uptime_seconds": 300
}
```

**Codes:**
- 200: Status retrieved
- 503: Engine offline

---

#### POST /engine/pause
Pause engine operation.

**Response:**
```json
{
    "status": "paused",
    "timestamp": "2024-01-15T10:30:45Z"
}
```

**Codes:**
- 200: Engine paused
- 409: Already paused

---

#### POST /engine/resume
Resume engine operation.

**Response:**
```json
{
    "status": "resumed",
    "timestamp": "2024-01-15T10:30:45Z"
}
```

**Codes:**
- 200: Engine resumed
- 409: Engine not paused

---

### Compute Operations

#### POST /compute/binary
Perform binary bitwise operations.

**Request:**
```json
{
    "operation": "xor",
    "value_a": 255,
    "value_b": 127,
    "format": "decimal"
}
```

**Parameters:**
- `operation`: "xor" | "and" | "or" | "not" | "xnor" | "nand" | "nor"
- `value_a`: 0 to 2^64-1
- `value_b`: 0 to 2^64-1 (optional for unary ops)
- `format`: "decimal" | "binary" | "hex" (default: "decimal")

**Response:**
```json
{
    "operation": "xor",
    "value_a": 255,
    "value_b": 127,
    "result": 128,
    "execution_time_us": 1.2,
    "format": "decimal"
}
```

**Codes:**
- 200: Operation successful
- 422: Invalid operation or values
- 503: Engine not running

---

#### POST /compute/matrix
Perform matrix operations.

**Request:**
```json
{
    "operation": "multiply",
    "rows": 256,
    "cols": 256,
    "matrix_a": [[1, 2], [3, 4]],
    "matrix_b": [[5, 6], [7, 8]],
    "format": "dense"
}
```

**Parameters:**
- `operation`: "random" | "multiply" | "transpose" | "invert" | "qr" | "svd"
- `rows`, `cols`: Matrix dimensions
- `matrix_a`, `matrix_b`: Matrix data (dense format)
- `format`: "dense" | "sparse"

**Response:**
```json
{
    "operation": "multiply",
    "rows": 256,
    "cols": 256,
    "result": [[...matrix data...]],
    "execution_time_us": 2500,
    "statistics": {
        "mean": 42.5,
        "std_dev": 15.3,
        "min": 1.0,
        "max": 99.9
    }
}
```

**Codes:**
- 200: Operation successful
- 422: Invalid matrix dimensions
- 503: Engine not running

---

#### POST /compute/quantum
Perform quantum circuit simulation.

**Request:**
```json
{
    "qubits": 8,
    "operations": [
        {
            "gate": "hadamard",
            "target": 0
        },
        {
            "gate": "cnot",
            "control": 0,
            "target": 1
        }
    ]
}
```

**Parameters:**
- `qubits`: 2-16 qubit register
- `operations`: Array of gate operations
  - `gate`: "hadamard" | "pauli_x" | "pauli_y" | "pauli_z" | "cnot" | "bell"
  - `target`: Qubit index
  - `control`: Control qubit (for 2-qubit gates)

**Response:**
```json
{
    "qubits": 8,
    "measurements": [0, 1, 0, 0, 1, 1, 0, 1],
    "probabilities": {
        "0": 0.125,
        "1": 0.875
    },
    "execution_time_us": 4800
}
```

**Codes:**
- 200: Simulation successful
- 422: Invalid circuit
- 503: Engine not running

---

#### POST /compute/hash
Compute hash of input data.

**Request:**
```json
{
    "data": "hello world",
    "algorithm": "sha256",
    "format": "hex"
}
```

**Parameters:**
- `data`: Input string or binary
- `algorithm`: "sha256" | "murmur3" | "xxhash" | "blake2"
- `format`: "hex" | "base64" | "decimal"

**Response:**
```json
{
    "data": "hello world",
    "algorithm": "sha256",
    "hash": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
    "format": "hex",
    "execution_time_us": 12.5
}
```

**Codes:**
- 200: Hash successful
- 422: Invalid algorithm or format
- 503: Engine not running

---

### Metrics & Monitoring

#### GET /metrics
Get current metrics and performance data.

**Query Parameters:**
- `period`: "1m" | "5m" | "15m" | "1h" (default: "1m")
- `aggregation`: "p50" | "p95" | "p99" | "p999" (default: "p99")

**Response:**
```json
{
    "period": "1m",
    "timestamp": "2024-01-15T10:30:45Z",
    "latency_us": {
        "min": 0.8,
        "max": 52.3,
        "mean": 5.2,
        "p50": 3.5,
        "p95": 15.8,
        "p99": 45.2,
        "p999": 50.1
    },
    "throughput": 500000,
    "error_rate": 0.0001,
    "queue_depth": 150
}
```

**Codes:**
- 200: Metrics retrieved
- 503: Engine not running

---

#### GET /metrics/export
Export metrics in a specific format.

**Query Parameters:**
- `format`: "json" | "csv" | "prometheus"
- `period`: Time period (default: "1h")

**Response:** 
Format-specific export (JSON array, CSV text, or Prometheus format)

**Codes:**
- 200: Export successful
- 422: Invalid format

---

#### POST /metrics/stress-test
Execute stress test and return metrics.

**Request:**
```json
{
    "duration_seconds": 60,
    "threads": 32,
    "operations_per_thread": 100000
}
```

**Response:**
```json
{
    "status": "completed",
    "duration_seconds": 60,
    "total_operations": 3200000,
    "throughput": 53333,
    "latency": {
        "p50": 2.1,
        "p95": 8.5,
        "p99": 25.3,
        "p999": 45.2
    },
    "errors": 0,
    "error_rate": 0.0
}
```

**Codes:**
- 200: Test completed
- 422: Invalid parameters
- 503: Engine not running

---

## Rate Limiting

Endpoints are rate-limited to 1000 requests/minute by default.

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705316445
```

**Rate Limit Exceeded (429):**
```json
{
    "status": "error",
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "1000 requests per minute limit exceeded",
        "retry_after_seconds": 45
    }
}
```

---

## Error Codes

| Code | Message | Meaning |
|------|---------|---------|
| 200 | OK | Request successful |
| 400 | Bad Request | Malformed request |
| 401 | Unauthorized | Invalid API key |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Endpoint not found |
| 409 | Conflict | Operation conflicts with current state |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Engine offline |

---

## Interactive API Documentation

Full interactive API documentation available at:

```
http://localhost:8000/docs
```

Based on OpenAPI 3.0.0 specification.

---

## Examples

### Example 1: Binary XOR Operation

```bash
curl -X POST http://localhost:8000/compute/binary \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "xor",
    "value_a": 255,
    "value_b": 127
  }'
```

### Example 2: Start Engine and Check Status

```bash
# Start engine
curl -X POST http://localhost:8000/engine/start \
  -H "Content-Type: application/json" \
  -d '{
    "threads": 16,
    "queue_capacity": 100000
  }'

# Check status
curl http://localhost:8000/engine/status
```

### Example 3: Run Stress Test

```bash
curl -X POST http://localhost:8000/metrics/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "duration_seconds": 300,
    "threads": 64,
    "operations_per_thread": 1000000
  }' | jq '.throughput'
```

---

## Webhook Support (v1.1.0+)

Future versions will support webhooks for long-running operations.

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for API changes and version history.
