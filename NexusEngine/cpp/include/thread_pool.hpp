#pragma once

#include <cstdint>
#include <thread>
#include <vector>
#include <functional>
#include <future>
#include <memory>
#include <atomic>

namespace nexus {

/**
 * @class ThreadPool
 * @brief Efficient work-stealing thread pool with auto-scaling
 * 
 * Features:
 * - Work-stealing algorithm for load balancing
 * - Auto-scaling based on queue depth
 * - Task priority support
 * - Future-based task results
 * 
 * Thread-safe: Yes
 * Performance: Minimal contention, cache-friendly
 */
class ThreadPool {
public:
    enum class TaskPriority {
        LOW = 0,
        NORMAL = 1,
        HIGH = 2
    };

    struct TaskStats {
        uint64_t total_tasks = 0;
        uint64_t completed_tasks = 0;
        uint64_t failed_tasks = 0;
        double avg_task_time_us = 0.0;
    };

    explicit ThreadPool(uint32_t num_threads = 0);
    ~ThreadPool();
    
    // Thread management
    void start();
    void stop();
    void wait_all();
    
    // Task submission
    template <typename Func, typename... Args>
    auto submit(Func&& fn, Args&&... args) {
        return submit_with_priority(TaskPriority::NORMAL, std::forward<Func>(fn), std::forward<Args>(args)...);
    }
    
    template <typename Func, typename... Args>
    auto submit_with_priority(TaskPriority priority, Func&& fn, Args&&... args) {
        using RetType = std::invoke_result_t<Func, Args...>;
        auto promise = std::make_shared<std::promise<RetType>>();
        auto future = promise->get_future();
        
        auto task = [promise, fn = std::forward<Func>(fn), 
                     args = std::make_tuple(std::forward<Args>(args)...)]() mutable {
            try {
                if constexpr (std::is_void_v<RetType>) {
                    std::apply(fn, args);
                    promise->set_value();
                } else {
                    promise->set_value(std::apply(fn, args));
                }
            } catch (...) {
                promise->set_exception(std::current_exception());
            }
        };
        
        enqueue_task(priority, std::move(task));
        return future;
    }
    
    // State queries
    [[nodiscard]] uint32_t active_threads() const;
    [[nodiscard]] uint32_t queue_depth() const;
    [[nodiscard]] const TaskStats& get_stats() const;
    [[nodiscard]] bool is_running() const;

private:
    using Task = std::function<void()>;
    
    uint32_t num_threads_;
    std::vector<std::thread> workers_;
    std::atomic<bool> running_{false};
    TaskStats stats_;
    
    void enqueue_task(TaskPriority priority, Task task);
    void worker_loop();
};

} // namespace nexus
