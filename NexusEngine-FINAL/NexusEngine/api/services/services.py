"""Services — NexusEngine Omega v3.0 | Autor: Emanuel Felipe"""
import time, threading, random, logging
from typing import Optional, List
from datetime import datetime
from .engine_core import (BinaryProcessor, MatrixEngine, QuantumSimulator,
    HashEngine, SortEngine, PrimeEngine, SequenceEngine, StatsEngine, MetricsCollector)

logger = logging.getLogger(__name__)

class EngineService:
    def __init__(self):
        self.is_running=False; self.threads=0; self.started_at=None
        self._workers=[]; self._stop_event=threading.Event()

    def start(self,threads:int=4)->bool:
        try:
            self._stop_event.clear()
            self.is_running=True; self.threads=threads
            self.started_at=datetime.utcnow()
            logger.info(f"Engine iniciado — {threads} workers")
            return True
        except Exception as e:
            logger.error(f"Falha ao iniciar: {e}"); return False

    def stop(self)->bool:
        self._stop_event.set(); self.is_running=False
        logger.info("Engine parado"); return True

    def get_status(self)->dict:
        return {"running":self.is_running,"threads":self.threads,
                "started_at":self.started_at.isoformat() if self.started_at else None,
                "timestamp":datetime.utcnow().isoformat()}


class ComputeService:
    def __init__(self):
        self.bp=BinaryProcessor(); self.mx=MatrixEngine()
        self.ha=HashEngine(); self.so=SortEngine()
        self.pr=PrimeEngine(); self.sq=SequenceEngine()
        self.st=StatsEngine()
        logger.info("ComputeService pronto")

    def binary(self,op,a,b=0):      return self.bp.compute(op,a,b)
    def matrix(self,op,r,c):        return self.mx.compute(op,r,c)
    def matrix_mul(self,a,b):       return self.mx.multiply(a,b)
    def matrix_solve(self,a,b):     return self.mx.solve(a,b)

    def quantum(self,qubits,init,gates=None,qi=None):
        t0=time.perf_counter()
        try:
            qs=QuantumSimulator(qubits)
            {"ground":qs.init_ground,"superposition":qs.init_superposition,
             "random":qs.init_random,"bell":qs.init_bell,"ghz":qs.init_ghz}.get(init,qs.init_ground)()
            applied=[]
            gate_map={"H":qs.H,"X":qs.X,"Y":qs.Y,"Z":qs.Z,"S":qs.S,"T":qs.T,
                      "Sdg":qs.Sdg,"CNOT":None,"CZ":None,"SWAP":None,
                      "Rx":qs.Rx,"Ry":qs.Ry,"Rz":qs.Rz}
            for g in (gates or []):
                gn=g.get("gate",""); gq=g.get("qubit",0); gt=g.get("target",1); th=g.get("theta",0)
                if gn in ("CNOT","CZ","SWAP"):
                    {"CNOT":qs.CNOT,"CZ":qs.CZ,"SWAP":qs.SWAP}[gn](gq,gt); applied.append(f"{gn}({gq},{gt})")
                elif gn in ("Rx","Ry","Rz"):
                    gate_map[gn](gq,th); applied.append(f"{gn}({gq},θ={round(th,3)})")
                elif gn in gate_map:
                    gate_map[gn](gq); applied.append(f"{gn}({gq})")
            lat=(time.perf_counter()-t0)*1e6
            return {"qubits":qubits,"init":init,"gates_applied":applied,
                    "probabilities":qs.probabilities(),"state_vector":qs.statevector(),
                    "entropy_bits":round(qs.entropy(),8),"latency_us":round(lat,4)}
        except Exception as e: return {"error":str(e)}

    def hash(self,data,algo):       return self.ha.hash(data,algo)
    def hash_all(self,data):        return self.ha.hash_all(data)
    def hash_verify(self,data,exp,algo): return self.ha.verify(data,exp,algo)
    def hmac(self,key,data,algo):   return self.ha.hmac(key,data,algo)

    def sort(self,data,algo):       return self.so.sort(data,algo)
    def sort_benchmark(self,data):  return self.so.benchmark(data)

    def prime(self,op,n,limit=1000):return self.pr.compute(op,n,limit)
    def sequence(self,op,n):        return self.sq.compute(op,n)

    def stats_analyze(self,data):   return self.st.analyze(data)
    def stats_correlation(self,x,y):return self.st.correlation(x,y)
    def stats_histogram(self,data,bins):return self.st.histogram(data,bins)

    def stress(self, threads:int, ops_per:int, metrics:'MetricsService'):
        def worker():
            for i in range(ops_per):
                t0=time.perf_counter()
                self.bp.compute("xor",i*0xFF,i^0xAA)
                metrics.record((time.perf_counter()-t0)*1e6,True,"stress")
        ts=[threading.Thread(target=worker,daemon=True) for _ in range(threads)]
        for t in ts: t.start()
        for t in ts: t.join()


class MetricsService:
    def __init__(self): self._c=MetricsCollector()
    def record(self,lat,success=True,module=""): self._c.record(lat,success,module)
    def snapshot(self): return self._c.snapshot()

engine_service  = EngineService()
compute_service = ComputeService()
metrics_service = MetricsService()
