#pragma once

#include <cstdint>
#include <thread>
#include <vector>
#include <functional>
#include <future>
#include <memory>
#include <atomic>
#include <queue>
#include <mutex>
#include <condition_variable>

namespace nexus {

/**
 * @class ThreadPool
 * @brief Simple thread pool with task queue and synchronization
 * 
 * Features:
 * - Fixed number of worker threads
 * - Task queue with blocking enqueue
 * - Support for returning results via std::future
 * - Configurable task priority
 * - Statistics tracking
 * 
 * Thread-safety:
 * - Thread-safe task submission via mutex-protected queue
 * - Thread-safe shutdown
 * - NOT lock-free (uses std::mutex + std::condition_variable)
 * 
 * Trade-offs:
 * - Simple, easy to reason about
 * - Using mutex (not lock-free) for clarity
 * - No work-stealing (simpler implementation)
 * - No auto-scaling (fixed thread count)
 * 
 * Limitations:
 * - Fixed thread count (no dynamic adjustment)
 * - Blocking enqueue if queue is full (requires size limit)
 * - No priority queue implementation (simplified)
 */
class ThreadPool {
public:
    enum class TaskPriority {
        LOW = 0,
        NORMAL = 1,
        HIGH = 2
    };

    struct TaskStats {
        std::atomic<uint64_t> total_tasks{0};
        std::atomic<uint64_t> completed_tasks{0};
        std::atomic<uint64_t> failed_tasks{0};
        std::atomic<double> avg_task_time_us{0.0};
    };

    /**
     * Create thread pool with specified number of worker threads.
     * 
     * @param num_threads Number of worker threads (default: hardware concurrency)
     */
    explicit ThreadPool(uint32_t num_threads = 0);
    ~ThreadPool();
    
    // Prevent copying
    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;
    
    // Thread management
    /**
     * Start worker threads.
     * Must be called before submitting tasks.
     */
    void start();
    
    /**
     * Stop worker threads and wait for remaining tasks.
     */
    void stop();
    
    /**
     * Block until all submitted tasks are completed.
     */
    void wait_all();
    
    // Task submission
    /**
     * Submit a task with normal priority.
     * Returns a future to get the result.
     * 
     * @param fn Function to execute
     * @param args Arguments to function
     * @return Future for result
     */
    template <typename Func, typename... Args>
    auto submit(Func&& fn, Args&&... args) {
        return submit_with_priority(TaskPriority::NORMAL, 
                                   std::forward<Func>(fn), 
                                   std::forward<Args>(args)...);
    }
    
    /**
     * Submit a task with specified priority.
     * Higher priority tasks are executed first.
     * 
     * WARNING: Priority is advisory only (FIFO within priority level).
     */
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
    
    struct PrioritizedTask {
        TaskPriority priority;
        Task task;
        
        // For priority queue (higher priority = lower value)
        bool operator<(const PrioritizedTask& other) const {
            return priority < other.priority;
        }
    };
    
    uint32_t num_threads_;
    std::vector<std::thread> workers_;
    std::priority_queue<PrioritizedTask> task_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;
    std::atomic<bool> running_{false};
    TaskStats stats_;
    
    void enqueue_task(TaskPriority priority, Task task);
    void worker_loop();
};

} // namespace nexus
