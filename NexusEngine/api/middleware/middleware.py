"""
Middleware for NexusEngine API
"""

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)


class RequestIDMiddleware:
    """Add request ID to all requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware:
    """Log all HTTP requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} "
            f"({process_time:.2f}ms) - {request.client.host if request.client else 'unknown'}"
        )
        
        return response


class RateLimitMiddleware:
    """Simple rate limiting"""
    
    def __init__(self, app, requests_per_second: int = 1000):
        self.app = app
        self.requests_per_second = requests_per_second
        self.request_times = {}
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        if client_ip not in self.request_times:
            self.request_times[client_ip] = []
        
        # Remove old requests
        self.request_times[client_ip] = [
            t for t in self.request_times[client_ip] 
            if current_time - t < 1.0
        ]
        
        if len(self.request_times[client_ip]) >= self.requests_per_second:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"}
            )
        
        self.request_times[client_ip].append(current_time)
        return await call_next(request)


class CORSMiddleware:
    """CORS handling"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return Response(
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                }
            )
        
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
