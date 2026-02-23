#include "memory_pool.hpp"
#include <iostream>
#include <stdexcept>

namespace nexus {

MemoryPool::MemoryPool(uint32_t block_size, uint32_t num_blocks)
    : block_size_(block_size), free_count_(num_blocks) {
    
    if (block_size == 0 || num_blocks == 0) {
        throw std::invalid_argument("block_size and num_blocks must be > 0");
    }
    
    blocks_.resize(num_blocks);
    
    try {
        for (uint32_t i = 0; i < num_blocks; ++i) {
            blocks_[i].data = new uint8_t[block_size];
            blocks_[i].allocated.store(false, std::memory_order_release);
        }
    } catch (...) {
        // Cleanup on failure
        for (auto& block : blocks_) {
            if (block.data != nullptr) {
                delete[] block.data;
            }
        }
        throw;
    }
}

MemoryPool::~MemoryPool() {
    std::lock_guard<std::mutex> lock(blocks_mutex_);
    for (auto& block : blocks_) {
        delete[] block.data;
        block.data = nullptr;
    }
}

void* MemoryPool::allocate() {
    std::lock_guard<std::mutex> lock(blocks_mutex_);
    
    if (!has_free_blocks()) {
        return nullptr;
    }
    
    // Linear search for free block (O(n) but blocks_ is typically small)
    for (auto& block : blocks_) {
        if (!block.allocated.load(std::memory_order_acquire)) {
            block.allocated.store(true, std::memory_order_release);
            free_count_.fetch_sub(1, std::memory_order_release);
            total_allocations_.fetch_add(1, std::memory_order_release);
            return block.data;
        }
    }
    
    return nullptr;  // Should not reach here if has_free_blocks was accurate
}

void MemoryPool::deallocate(void* ptr) {
    if (ptr == nullptr) {
        return;  // Safe no-op
    }
    
    std::lock_guard<std::mutex> lock(blocks_mutex_);
    
    for (auto& block : blocks_) {
        if (block.data == ptr && block.allocated.load(std::memory_order_acquire)) {
            block.allocated.store(false, std::memory_order_release);
            free_count_.fetch_add(1, std::memory_order_release);
            total_deallocations_.fetch_add(1, std::memory_order_release);
            return;
        }
    }
    
    // Warning: pointer not owned by this pool
    // In production, consider throwing or logging error
}

MemoryPool::PoolStats MemoryPool::get_stats() const {
    std::lock_guard<std::mutex> lock(blocks_mutex_);
    
    PoolStats stats;
    stats.total_blocks = blocks_.size();
    stats.free_blocks = free_count_.load(std::memory_order_acquire);
    stats.allocated_blocks = stats.total_blocks - stats.free_blocks;
    stats.total_allocations = total_allocations_.load(std::memory_order_acquire);
    stats.total_deallocations = total_deallocations_.load(std::memory_order_acquire);
    return stats;
}

bool MemoryPool::has_free_blocks() const {
    return free_count_.load(std::memory_order_acquire) > 0;
}

double MemoryPool::utilization_percent() const {
    uint32_t free = free_count_.load(std::memory_order_acquire);
    if (blocks_.empty()) {
        return 0.0;
    }
    return (1.0 - static_cast<double>(free) / blocks_.size()) * 100.0;
}

uint32_t MemoryPool::block_size() const {
    return block_size_;
}

uint32_t MemoryPool::max_blocks() const {
    return blocks_.size();
}

} // namespace nexus
