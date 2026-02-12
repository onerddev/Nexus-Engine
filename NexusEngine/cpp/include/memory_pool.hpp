#pragma once

#include <cstdint>
#include <memory>
#include <vector>
#include <atomic>

namespace nexus {

/**
 * @class MemoryPool
 * @brief High-performance memory pool allocator
 * 
 * Features:
 * - Pre-allocated memory blocks
 * - Zero fragmentation
 * - Thread-safe allocation/deallocation
 * - Alignment guarantees
 * - Statistics tracking
 * 
 * Thread-safe: Yes
 * Performance: Constant-time allocation/deallocation
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

    explicit MemoryPool(uint32_t block_size, uint32_t num_blocks);
    ~MemoryPool();
    
    // Memory allocation
    void* allocate();
    void deallocate(void* ptr);
    
    // Statistics
    [[nodiscard]] PoolStats get_stats() const;
    [[nodiscard]] bool has_free_blocks() const;
    [[nodiscard]] double utilization_percent() const;
    
    // Configuration
    [[nodiscard]] uint32_t block_size() const;
    [[nodiscard]] uint32_t max_blocks() const;

private:
    struct Block {
        uint8_t* data = nullptr;
        bool allocated = false;
    };

    uint32_t block_size_;
    std::vector<Block> blocks_;
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
