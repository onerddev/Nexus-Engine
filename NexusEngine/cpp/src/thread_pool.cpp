#include "thread_pool.hpp"
#include <iostream>
#include <chrono>

namespace nexus {

ThreadPool::ThreadPool(uint32_t num_threads)
    : num_threads_(num_threads ? num_threads : std::thread::hardware_concurrency()) {
    if (num_threads_ == 0) {
        num_threads_ = 4;  // Fallback
    }
}

ThreadPool::~ThreadPool() {
    if (running_.load(std::memory_order_acquire)) {
        stop();
    }
}

void ThreadPool::start() {
    if (running_.exchange(true, std::memory_order_release)) {
        return;  // Already running
    }
    
    for (uint32_t i = 0; i < num_threads_; ++i) {
        workers_.emplace_back([this] { worker_loop(); });
    }
}

void ThreadPool::stop() {
    running_.store(false, std::memory_order_release);
    queue_cv_.notify_all();  // Wake all workers
    
    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }
    workers_.clear();
}

void ThreadPool::wait_all() {
    // Wait for all tasks to complete
    // This is a simple busy wait - could be improved with condition variable
    while (stats_.total_tasks.load() > stats_.completed_tasks.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

uint32_t ThreadPool::active_threads() const {
    return num_threads_;
}

uint32_t ThreadPool::queue_depth() const {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    return task_queue_.size();
}

const ThreadPool::TaskStats& ThreadPool::get_stats() const {
    return stats_;
}

bool ThreadPool::is_running() const {
    return running_.load(std::memory_order_acquire);
}

void ThreadPool::enqueue_task(TaskPriority priority, Task task) {
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        task_queue_.push({priority, std::move(task)});
        stats_.total_tasks.fetch_add(1, std::memory_order_release);
    }
    queue_cv_.notify_one();  // Wake one worker
}

void ThreadPool::worker_loop() {
    while (running_.load(std::memory_order_acquire)) {
        PrioritizedTask pTask;
        
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            
            // Wait for task or shutdown
            queue_cv_.wait(lock, [this] {
                return !task_queue_.empty() || 
                       !running_.load(std::memory_order_acquire);
            });
            
            if (!running_.load(std::memory_order_acquire) && task_queue_.empty()) {
                break;
            }
            
            if (task_queue_.empty()) {
                continue;
            }
            
            pTask = std::move(const_cast<PrioritizedTask&>(task_queue_.top()));
            task_queue_.pop();
        }
        
        // Execute task outside lock
        if (pTask.task) {
            try {
                auto start = std::chrono::high_resolution_clock::now();
                pTask.task();
                auto end = std::chrono::high_resolution_clock::now();
                
                stats_.completed_tasks.fetch_add(1, std::memory_order_release);
                
                // Update average latency (simplified)
                auto duration_us = std::chrono::duration_cast<std::chrono::microseconds>(
                    end - start).count();
                // Note: This is approximate, not true average
                stats_.avg_task_time_us.store(duration_us, std::memory_order_release);
            } catch (...) {
                stats_.failed_tasks.fetch_add(1, std::memory_order_release);
            }
        }
    }
}

} // namespace nexus
