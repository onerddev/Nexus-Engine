"""Schemas Pydantic v2 — NexusEngine Omega v3.0 | Autor: Emanuel Felipe"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

# ── Engine ──────────────────────────────────────────────────────────────────
class EngineState(str,Enum):
    STOPPED="STOPPED"; RUNNING="RUNNING"; ERROR="ERROR"

class EngineStartReq(BaseModel):
    threads: int = Field(4, ge=1, le=64)

class EngineStatusResp(BaseModel):
    status: EngineState; running: bool; threads: int=0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ── Binary ───────────────────────────────────────────────────────────────────
BINARY_OPS=["xor","and","or","not","nand","nor","xnor","shl","shr","rol","ror","popcount","parity","reverse_bits"]
class BinaryReq(BaseModel):
    operation: str = Field(..., description=f"Uma de: {BINARY_OPS}")
    value_a: int   = Field(..., ge=0)
    value_b: int   = Field(0,  ge=0)
    @field_validator("operation")
    @classmethod
    def chk(cls,v):
        if v not in BINARY_OPS: raise ValueError(f"Use: {BINARY_OPS}")
        return v

class BinaryResp(BaseModel):
    operation: str; value_a: int; value_b: int
    result: int; binary: str; hex: str; octal: str
    popcount: int; latency_us: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ── Matrix ───────────────────────────────────────────────────────────────────
MATRIX_OPS=["zeros","ones","identity","random_normal","random_uniform","diagonal","hilbert","vandermonde","toeplitz","magic"]
class MatrixReq(BaseModel):
    operation: str = Field(..., description=f"Uma de: {MATRIX_OPS}")
    rows: int = Field(4, ge=1, le=5000)
    cols: int = Field(4, ge=1, le=5000)
    @field_validator("operation")
    @classmethod
    def chk(cls,v):
        if v not in MATRIX_OPS: raise ValueError(f"Use: {MATRIX_OPS}")
        return v

class MatrixMulReq(BaseModel):
    a: List[List[float]] = Field(..., description="Matriz A")
    b: List[List[float]] = Field(..., description="Matriz B")

class MatrixSolveReq(BaseModel):
    a: List[List[float]] = Field(..., description="Matriz A (quadrada)")
    b: List[float]       = Field(..., description="Vetor b")

# ── Quantum ───────────────────────────────────────────────────────────────────
QUANTUM_INITS=["ground","superposition","random","bell","ghz"]
class QuantumGate(BaseModel):
    gate: str; qubit: int=0; target: Optional[int]=None; theta: Optional[float]=None

class QuantumReq(BaseModel):
    qubits: int = Field(4, ge=1, le=16)
    operation: str = Field("ground", description=f"Uma de: {QUANTUM_INITS}")
    gates: Optional[List[QuantumGate]] = None
    @field_validator("operation")
    @classmethod
    def chk(cls,v):
        if v not in QUANTUM_INITS: raise ValueError(f"Use: {QUANTUM_INITS}")
        return v

# ── Hash ──────────────────────────────────────────────────────────────────────
HASH_ALGOS=["md5","sha1","sha224","sha256","sha384","sha512","sha3_256","sha3_512","blake2b","blake2s"]
class HashReq(BaseModel):
    data: str = Field(..., min_length=1, max_length=500_000)
    algorithm: str = Field("sha256")
    @field_validator("algorithm")
    @classmethod
    def chk(cls,v):
        if v not in HASH_ALGOS: raise ValueError(f"Use: {HASH_ALGOS}")
        return v

class HashVerifyReq(BaseModel):
    data: str; expected: str; algorithm: str="sha256"

class HmacReq(BaseModel):
    key: str; data: str; algorithm: str="sha256"

# ── Sort ─────────────────────────────────────────────────────────────────────
SORT_ALGOS=["bubble","insertion","selection","merge","quick","heap","shell","counting"]
class SortReq(BaseModel):
    data: List[float] = Field(..., min_length=1, max_length=10_000)
    algorithm: str = Field("merge")
    @field_validator("algorithm")
    @classmethod
    def chk(cls,v):
        if v not in SORT_ALGOS: raise ValueError(f"Use: {SORT_ALGOS}")
        return v

class SortBenchmarkReq(BaseModel):
    data: List[float] = Field(..., min_length=2, max_length=500)

# ── Prime ─────────────────────────────────────────────────────────────────────
PRIME_OPS=["is_prime","sieve","factorize","goldbach","nth_prime"]
class PrimeReq(BaseModel):
    operation: str = Field(..., description=f"Uma de: {PRIME_OPS}")
    n: int = Field(97, ge=1)
    limit: int = Field(1000, ge=2, le=1_000_000)
    @field_validator("operation")
    @classmethod
    def chk(cls,v):
        if v not in PRIME_OPS: raise ValueError(f"Use: {PRIME_OPS}")
        return v

# ── Sequence ───────────────────────────────────────────────────────────────────
SEQ_OPS=["fibonacci","collatz","pascal","lucas","tribonacci"]
class SequenceReq(BaseModel):
    operation: str = Field(..., description=f"Uma de: {SEQ_OPS}")
    n: int = Field(20, ge=1, le=10_000)
    @field_validator("operation")
    @classmethod
    def chk(cls,v):
        if v not in SEQ_OPS: raise ValueError(f"Use: {SEQ_OPS}")
        return v

# ── Statistics ────────────────────────────────────────────────────────────────
class StatsReq(BaseModel):
    data: List[float] = Field(..., min_length=2, max_length=100_000)

class CorrelationReq(BaseModel):
    x: List[float]; y: List[float]

class HistogramReq(BaseModel):
    data: List[float] = Field(..., min_length=2)
    bins: int = Field(10, ge=2, le=100)

# ── Metrics ───────────────────────────────────────────────────────────────────
class MetricsData(BaseModel):
    p50:float; p95:float; p99:float; p999:float; mean:float; min:float; max:float

class MetricsResp(BaseModel):
    total_operations: int; total_errors: int; error_rate: float
    latency_us: MetricsData; throughput_ops_sec: float
    by_module: Dict[str,int]; cpu_percent: float
    memory_bytes: int; uptime_seconds: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StressReq(BaseModel):
    threads: int = Field(4, ge=1, le=32)
    operations_per_thread: int = Field(2000, ge=100, le=100_000)

class StressResp(BaseModel):
    status: str; threads: int; total_operations: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ── Health ────────────────────────────────────────────────────────────────────
class HealthResp(BaseModel):
    status: str; version: str="3.0.0"; author: str="Emanuel Felipe"
    components: Dict[str,str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
