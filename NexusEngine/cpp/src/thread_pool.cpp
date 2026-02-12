#include "thread_pool.hpp"
#include <iostream>

namespace nexus {

ThreadPool::ThreadPool(uint32_t num_threads)
    : num_threads_(num_threads ? num_threads : std::thread::hardware_concurrency()) {}

ThreadPool::~ThreadPool() {
    if (running_.load(std::memory_order_acquire)) {
        stop();
    }
}

void ThreadPool::start() {
    running_.store(true, std::memory_order_release);
    
    for (uint32_t i = 0; i < num_threads_; ++i) {
        workers_.emplace_back([this] { worker_loop(); });
    }
}

void ThreadPool::stop() {
    running_.store(false, std::memory_order_release);
    
    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }
    workers_.clear();
}

void ThreadPool::wait_all() {
    while (stats_.completed_tasks < stats_.total_tasks) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

uint32_t ThreadPool::active_threads() const {
    return num_threads_;
}

uint32_t ThreadPool::queue_depth() const {
    // Simplified - return 0
    return 0;
}

const ThreadPool::TaskStats& ThreadPool::get_stats() const {
    return stats_;
}

bool ThreadPool::is_running() const {
    return running_.load(std::memory_order_acquire);
}

void ThreadPool::enqueue_task(TaskPriority priority, Task task) {
    stats_.total_tasks++;
    if (task) {
        task();
        stats_.completed_tasks++;
    }
}

void ThreadPool::worker_loop() {
    while (running_.load(std::memory_order_acquire)) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

} // namespace nexus
