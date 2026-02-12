"""
Main FastAPI application for NexusEngine
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

from api.routers.routes import (
    engine_router, compute_router, metrics_router, health_router
)
from api.middleware.middleware import (
    RequestIDMiddleware, LoggingMiddleware, RateLimitMiddleware, CORSMiddleware
)
from api.services.services import engine_service

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("NexusEngine API starting up...")
    yield
    # Shutdown
    logger.info("NexusEngine API shutting down...")
    engine_service.stop()


# Create FastAPI app
app = FastAPI(
    title="NexusEngine Omega API",
    description="Ultra Low Latency Hybrid Computational Engine - Headless Control Layer",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(CORSMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_second=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# Include routers
app.include_router(engine_router)
app.include_router(compute_router)
app.include_router(metrics_router)
app.include_router(health_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url.path)
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "NexusEngine Omega",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "api_version": "v1"
    }


# Ready endpoint
@app.get("/ready")
async def ready():
    """Readiness check for orchestration"""
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 4))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        reload=os.getenv("API_RELOAD", "false").lower() == "true"
    )
