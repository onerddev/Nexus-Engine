/* NexusEngine Main Executable */

#include <iostream>
#include <memory>
#include "core_engine.hpp"
#include "binary_processor.hpp"
#include "quantum_simulator.hpp"
#include "matrix_engine.hpp"

int main(int argc, char** argv) {
    std::cout << "NexusEngine Omega - Ultra Low Latency Hybrid Computational Engine\n";
    std::cout << "Version 1.0.0 (C++20)\n\n";
    
    try {
        // Initialize core engine
        nexus::CoreEngine::EngineConfig config;
        config.num_threads = 16;
        config.queue_capacity = 100000;
        config.enable_metrics = true;
        config.enable_logging = true;
        
        auto engine = std::make_unique<nexus::CoreEngine>(config);
        
        // Start engine
        std::cout << "Starting engine...\n";
        engine->start();
        
        // Run demonstrations
        std::cout << "\n=== Binary Operations ===\n";
        uint64_t a = 0b11110000;
        uint64_t b = 0b10101010;
        
        auto xor_result = nexus::BinaryProcessor::xor_op(a, b);
        std::cout << "XOR: " << nexus::BinaryProcessor::to_binary_string(xor_result, 8) << "\n";
        
        auto popcount = nexus::BinaryProcessor::popcount(a);
        std::cout << "Popcount(a): " << popcount << "\n";
        
        std::cout << "\n=== Quantum Simulation ===\n";
        nexus::QuantumSimulator sim(4);
        sim.initialize_superposition();
        sim.apply_hadamard(0);
        
        std::cout << "Qubit 0 probability |0>: " << sim.get_probability_zero(0) << "\n";
        std::cout << "Qubit 0 probability |1>: " << sim.get_probability_one(0) << "\n";
        
        std::cout << "\n=== Matrix Operations ===\n";
        auto identity = nexus::MatrixEngine::create_identity(3);
        auto trace = nexus::MatrixEngine::trace(identity);
        std::cout << "Trace of 3x3 identity: " << trace << "\n";
        
        // Get metrics
        std::cout << "\n=== Engine Metrics ===\n";
        const auto& metrics = engine->get_metrics();
        std::cout << "Processed items: " << metrics.processed_items << "\n";
        std::cout << "Average throughput: " << metrics.avg_throughput << " ops/sec\n";
        
        // Cleanup
        std::cout << "\nShutting down...\n";
        engine->stop();
        
        std::cout << "✓ All systems operational\n";
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}
