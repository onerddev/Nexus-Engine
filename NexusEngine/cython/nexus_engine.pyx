# cython: language_level=3
# distutils: language = c++
# distutils: sources = cpp/src/core_engine.cpp, cpp/src/binary_processor.cpp, cpp/src/quantum_simulator.cpp, cpp/src/matrix_engine.cpp, cpp/src/metrics_collector.cpp, cpp/src/hash_engine.cpp, cpp/src/memory_pool.cpp, cpp/src/plugin_loader.cpp, cpp/src/simd_ops.cpp, cpp/src/thread_pool.cpp
# distutils: include_dirs = cpp/include

from libc.stdint cimport uint32_t, uint64_t, int64_t
from libcpp.vector cimport vector
from libcpp.string cimport string
from libcpp cimport bool
from cython.parallel cimport prange

# Declare C++ classes
cdef extern from "core_engine.hpp" namespace "nexus":
    cdef cppclass CoreEngine:
        enum EngineState:
            STOPPED
            RUNNING
            PAUSED
            ERROR
        
        CoreEngine() except +
        void start() except +
        void stop() except +
        void pause() except +
        void resume() except +
        EngineState get_state() except +
        bool is_running() except +

cdef extern from "binary_processor.hpp" namespace "nexus":
    cdef cppclass BinaryProcessor:
        @staticmethod
        uint64_t xor_op(uint64_t a, uint64_t b) except +
        @staticmethod
        uint64_t and_op(uint64_t a, uint64_t b) except +
        @staticmethod
        uint64_t or_op(uint64_t a, uint64_t b) except +
        @staticmethod
        uint64_t not_op(uint64_t a) except +
        @staticmethod
        uint32_t popcount(uint64_t a) except +
        @staticmethod
        uint32_t hamming_distance(uint64_t a, uint64_t b) except +
        @staticmethod
        string to_binary_string(uint64_t value, size_t width) except +
        @staticmethod
        uint64_t from_binary_string(const string& binary) except +

cdef extern from "quantum_simulator.hpp" namespace "nexus":
    cdef cppclass QuantumSimulator:
        QuantumSimulator(uint32_t num_qubits) except +
        void initialize_ground_state() except +
        void initialize_superposition() except +
        void initialize_random() except +
        void apply_hadamard(uint32_t qubit_idx) except +
        double get_probability_zero(uint32_t qubit_idx) except +
        double get_probability_one(uint32_t qubit_idx) except +

cdef extern from "matrix_engine.hpp" namespace "nexus":
    cdef cppclass MatrixEngine:
        @staticmethod
        vector[vector[double]] create_zeros(uint32_t rows, uint32_t cols) except +
        @staticmethod
        vector[vector[double]] create_ones(uint32_t rows, uint32_t cols) except +
        @staticmethod
        vector[vector[double]] create_identity(uint32_t size) except +
        @staticmethod
        vector[vector[double]] create_random(uint32_t rows, uint32_t cols, double min_val, double max_val) except +

cdef extern from "metrics_collector.hpp" namespace "nexus":
    cdef cppclass MetricsCollector:
        MetricsCollector() except +
        void record_operation(uint64_t latency_us, bool success) except +
        string to_json() except +
        void reset() except +

cdef extern from "hash_engine.hpp" namespace "nexus":
    cdef cppclass HashEngine:
        @staticmethod
        string sha256(const string& data) except +
        @staticmethod
        string xxhash64(const string& data, uint64_t seed) except +

# Python wrapper classes

cdef class PyCoreEngine:
    """Python wrapper for CoreEngine"""
    cdef CoreEngine* c_engine
    
    def __cinit__(self):
        self.c_engine = new CoreEngine()
    
    def __dealloc__(self):
        if self.c_engine != NULL:
            del self.c_engine
    
    def start(self):
        """Start the engine"""
        with nogil:
            self.c_engine.start()
    
    def stop(self):
        """Stop the engine"""
        with nogil:
            self.c_engine.stop()
    
    def pause(self):
        """Pause the engine"""
        with nogil:
            self.c_engine.pause()
    
    def resume(self):
        """Resume the engine"""
        with nogil:
            self.c_engine.resume()
    
    def is_running(self):
        """Check if engine is running"""
        with nogil:
            result = self.c_engine.is_running()
        return result


cdef class PyBinaryProcessor:
    """Python wrapper for BinaryProcessor"""
    
    @staticmethod
    def xor(uint64_t a, uint64_t b):
        """XOR operation"""
        with nogil:
            result = BinaryProcessor.xor_op(a, b)
        return result
    
    @staticmethod
    def and_(uint64_t a, uint64_t b):
        """AND operation"""
        with nogil:
            result = BinaryProcessor.and_op(a, b)
        return result
    
    @staticmethod
    def or_(uint64_t a, uint64_t b):
        """OR operation"""
        with nogil:
            result = BinaryProcessor.or_op(a, b)
        return result
    
    @staticmethod
    def not_(uint64_t a):
        """NOT operation"""
        with nogil:
            result = BinaryProcessor.not_op(a)
        return result
    
    @staticmethod
    def popcount(uint64_t a):
        """Count set bits"""
        with nogil:
            result = BinaryProcessor.popcount(a)
        return result
    
    @staticmethod
    def hamming_distance(uint64_t a, uint64_t b):
        """Hamming distance between two integers"""
        with nogil:
            result = BinaryProcessor.hamming_distance(a, b)
        return result
    
    @staticmethod
    def to_binary(uint64_t value, uint32_t width=64):
        """Convert integer to binary string"""
        cdef string binary
        with nogil:
            binary = BinaryProcessor.to_binary_string(value, width)
        return binary.decode('utf-8')
    
    @staticmethod
    def from_binary(str binary):
        """Convert binary string to integer"""
        cdef string c_binary = binary.encode('utf-8')
        cdef uint64_t result
        with nogil:
            result = BinaryProcessor.from_binary_string(c_binary)
        return result


cdef class PyQuantumSimulator:
    """Python wrapper for QuantumSimulator"""
    cdef QuantumSimulator* c_sim
    
    def __cinit__(self, uint32_t num_qubits=8):
        self.c_sim = new QuantumSimulator(num_qubits)
    
    def __dealloc__(self):
        if self.c_sim != NULL:
            del self.c_sim
    
    def initialize_ground(self):
        """Initialize to ground state"""
        with nogil:
            self.c_sim.initialize_ground_state()
    
    def initialize_superposition(self):
        """Initialize to superposition"""
        with nogil:
            self.c_sim.initialize_superposition()
    
    def initialize_random(self):
        """Initialize to random state"""
        with nogil:
            self.c_sim.initialize_random()
    
    def apply_hadamard(self, uint32_t qubit_idx):
        """Apply Hadamard gate"""
        with nogil:
            self.c_sim.apply_hadamard(qubit_idx)
    
    def probability_zero(self, uint32_t qubit_idx):
        """Get probability of measuring 0"""
        cdef double prob
        with nogil:
            prob = self.c_sim.get_probability_zero(qubit_idx)
        return prob
    
    def probability_one(self, uint32_t qubit_idx):
        """Get probability of measuring 1"""
        cdef double prob
        with nogil:
            prob = self.c_sim.get_probability_one(qubit_idx)
        return prob


cdef class PyMatrixEngine:
    """Python wrapper for MatrixEngine"""
    
    @staticmethod
    def zeros(uint32_t rows, uint32_t cols):
        """Create zero matrix"""
        cdef vector[vector[double]] c_matrix
        with nogil:
            c_matrix = MatrixEngine.create_zeros(rows, cols)
        return [[c_matrix[i][j] for j in range(cols)] for i in range(rows)]
    
    @staticmethod
    def ones(uint32_t rows, uint32_t cols):
        """Create ones matrix"""
        cdef vector[vector[double]] c_matrix
        with nogil:
            c_matrix = MatrixEngine.create_ones(rows, cols)
        return [[c_matrix[i][j] for j in range(cols)] for i in range(rows)]
    
    @staticmethod
    def identity(uint32_t size):
        """Create identity matrix"""
        cdef vector[vector[double]] c_matrix
        with nogil:
            c_matrix = MatrixEngine.create_identity(size)
        return [[c_matrix[i][j] for j in range(size)] for i in range(size)]
    
    @staticmethod
    def random(uint32_t rows, uint32_t cols, double min_val=0.0, double max_val=1.0):
        """Create random matrix"""
        cdef vector[vector[double]] c_matrix
        with nogil:
            c_matrix = MatrixEngine.create_random(rows, cols, min_val, max_val)
        return [[c_matrix[i][j] for j in range(cols)] for i in range(rows)]


cdef class PyMetricsCollector:
    """Python wrapper for MetricsCollector"""
    cdef MetricsCollector* c_collector
    
    def __cinit__(self):
        self.c_collector = new MetricsCollector()
    
    def __dealloc__(self):
        if self.c_collector != NULL:
            del self.c_collector
    
    def record(self, uint64_t latency_us, bool success=True):
        """Record operation"""
        with nogil:
            self.c_collector.record_operation(latency_us, success)
    
    def to_json(self):
        """Get metrics as JSON"""
        cdef string json_str
        with nogil:
            json_str = self.c_collector.to_json()
        return json_str.decode('utf-8')
    
    def reset(self):
        """Reset metrics"""
        with nogil:
            self.c_collector.reset()


cdef class PyHashEngine:
    """Python wrapper for HashEngine"""
    
    @staticmethod
    def sha256(str data):
        """SHA256 hash"""
        cdef string c_data = data.encode('utf-8')
        cdef string result
        with nogil:
            result = HashEngine.sha256(c_data)
        return result.decode('utf-8')
    
    @staticmethod
    def xxhash64(str data, uint64_t seed=0):
        """XXHash64"""
        cdef string c_data = data.encode('utf-8')
        cdef string result
        with nogil:
            result = HashEngine.xxhash64(c_data, seed)
        return result.decode('utf-8')
