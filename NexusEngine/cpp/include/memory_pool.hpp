#pragma once

#include <cstdint>
#include <memory>
#include <vector>
#include <atomic>
#include <mutex>

namespace nexus {

/**
 * @class MemoryPool
 * @brief Thread-safe memory pool allocator with mutex protection
 * 
 * Features:
 * - Pre-allocated fixed-size memory blocks
 * - Thread-safe allocation/deallocation via mutex
 * - No fragmentation (pre-allocated fixed blocks)
 * - Constant-time allocation (O(n) in worst case, O(1) amortized)
 * - Statistics tracking with atomic operations
 * 
 * Thread-safety:
 *   - allocate()/deallocate() protected by mutex
 *   - Statistics safe with atomics
 *   - Not lock-free (uses std::mutex)
 * 
 * WARNING:
 *   - Allocations may block if pool exhausted
 *   - Deallocating non-owned pointer causes undefined behavior
 *   - Block size is fixed at construction time
 */
class MemoryPool {
public:
    struct PoolStats {
        uint64_t total_blocks = 0;
        uint64_t allocated_blocks = 0;
        uint64_t free_blocks = 0;
        uint64_t total_allocations = 0;
        uint64_t total_deallocations = 0;
    };

    /**
     * Construct memory pool with fixed block size and count.
     * 
     * @param block_size Size of each memory block in bytes
     * @param num_blocks Total number of blocks to pre-allocate
     * @throws std::bad_alloc if memory allocation fails
     */
    explicit MemoryPool(uint32_t block_size, uint32_t num_blocks);
    ~MemoryPool();
    
    // Prevent copying (allocator handles ownership)
    MemoryPool(const MemoryPool&) = delete;
    MemoryPool& operator=(const MemoryPool&) = delete;
    
    // Memory allocation
    /**
     * Allocate a block of memory.
     * Thread-safe.
     * 
     * @return Pointer to allocated block, or nullptr if exhausted
     */
    void* allocate();
    
    /**
     * Deallocate a previously allocated block.
     * Thread-safe.
     * 
     * WARNING: Calling with non-owned pointer has undefined behavior.
     * 
     * @param ptr Pointer returned by allocate()
     */
    void deallocate(void* ptr);
    
    // Statistics (atomic, thread-safe)
    [[nodiscard]] PoolStats get_stats() const;
    [[nodiscard]] bool has_free_blocks() const;
    [[nodiscard]] double utilization_percent() const;
    
    // Configuration
    [[nodiscard]] uint32_t block_size() const;
    [[nodiscard]] uint32_t max_blocks() const;

private:
    struct Block {
        uint8_t* data = nullptr;
        std::atomic<bool> allocated{false};  // Now atomic-protected
    };

    uint32_t block_size_;
    std::vector<Block> blocks_;
    std::mutex blocks_mutex_;  // Protects blocks_ vector access
    std::atomic<uint32_t> free_count_;
    std::atomic<uint64_t> total_allocations_{0};
    std::atomic<uint64_t> total_deallocations_{0};
};

/**
 * @class ObjectPool
 * @brief Generic object pool for pre-constructed objects
 */
template <typename T>
class ObjectPool {
public:
    explicit ObjectPool(uint32_t capacity);
    ~ObjectPool();
    
    template <typename... Args>
    std::shared_ptr<T> allocate(Args&&... args);
    
    [[nodiscard]] uint32_t available() const;
    [[nodiscard]] uint32_t in_use() const;

private:
    std::vector<std::shared_ptr<T>> available_;
    std::atomic<uint32_t> in_use_count_{0};
};

} // namespace nexus
