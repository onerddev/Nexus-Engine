"""Routes — NexusEngine Omega v3.0 | Autor: Emanuel Felipe"""
import time, logging, threading
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models.schemas import *
from ..services.services import engine_service, compute_service, metrics_service

logger = logging.getLogger(__name__)

engine_router   = APIRouter(prefix="/engine",         tags=["🔧 Engine"])
compute_router  = APIRouter(prefix="/compute",        tags=["⚡ Compute"])
hash_router     = APIRouter(prefix="/hash",           tags=["🔐 Hash"])
metrics_router  = APIRouter(prefix="/metrics",        tags=["📊 Metrics"])
health_router   = APIRouter(tags=["✅ Health"])

def _t(): return time.perf_counter()
def _lat(t0): return (time.perf_counter()-t0)*1e6
def _err(r): return "error" in r

# ── Engine ────────────────────────────────────────────────────────────────────
@engine_router.post("/start", response_model=EngineStatusResp, summary="Iniciar engine")
async def start_engine(req: EngineStartReq):
    if not engine_service.start(req.threads): raise HTTPException(500,"Falha ao iniciar")
    s=engine_service.get_status()
    return EngineStatusResp(status="RUNNING",running=True,threads=s["threads"])

@engine_router.post("/stop", response_model=EngineStatusResp, summary="Parar engine")
async def stop_engine():
    engine_service.stop()
    return EngineStatusResp(status="STOPPED",running=False)

@engine_router.get("/status", response_model=EngineStatusResp, summary="Status do engine")
async def engine_status():
    s=engine_service.get_status()
    return EngineStatusResp(status="RUNNING" if s["running"] else "STOPPED",
                            running=s["running"],threads=s["threads"])

# ── Compute / Binary ──────────────────────────────────────────────────────────
@compute_router.post("/binary", summary="Operação binária (14 tipos)")
async def binary(req: BinaryReq):
    t0=_t(); r=compute_service.binary(req.operation,req.value_a,req.value_b)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"binary")
    return {**r,"operation":req.operation,"value_a":req.value_a,"value_b":req.value_b,
            "timestamp":datetime.utcnow().isoformat()}

# ── Compute / Matrix ──────────────────────────────────────────────────────────
@compute_router.post("/matrix", summary="Criar e analisar matriz (10 tipos)")
async def matrix(req: MatrixReq):
    t0=_t(); r=compute_service.matrix(req.operation,req.rows,req.cols)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"matrix")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@compute_router.post("/matrix/multiply", summary="Multiplicar duas matrizes")
async def matrix_mul(req: MatrixMulReq):
    t0=_t(); r=compute_service.matrix_mul(req.a,req.b)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"matrix")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@compute_router.post("/matrix/solve", summary="Resolver sistema linear Ax=b")
async def matrix_solve(req: MatrixSolveReq):
    t0=_t(); r=compute_service.matrix_solve(req.a,req.b)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"matrix")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Compute / Quantum ──────────────────────────────────────────────────────────
@compute_router.post("/quantum", summary="Simulação quântica (12 portas)")
async def quantum(req: QuantumReq):
    t0=_t()
    gates=[g.model_dump() for g in req.gates] if req.gates else None
    r=compute_service.quantum(req.qubits,req.operation,gates)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"quantum")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Compute / Sort ────────────────────────────────────────────────────────────
@compute_router.post("/sort", summary="Ordenar lista (8 algoritmos)")
async def sort(req: SortReq):
    t0=_t(); r=compute_service.sort(req.data,req.algorithm)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"sort")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@compute_router.post("/sort/benchmark", summary="Benchmark de todos os algoritmos")
async def sort_benchmark(req: SortBenchmarkReq):
    t0=_t(); r=compute_service.sort_benchmark(req.data)
    metrics_service.record(_lat(t0),True,"sort")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Compute / Prime ───────────────────────────────────────────────────────────
@compute_router.post("/prime", summary="Operações com números primos")
async def prime(req: PrimeReq):
    t0=_t(); r=compute_service.prime(req.operation,req.n,req.limit)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"prime")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Compute / Sequence ────────────────────────────────────────────────────────
@compute_router.post("/sequence", summary="Sequências numéricas (Fibonacci, Collatz, Pascal...)")
async def sequence(req: SequenceReq):
    t0=_t(); r=compute_service.sequence(req.operation,req.n)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"sequence")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Compute / Statistics ───────────────────────────────────────────────────────
@compute_router.post("/stats", summary="Análise estatística de dataset")
async def stats(req: StatsReq):
    t0=_t(); r=compute_service.stats_analyze(req.data)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"stats")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@compute_router.post("/stats/correlation", summary="Correlação de Pearson entre dois datasets")
async def correlation(req: CorrelationReq):
    t0=_t(); r=compute_service.stats_correlation(req.x,req.y)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"stats")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@compute_router.post("/stats/histogram", summary="Histograma de frequência")
async def histogram(req: HistogramReq):
    t0=_t(); r=compute_service.stats_histogram(req.data,req.bins)
    metrics_service.record(_lat(t0),True,"stats")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Hash ──────────────────────────────────────────────────────────────────────
@hash_router.post("", summary="Calcular hash (10 algoritmos)")
async def hash_data(req: HashReq):
    t0=_t(); r=compute_service.hash(req.data,req.algorithm)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"hash")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@hash_router.post("/all", summary="Calcular com TODOS os algoritmos")
async def hash_all(req: HashReq):
    t0=_t(); r=compute_service.hash_all(req.data)
    metrics_service.record(_lat(t0),True,"hash")
    return {"results":r,"algorithms":list(r.keys()),"timestamp":datetime.utcnow().isoformat()}

@hash_router.post("/verify", summary="Verificar hash")
async def hash_verify(req: HashVerifyReq):
    t0=_t(); r=compute_service.hash_verify(req.data,req.expected,req.algorithm)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"hash")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

@hash_router.post("/hmac", summary="Calcular HMAC")
async def hmac(req: HmacReq):
    t0=_t(); r=compute_service.hmac(req.key,req.data,req.algorithm)
    if _err(r): raise HTTPException(400,r["error"])
    metrics_service.record(_lat(t0),True,"hash")
    return {**r,"timestamp":datetime.utcnow().isoformat()}

# ── Metrics ───────────────────────────────────────────────────────────────────
@metrics_router.get("", summary="Métricas agregadas (latência, CPU, RAM, módulos)")
async def get_metrics():
    return {**metrics_service.snapshot(),"timestamp":datetime.utcnow().isoformat()}

@metrics_router.post("/stress", response_model=StressResp, summary="Stress test paralelo")
async def stress(req: StressReq, bg: BackgroundTasks):
    bg.add_task(compute_service.stress,req.threads,req.operations_per_thread,metrics_service)
    return StressResp(status="RUNNING",threads=req.threads,
                      total_operations=req.threads*req.operations_per_thread)

# ── Health ────────────────────────────────────────────────────────────────────
@health_router.get("/health", response_model=HealthResp, summary="Health check completo")
async def health():
    m=metrics_service.snapshot()
    return HealthResp(status="HEALTHY",components={
        "engine":"RUNNING" if engine_service.is_running else "STOPPED",
        "binary":"OK","matrix":"OK","quantum":"OK","hash":"OK",
        "sort":"OK","prime":"OK","sequence":"OK","stats":"OK","metrics":"OK",
        "cpu_pct":str(m["cpu_percent"]),"memory_mb":str(round(m["memory_bytes"]/1024**2,1)),
        "uptime_s":str(m["uptime_seconds"])})

@health_router.get("/ping", summary="Ping simples")
async def ping():
    return {"status":"OK","timestamp":datetime.utcnow().isoformat()}
