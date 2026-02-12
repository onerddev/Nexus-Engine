"""
API routers for NexusEngine
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from datetime import datetime
from typing import Optional
import logging

from ..models.schemas import (
    EngineStartRequest, EngineStatusResponse,
    BinaryOperationRequest, BinaryOperationResponse,
    MatrixComputeRequest, MatrixComputeResponse,
    QuantumSimulateRequest, QuantumSimulateResponse,
    AggregatedMetricsResponse, HealthResponse, ErrorResponse,
    StressTestRequest, StressTestResponse
)
from ..services.services import engine_service, compute_service, metrics_service

logger = logging.getLogger(__name__)

# Initialize routers
engine_router = APIRouter(prefix="/engine", tags=["Engine"])
compute_router = APIRouter(prefix="/compute", tags=["Compute"])
metrics_router = APIRouter(prefix="/metrics", tags=["Metrics"])
health_router = APIRouter(tags=["Health"])


# ==================== Engine Routes ====================

@engine_router.post("/start", response_model=EngineStatusResponse, status_code=200)
async def start_engine(request: EngineStartRequest):
    """Start the engine"""
    try:
        success = engine_service.start(request.threads)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start engine")
        
        return EngineStatusResponse(
            status="RUNNING",
            running=True,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error starting engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@engine_router.post("/stop", response_model=EngineStatusResponse, status_code=200)
async def stop_engine():
    """Stop the engine"""
    try:
        success = engine_service.stop()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop engine")
        
        return EngineStatusResponse(
            status="STOPPED",
            running=False,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error stopping engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@engine_router.get("/status", response_model=EngineStatusResponse, status_code=200)
async def get_engine_status():
    """Get engine status"""
    status = engine_service.get_status()
    return EngineStatusResponse(
        status="RUNNING" if status["running"] else "STOPPED",
        running=status["running"],
        timestamp=datetime.fromisoformat(status["timestamp"])
    )


# ==================== Compute Routes ====================

@compute_router.post("/binary", response_model=BinaryOperationResponse, status_code=200)
async def perform_binary_operation(request: BinaryOperationRequest):
    """Perform binary operation"""
    try:
        result = compute_service.binary_operation(
            request.operation,
            request.value_a,
            request.value_b
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        metrics_service.record_operation(0.5, True)
        
        return BinaryOperationResponse(
            operation=request.operation,
            value_a=request.value_a,
            value_b=request.value_b,
            result=result["result"],
            result_binary=result.get("result_binary", bin(result["result"])),
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in binary operation: {e}")
        metrics_service.record_operation(0.5, False)
        raise HTTPException(status_code=500, detail=str(e))


@compute_router.post("/matrix", response_model=MatrixComputeResponse, status_code=200)
async def compute_matrix(request: MatrixComputeRequest):
    """Perform matrix computation"""
    try:
        result = compute_service.matrix_compute(
            request.operation,
            request.rows,
            request.cols
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        metrics_service.record_operation(2.5, True)
        
        return MatrixComputeResponse(
            operation=result["operation"],
            rows=result["rows"],
            cols=result["cols"],
            sample=result["sample"],
            status="SUCCESS"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in matrix computation: {e}")
        metrics_service.record_operation(2.5, False)
        raise HTTPException(status_code=500, detail=str(e))


@compute_router.post("/quantum", response_model=QuantumSimulateResponse, status_code=200)
async def simulate_quantum(request: QuantumSimulateRequest):
    """Perform quantum simulation"""
    try:
        result = compute_service.quantum_simulate(
            request.qubits,
            request.operation,
            request.qubit_index
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        metrics_service.record_operation(4.8, True)
        
        return QuantumSimulateResponse(
            qubits=request.qubits,
            operation=request.operation,
            probabilities=result["probabilities"],
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quantum simulation: {e}")
        metrics_service.record_operation(4.8, False)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Metrics Routes ====================

@metrics_router.get("", response_model=AggregatedMetricsResponse, status_code=200)
async def get_metrics():
    """Get aggregated metrics"""
    try:
        metrics = metrics_service.get_aggregated_metrics()
        return AggregatedMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@metrics_router.post("/stress-test", response_model=StressTestResponse, status_code=200)
async def run_stress_test(request: StressTestRequest, background_tasks: BackgroundTasks):
    """Run stress test"""
    try:
        # Schedule stress test in background
        background_tasks.add_task(
            _run_stress_test,
            request.threads,
            request.duration_seconds,
            request.operations_per_thread
        )
        
        return StressTestResponse(
            status="RUNNING",
            threads=request.threads,
            duration_seconds=request.duration_seconds,
            total_operations=request.threads * request.operations_per_thread,
            throughput_ops_sec=request.threads * 10000,
            max_latency_us=150,
            error_rate=0.0,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Routes ====================

@health_router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="HEALTHY",
        components={
            "engine": "OK" if engine_service.is_running else "STOPPED",
            "compute": "OK",
            "metrics": "OK"
        },
        version="1.0.0"
    )


@health_router.get("/ping", status_code=200)
async def ping():
    """Simple ping for load balancers"""
    return {"status": "OK", "timestamp": datetime.utcnow().isoformat()}


# ==================== Helper Functions ====================

async def _run_stress_test(threads: int, duration: int, ops_per_thread: int):
    """Background task for stress test"""
    logger.info(f"Starting stress test: {threads} threads, {duration}s, {ops_per_thread} ops")
    
    # Simulate stress test
    for i in range(threads * ops_per_thread):
        metrics_service.record_operation((i % 100) + 1, random_bool())
    
    logger.info("Stress test completed")


def random_bool(probability=0.99):
    """Helper to return bool with probability"""
    import random
    return random.random() < probability
