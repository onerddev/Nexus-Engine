"""
Core services for NexusEngine API
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EngineService:
    """Engine lifecycle management"""
    
    def __init__(self):
        self.engine = None
        self.is_running = False
    
    def start(self, threads: int = 4):
        """Start engine"""
        try:
            # Import Cython bindings if available
            try:
                import nexus_engine
                self.engine = nexus_engine.PyCoreEngine()
                self.engine.start()
            except ImportError:
                logger.warning("Cython bindings not available, using mock")
            
            self.is_running = True
            logger.info(f"Engine started with {threads} threads")
            return True
        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            return False
    
    def stop(self):
        """Stop engine"""
        try:
            if self.engine:
                self.engine.stop()
            self.is_running = False
            logger.info("Engine stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop engine: {e}")
            return False
    
    def get_status(self):
        """Get engine status"""
        return {
            "running": self.is_running,
            "timestamp": datetime.utcnow().isoformat()
        }


class ComputeService:
    """Computation services"""
    
    def __init__(self):
        self.bp = None
        self.qsim = None
        self.matrix = None
        self.hash_engine = None
        
        # Try to import Cython bindings
        try:
            import nexus_engine
            self.bp = nexus_engine.PyBinaryProcessor()
            self.matrix = nexus_engine.PyMatrixEngine()
            self.hash_engine = nexus_engine.PyHashEngine()
        except ImportError:
            logger.warning("Cython bindings not available")
    
    def binary_operation(self, operation: str, value_a: int, value_b: Optional[int] = None):
        """Perform binary operation"""
        try:
            if not self.bp:
                return {"error": "Binary processor not available"}
            
            if operation == "xor":
                result = self.bp.xor(value_a, value_b or 0)
            elif operation == "and":
                result = self.bp.and_(value_a, value_b or 0)
            elif operation == "or":
                result = self.bp.or_(value_a, value_b or 0)
            elif operation == "not":
                result = self.bp.not_(value_a)
            else:
                return {"error": f"Unknown operation: {operation}"}
            
            return {
                "result": result,
                "result_binary": self.bp.to_binary(result) if hasattr(self.bp, 'to_binary') else bin(result)
            }
        except Exception as e:
            logger.error(f"Binary operation failed: {e}")
            return {"error": str(e)}
    
    def matrix_compute(self, operation: str, rows: int, cols: int):
        """Perform matrix computation"""
        try:
            if not self.matrix:
                return {"error": "Matrix engine not available"}
            
            if operation == "zeros":
                matrix = self.matrix.zeros(rows, cols)
            elif operation == "ones":
                matrix = self.matrix.ones(rows, cols)
            elif operation == "identity":
                matrix = self.matrix.identity(rows)
            elif operation == "random":
                matrix = self.matrix.random(rows, cols)
            else:
                return {"error": f"Unknown operation: {operation}"}
            
            # Return sample
            sample = [[matrix[i][j] for j in range(min(3, len(matrix[0])))] 
                      for i in range(min(3, len(matrix)))]
            
            return {
                "operation": operation,
                "rows": rows,
                "cols": cols,
                "sample": sample
            }
        except Exception as e:
            logger.error(f"Matrix computation failed: {e}")
            return {"error": str(e)}
    
    def quantum_simulate(self, qubits: int, operation: str, qubit_index: Optional[int] = None):
        """Perform quantum simulation"""
        try:
            import nexus_engine
            qsim = nexus_engine.PyQuantumSimulator(qubits)
            
            if operation == "ground":
                qsim.initialize_ground()
            elif operation == "superposition":
                qsim.initialize_superposition()
            elif operation == "random":
                qsim.initialize_random()
            else:
                qsim.initialize_ground()
            
            # Get probabilities for first few qubits
            probs = []
            for i in range(min(qubits, 8)):
                p0 = qsim.probability_zero(i)
                p1 = qsim.probability_one(i)
                probs.append({
                    "qubit": i,
                    "p0": round(p0, 4),
                    "p1": round(p1, 4)
                })
            
            return {"probabilities": probs}
        except Exception as e:
            logger.error(f"Quantum simulation failed: {e}")
            return {"error": str(e)}


class MetricsService:
    """Metrics collection and reporting"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.total_operations = 0
        self.total_errors = 0
        self.latencies = []
    
    def record_operation(self, latency_us: float, success: bool = True):
        """Record operation metric"""
        self.total_operations += 1
        if not success:
            self.total_errors += 1
        self.latencies.append(latency_us)
    
    def get_aggregated_metrics(self):
        """Get aggregated metrics"""
        if not self.latencies:
            return {
                "total_operations": 0,
                "total_errors": 0,
                "error_rate": 0.0,
                "latency_us": {
                    "p50": 0, "p95": 0, "p99": 0, "p999": 0, "mean": 0, "min": 0, "max": 0
                },
                "throughput_ops_sec": 0,
                "queue_size": 0,
                "cpu_usage_percent": 0,
                "memory_bytes": 0,
                "uptime_seconds": 0
            }
        
        sorted_latencies = sorted(self.latencies)
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_operations": self.total_operations,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / self.total_operations if self.total_operations > 0 else 0,
            "latency_us": {
                "p50": sorted_latencies[len(sorted_latencies) // 2],
                "p95": sorted_latencies[int(len(sorted_latencies) * 0.95)],
                "p99": sorted_latencies[int(len(sorted_latencies) * 0.99)],
                "p999": sorted_latencies[-1],
                "mean": sum(self.latencies) / len(self.latencies),
                "min": min(self.latencies),
                "max": max(self.latencies)
            },
            "throughput_ops_sec": self.total_operations / uptime if uptime > 0 else 0,
            "queue_size": 0,
            "cpu_usage_percent": 0,
            "memory_bytes": 0,
            "uptime_seconds": int(uptime)
        }


# Global service instances
engine_service = EngineService()
compute_service = ComputeService()
metrics_service = MetricsService()
