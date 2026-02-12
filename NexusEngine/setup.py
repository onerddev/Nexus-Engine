from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os

# Get the C++ source files
cpp_dir = os.path.join(os.path.dirname(__file__), '..', 'cpp')
sources = [
    os.path.join(cpp_dir, 'src', 'core_engine.cpp'),
    os.path.join(cpp_dir, 'src', 'binary_processor.cpp'),
    os.path.join(cpp_dir, 'src', 'quantum_simulator.cpp'),
    os.path.join(cpp_dir, 'src', 'matrix_engine.cpp'),
    os.path.join(cpp_dir, 'src', 'metrics_collector.cpp'),
    os.path.join(cpp_dir, 'src', 'hash_engine.cpp'),
    os.path.join(cpp_dir, 'src', 'memory_pool.cpp'),
    os.path.join(cpp_dir, 'src', 'plugin_loader.cpp'),
    os.path.join(cpp_dir, 'src', 'simd_ops.cpp'),
    os.path.join(cpp_dir, 'src', 'thread_pool.cpp'),
]

extensions = [
    Extension(
        "nexus_engine",
        ["cython/nexus_engine.pyx"] + sources,
        include_dirs=[os.path.join(cpp_dir, 'include')],
        language="c++",
        extra_compile_args=["-O3", "-march=native", "-pthread"],
        extra_link_args=["-pthread", "-fopenmp"],
    )
]

setup(
    name="NexusEngine",
    version="1.0.0",
    description="Ultra Low Latency Hybrid Computational Engine",
    author="NexusEngine Team",
    ext_modules=cythonize(extensions, language_level="3"),
)
