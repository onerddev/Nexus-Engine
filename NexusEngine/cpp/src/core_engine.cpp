#include "core_engine.hpp"
#include "metrics_collector.hpp"
#include <iostream>
#include <chrono>

namespace nexus {

CoreEngine::CoreEngine(const EngineConfig& config)
    : config_(config), state_(EngineState::STOPPED) {
    if (config_.enable_logging) {
        std::cout << "[CoreEngine] Initialized with " << config_.num_threads 
                  << " threads, queue capacity: " << config_.queue_capacity << std::endl;
    }
}

CoreEngine::~CoreEngine() {
    if (is_running()) {
        stop();
    }
}

void CoreEngine::start() {
    if (state_ != EngineState::STOPPED) {
        return;
    }
    
    state_ = EngineState::RUNNING;
    
    for (uint32_t i = 0; i < config_.num_threads; ++i) {
        worker_threads_.emplace_back([this] { worker_loop(); });
    }
    
    metrics_.active_threads = config_.num_threads;
    
    if (config_.enable_logging) {
        std::cout << "[CoreEngine] Started with " << config_.num_threads << " workers" << std::endl;
    }
}

void CoreEngine::stop() {
    EngineState expected = EngineState::RUNNING;
    if (!state_.compare_exchange_strong(expected, EngineState::STOPPED)) {
        expected = EngineState::PAUSED;
        state_.compare_exchange_strong(expected, EngineState::STOPPED);
    }
    
    for (auto& t : worker_threads_) {
        if (t.joinable()) {
            t.join();
        }
    }
    worker_threads_.clear();
    metrics_.active_threads = 0;
    
    if (config_.enable_logging) {
        std::cout << "[CoreEngine] Stopped. Total items processed: " 
                  << metrics_.processed_items << std::endl;
    }
}

void CoreEngine::pause() {
    state_ = EngineState::PAUSED;
}

void CoreEngine::resume() {
    if (state_ == EngineState::PAUSED) {
        state_ = EngineState::RUNNING;
    }
}

CoreEngine::EngineState CoreEngine::get_state() const {
    return state_.load(std::memory_order_acquire);
}

bool CoreEngine::is_running() const {
    return state_.load(std::memory_order_acquire) == EngineState::RUNNING;
}

const CoreEngine::EngineMetrics& CoreEngine::get_metrics() const {
    return metrics_;
}

void CoreEngine::reset_metrics() {
    metrics_.processed_items = 0;
    metrics_.failed_items = 0;
    metrics_.total_latency_us = 0;
    metrics_.current_queue_size = 0;
    metrics_.avg_throughput = 0.0;
}

void CoreEngine::set_config(const EngineConfig& config) {
    if (!is_running()) {
        config_ = config;
    }
}

const CoreEngine::EngineConfig& CoreEngine::get_config() const {
    return config_;
}

void CoreEngine::worker_loop() {
    while (state_ != EngineState::STOPPED) {
        if (state_ == EngineState::PAUSED) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;
        }
        
        // Simulate work
        std::this_thread::sleep_for(std::chrono::microseconds(1));
        
        auto start = std::chrono::high_resolution_clock::now();
        
        // Increment processing counter
        metrics_.processed_items.fetch_add(1, std::memory_order_release);
        
        auto end = std::chrono::high_resolution_clock::now();
        auto latency_us = std::chrono::duration_cast<std::chrono::microseconds>(
            end - start).count();
        
        metrics_.total_latency_us.fetch_add(latency_us, std::memory_order_release);
    }
}

void CoreEngine::update_metrics() {
    auto processed = metrics_.processed_items.load(std::memory_order_acquire);
    auto total_latency_us = metrics_.total_latency_us.load(std::memory_order_acquire);
    
    if (processed > 0) {
        metrics_.avg_throughput = processed / 
            (total_latency_us / 1000000.0 + 0.001);
    }
}

} // namespace nexus
