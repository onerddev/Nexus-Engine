"""NexusEngine Omega v3.0 — API Principal | Autor: Emanuel Felipe"""
import logging, os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from api.routers.routes    import engine_router,compute_router,hash_router,metrics_router,health_router
from api.routers.dashboard import ui_router
from api.middleware.middleware import RequestIDMiddleware,LoggingMiddleware,RateLimitMiddleware,CORSMiddleware
from api.services.services import engine_service

load_dotenv()
logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
logger=logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    logger.info("="*58)
    logger.info("  NexusEngine Omega v3.0 — por Emanuel Felipe")
    logger.info("  Dashboard : http://localhost:8000/dashboard")
    logger.info("  Swagger   : http://localhost:8000/docs")
    logger.info("  Módulos   : binary|matrix|quantum|hash|sort|prime|sequence|stats")
    logger.info("="*58)
    yield
    engine_service.stop()

app=FastAPI(
    title="NexusEngine Omega",
    description="""## Motor Computacional de Alta Performance

**Autor:** Emanuel Felipe | **Versão:** 3.0.0 | **Licença:** MIT

### Módulos
| Módulo | Ops | Descrição |
|---|---|---|
| **Binary** | 14 | XOR, AND, OR, NOT, NAND, NOR, XNOR, SHL, SHR, ROL, ROR, popcount, parity, reverse |
| **Matrix** | 10 | zeros, ones, identity, random, hilbert, magic, vandermonde, toeplitz + análise |
| **Quantum** | 12 | H, X, Y, Z, S, T, Sdg, CNOT, CZ, SWAP, Rx, Ry, Rz + vetor de estado |
| **Hash** | 10 | md5, sha1, sha224, sha256, sha384, sha512, sha3_256, sha3_512, blake2b, blake2s |
| **Sort** | 8 | bubble, insertion, selection, merge, quick, heap, shell, counting + benchmark |
| **Prime** | 5 | is_prime, sieve, factorize, goldbach, nth_prime |
| **Sequence** | 5 | fibonacci, collatz, pascal, lucas, tribonacci |
| **Statistics** | 3 | analyze, correlation, histogram |
""",
    version="3.0.0",lifespan=lifespan,docs_url="/docs",redoc_url="/redoc",
    contact={"name":"Emanuel Felipe","url":"https://github.com/onerddev"},
    license_info={"name":"MIT"})

app.add_middleware(CORSMiddleware)
app.add_middleware(RateLimitMiddleware,rps=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

for r in [engine_router,compute_router,hash_router,metrics_router,health_router,ui_router]:
    app.include_router(r)

@app.exception_handler(Exception)
async def global_err(req:Request,exc:Exception):
    logger.error(f"Erro: {exc}",exc_info=True)
    return JSONResponse(status_code=500,content={"error":"Erro interno","detail":str(exc)})

@app.get("/",include_in_schema=False)
async def root(): return RedirectResponse("/dashboard")

@app.get("/ready",include_in_schema=False)
async def ready(): return {"status":"ready"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run("api.main:app",host=os.getenv("API_HOST","0.0.0.0"),
                port=int(os.getenv("API_PORT","8000")),
                reload=os.getenv("API_RELOAD","false").lower()=="true")
