"""
Pydantic models for NexusEngine API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EngineStateEnum(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class EngineStartRequest(BaseModel):
    threads: int = Field(4, ge=1, le=256, description="Number of worker threads")
    queue_capacity: int = Field(100000, ge=1000, description="Queue capacity")
    
    class Config:
        schema_extra = {
            "example": {
                "threads": 16,
                "queue_capacity": 100000
            }
        }


class EngineStatusResponse(BaseModel):
    status: EngineStateEnum
    running: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "status": "RUNNING",
                "running": True,
                "timestamp": "2026-02-11T10:00:00"
            }
        }


class BinaryOperationRequest(BaseModel):
    operation: str = Field(..., description="xor, and, or, not")
    value_a: int = Field(..., description="First value")
    value_b: Optional[int] = Field(None, description="Second value")
    
    @validator('operation')
    def validate_operation(cls, v):
        valid = {'xor', 'and', 'or', 'not'}
        if v.lower() not in valid:
            raise ValueError(f"Operation must be one of {valid}")
        return v.lower()


class BinaryOperationResponse(BaseModel):
    operation: str
    value_a: int
    value_b: Optional[int]
    result: int
    result_binary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MatrixComputeRequest(BaseModel):
    operation: str = Field(..., description="create, zeros, ones, identity, random")
    rows: int = Field(256, ge=1, le=10000)
    cols: int = Field(256, ge=1, le=10000)
    
    @validator('operation')
    def validate_operation(cls, v):
        valid = {'create', 'zeros', 'ones', 'identity', 'random'}
        if v.lower() not in valid:
            raise ValueError(f"Operation must be one of {valid}")
        return v.lower()


class MatrixComputeResponse(BaseModel):
    operation: str
    rows: int
    cols: int
    sample: List[List[float]] = Field(..., description="First 3x3 sample")
    status: str


class QuantumSimulateRequest(BaseModel):
    qubits: int = Field(6, ge=1, le=32, description="Number of qubits")
    operation: str = Field("init", description="init, hadamard, measure")
    qubit_index: Optional[int] = Field(None, description="Qubit index for targeted operations")


class QuantumSimulateResponse(BaseModel):
    qubits: int
    operation: str
    probabilities: List[Dict[str, float]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsData(BaseModel):
    p50: float = Field(..., description="50th percentile latency (µs)")
    p95: float = Field(..., description="95th percentile latency (µs)")
    p99: float = Field(..., description="99th percentile latency (µs)")
    p999: float = Field(..., description="99.9th percentile latency (µs)")
    mean: float = Field(..., description="Mean latency (µs)")
    min: float = Field(..., description="Minimum latency (µs)")
    max: float = Field(..., description="Maximum latency (µs)")


class AggregatedMetricsResponse(BaseModel):
    total_operations: int
    total_errors: int
    error_rate: float
    latency_us: MetricsData
    throughput_ops_sec: float
    queue_size: int
    cpu_usage_percent: float
    memory_bytes: int
    uptime_seconds: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str = Field(..., description="HEALTHY, DEGRADED, UNHEALTHY")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, str] = Field(..., description="Component status")
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class StressTestRequest(BaseModel):
    threads: int = Field(16, ge=1, le=256)
    duration_seconds: int = Field(10, ge=1, le=3600)
    operations_per_thread: int = Field(10000, ge=100)


class StressTestResponse(BaseModel):
    status: str
    threads: int
    duration_seconds: int
    total_operations: int
    throughput_ops_sec: float
    max_latency_us: float
    error_rate: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
