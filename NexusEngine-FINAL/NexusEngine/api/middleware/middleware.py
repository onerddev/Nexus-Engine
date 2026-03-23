"""Middleware — NexusEngine Omega v3.0 | Autor: Emanuel Felipe"""
import time, uuid, logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, req, call_next):
        rid=str(uuid.uuid4()); req.state.request_id=rid
        resp=await call_next(req)
        resp.headers["X-Request-ID"]=rid
        resp.headers["X-Powered-By"]="NexusEngine/3.0"
        return resp

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, req, call_next):
        t0=time.perf_counter(); resp=await call_next(req)
        ms=(time.perf_counter()-t0)*1000
        logger.info(f"{req.method} {req.url.path} → {resp.status_code} ({ms:.1f}ms)")
        return resp

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,rps=1000):
        super().__init__(app); self._rps=rps; self._hits={}
    async def dispatch(self, req, call_next):
        ip=req.client.host if req.client else "?"; now=time.time()
        self._hits[ip]=[t for t in self._hits.get(ip,[]) if now-t<1.0]
        if len(self._hits[ip])>=self._rps:
            return JSONResponse(status_code=429,content={"error":"Rate limit exceeded"})
        self._hits[ip].append(now)
        return await call_next(req)

class CORSMiddleware(BaseHTTPMiddleware):
    H={"Access-Control-Allow-Origin":"*",
       "Access-Control-Allow-Methods":"GET,POST,PUT,DELETE,OPTIONS,PATCH",
       "Access-Control-Allow-Headers":"Content-Type,Authorization,X-Request-ID",
       "Access-Control-Max-Age":"86400"}
    async def dispatch(self, req, call_next):
        if req.method=="OPTIONS": return Response(headers=self.H)
        resp=await call_next(req)
        for k,v in self.H.items(): resp.headers[k]=v
        return resp
