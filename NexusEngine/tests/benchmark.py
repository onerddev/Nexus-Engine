"""
Benchmark system for NexusEngine
Comprehensive performance benchmarking suite
"""

import time
import json
import statistics
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import sys


@dataclass
class BenchmarkResult:
    """Benchmark result data"""
    name: str
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    throughput_ops_sec: float
    latencies: List[float]
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate latency statistics"""
        if not self.latencies:
            return {}
        
        sorted_latencies = sorted(self.latencies)
        return {
            "min_us": min(self.latencies),
            "max_us": max(self.latencies),
            "mean_us": statistics.mean(self.latencies),
            "median_us": statistics.median(self.latencies),
            "stdev_us": statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0,
            "p50_us": sorted_latencies[len(self.latencies)//2],
            "p95_us": sorted_latencies[int(len(self.latencies)*0.95)],
            "p99_us": sorted_latencies[int(len(self.latencies)*0.99)],
            "p999_us": sorted_latencies[-1],
        }


class BenchmarkSuite:
    """Comprehensive benchmark suite"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def benchmark_binary_xor(self, iterations: int = 1000000) -> BenchmarkResult:
        """Benchmark XOR operation"""
        latencies = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                op_start = time.time()
                # Simulate XOR operation
                result = (i ^ (i >> 1))
                op_time = (time.time() - op_start) * 1e6  # Convert to microseconds
                latencies.append(op_time)
                successful += 1
            except Exception:
                failed += 1
        
        duration = time.time() - start_time
        
        result = BenchmarkResult(
            name="binary_xor",
            duration_seconds=duration,
            total_operations=iterations,
            successful_operations=successful,
            failed_operations=failed,
            throughput_ops_sec=iterations / duration,
            latencies=latencies
        )
        
        self.results.append(result)
        return result
    
    def benchmark_matrix_multiply(self, size: int = 256, iterations: int = 100) -> BenchmarkResult:
        """Benchmark matrix multiplication"""
        import numpy as np
        
        latencies = []
        successful = 0
        failed = 0
        
        # Create test matrices
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                op_start = time.time()
                result = np.dot(a, b)
                op_time = (time.time() - op_start) * 1e6
                latencies.append(op_time)
                successful += 1
            except Exception:
                failed += 1
        
        duration = time.time() - start_time
        
        result = BenchmarkResult(
            name=f"matrix_multiply_{size}x{size}",
            duration_seconds=duration,
            total_operations=iterations,
            successful_operations=successful,
            failed_operations=failed,
            throughput_ops_sec=iterations / duration,
            latencies=latencies
        )
        
        self.results.append(result)
        return result
    
    def benchmark_hash_sha256(self, iterations: int = 10000) -> BenchmarkResult:
        """Benchmark SHA256 hashing"""
        import hashlib
        
        latencies = []
        successful = 0
        failed = 0
        
        data = b"NexusEngine benchmark data for SHA256 hashing"
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                op_start = time.time()
                hashlib.sha256(data + str(i).encode()).hexdigest()
                op_time = (time.time() - op_start) * 1e6
                latencies.append(op_time)
                successful += 1
            except Exception:
                failed += 1
        
        duration = time.time() - start_time
        
        result = BenchmarkResult(
            name="sha256_hash",
            duration_seconds=duration,
            total_operations=iterations,
            successful_operations=successful,
            failed_operations=failed,
            throughput_ops_sec=iterations / duration,
            latencies=latencies
        )
        
        self.results.append(result)
        return result
    
    def benchmark_quantum_simulation(self, qubits: int = 8, iterations: int = 1000) -> BenchmarkResult:
        """Benchmark quantum simulation"""
        latencies = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                op_start = time.time()
                # Simulate quantum operations
                self._simulate_quantum_circuit(qubits)
                op_time = (time.time() - op_start) * 1e6
                latencies.append(op_time)
                successful += 1
            except Exception:
                failed += 1
        
        duration = time.time() - start_time
        
        result = BenchmarkResult(
            name=f"quantum_simulate_{qubits}qubits",
            duration_seconds=duration,
            total_operations=iterations,
            successful_operations=successful,
            failed_operations=failed,
            throughput_ops_sec=iterations / duration,
            latencies=latencies
        )
        
        self.results.append(result)
        return result
    
    def _simulate_quantum_circuit(self, qubits: int):
        """Simulate simple quantum circuit"""
        import numpy as np
        # Initialize quantum state
        state = np.zeros(2**qubits, dtype=complex)
        state[0] = 1.0  # |0...0⟩
        
        # Apply Hadamard gates
        for q in range(min(qubits, 4)):
            state = self._hadamard_gate(state, q, qubits)
    
    def _hadamard_gate(self, state, qubit, total_qubits):
        """Apply Hadamard gate"""
        import numpy as np
        new_state = state.copy()
        for i in range(len(state)):
            if (i >> qubit) & 1 == 0:
                new_state[i] = state[i] / np.sqrt(2)
        return new_state
    
    def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print("NexusEngine Benchmark Suite")
        print("=" * 60)
        
        benchmarks = [
            ("Binary XOR (1M ops)", lambda: self.benchmark_binary_xor(1000000)),
            ("Matrix Multiply 256x256 (100 ops)", lambda: self.benchmark_matrix_multiply(256, 100)),
            ("SHA256 Hash (10k ops)", lambda: self.benchmark_hash_sha256(10000)),
            ("Quantum Simulation 8-qubit (1k ops)", lambda: self.benchmark_quantum_simulation(8, 1000)),
        ]
        
        for name, benchmark_func in benchmarks:
            print(f"\n{name}...")
            result = benchmark_func()
            self._print_result(result)
        
        self._print_summary()
    
    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result"""
        stats = result.get_stats()
        
        print(f"  Total Operations: {result.total_operations:,}")
        print(f"  Successful: {result.successful_operations:,}")
        print(f"  Failed: {result.failed_operations:,}")
        print(f"  Duration: {result.duration_seconds:.3f}s")
        print(f"  Throughput: {result.throughput_ops_sec:,.0f} ops/sec")
        print(f"  Latency:")
        print(f"    Min: {stats['min_us']:.2f}µs")
        print(f"    Mean: {stats['mean_us']:.2f}µs")
        print(f"    Median: {stats['median_us']:.2f}µs")
        print(f"    p95: {stats['p95_us']:.2f}µs")
        print(f"    p99: {stats['p99_us']:.2f}µs")
        print(f"    Max: {stats['max_us']:.2f}µs")
    
    def _print_summary(self):
        """Print summary"""
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        
        total_ops = sum(r.total_operations for r in self.results)
        total_time = sum(r.duration_seconds for r in self.results)
        
        print(f"Total Operations: {total_ops:,}")
        print(f"Total Time: {total_time:.3f}s")
        print(f"Overall Throughput: {total_ops/total_time:,.0f} ops/sec")
    
    def export_results(self, filename: str = "benchmark_results.json"):
        """Export results to JSON"""
        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "benchmarks": []
        }
        
        for result in self.results:
            stats = result.get_stats()
            export_data["benchmarks"].append({
                "name": result.name,
                "duration_seconds": result.duration_seconds,
                "total_operations": result.total_operations,
                "successful_operations": result.successful_operations,
                "failed_operations": result.failed_operations,
                "throughput_ops_sec": result.throughput_ops_sec,
                "statistics": stats
            })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\nResults exported to {filename}")


if __name__ == "__main__":
    suite = BenchmarkSuite()
    suite.run_all_benchmarks()
    suite.export_results("reports/benchmark_results.json")
