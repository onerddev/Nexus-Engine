#include "memory_pool.hpp"
#include <iostream>

namespace nexus {

MemoryPool::MemoryPool(uint32_t block_size, uint32_t num_blocks)
    : block_size_(block_size), free_count_(num_blocks) {
    
    blocks_.resize(num_blocks);
    
    for (uint32_t i = 0; i < num_blocks; ++i) {
        blocks_[i].data = new uint8_t[block_size];
        blocks_[i].allocated = false;
    }
}

MemoryPool::~MemoryPool() {
    for (auto& block : blocks_) {
        delete[] block.data;
    }
}

void* MemoryPool::allocate() {
    if (has_free_blocks()) {
        for (auto& block : blocks_) {
            if (!block.allocated) {
                block.allocated = true;
                free_count_.fetch_sub(1, std::memory_order_release);
                total_allocations_.fetch_add(1, std::memory_order_release);
                return block.data;
            }
        }
    }
    return nullptr;
}

void MemoryPool::deallocate(void* ptr) {
    for (auto& block : blocks_) {
        if (block.data == ptr && block.allocated) {
            block.allocated = false;
            free_count_.fetch_add(1, std::memory_order_release);
            total_deallocations_.fetch_add(1, std::memory_order_release);
            return;
        }
    }
}

MemoryPool::PoolStats MemoryPool::get_stats() const {
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
    return (1.0 - static_cast<double>(free) / blocks_.size()) * 100.0;
}

uint32_t MemoryPool::block_size() const {
    return block_size_;
}

uint32_t MemoryPool::max_blocks() const {
    return blocks_.size();
}

} // namespace nexus
