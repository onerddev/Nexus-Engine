#pragma once

#include <cstdint>
#include <atomic>
#include <thread>
#include <vector>
#include <memory>
#include <chrono>
#include <functional>

namespace nexus {

/**
 * @class CoreEngine
 * @brief Main orchestrator for high-performance computational tasks
 * 
 * Manages thread pools, task scheduling, and performance monitoring
 * for the NexusEngine Omega system.
 * 
 * Thread-safe: Yes (lock-free design with std::atomic)
 * Features:
 * - Auto-scaling thread pool
 * - Task queue management
 * - Real-time metrics collection
 * - Latency tracking
 */
class CoreEngine {
public:
    enum class EngineState {
        STOPPED = 0,
        RUNNING = 1,
        PAUSED = 2,
        ERROR = 3
    };

    struct EngineConfig {
        uint32_t num_threads = std::thread::hardware_concurrency();
        uint32_t queue_capacity = 100000;
        uint32_t batch_size = 1024;
        std::chrono::milliseconds timeout = std::chrono::milliseconds(5000);
        bool enable_metrics = true;
        bool enable_logging = true;
    };

    struct EngineMetrics {
        std::atomic<uint64_t> processed_items{0};
        std::atomic<uint64_t> failed_items{0};
        std::atomic<uint64_t> total_latency_us{0};
        std::atomic<uint32_t> current_queue_size{0};
        std::atomic<uint32_t> active_threads{0};
        std::atomic<double> avg_throughput{0.0};
        std::atomic<double> cpu_usage{0.0};
    };

    explicit CoreEngine(const EngineConfig& config = EngineConfig());
    ~CoreEngine();

    // Engine lifecycle
    void start();
    void stop();
    void pause();
    void resume();
    
    // State management
    EngineState get_state() const;
    bool is_running() const;
    
    // Metrics
    const EngineMetrics& get_metrics() const;
    void reset_metrics();
    
    // Configuration
    void set_config(const EngineConfig& config);
    const EngineConfig& get_config() const;

private:
    EngineConfig config_;
    EngineMetrics metrics_;
    std::atomic<EngineState> state_{EngineState::STOPPED};
    std::vector<std::thread> worker_threads_;
    
    void worker_loop();
    void update_metrics();
};

} // namespace nexus
