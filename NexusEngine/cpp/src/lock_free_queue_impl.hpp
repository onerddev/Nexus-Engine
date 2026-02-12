#include "lock_free_queue.hpp"

namespace nexus {

template <typename T>
LockFreeQueue<T>::LockFreeQueue(uint32_t capacity) 
    : capacity_(capacity), mask_(capacity - 1) {
    buffer_ = std::make_unique<Node[]>(capacity);
}

template <typename T>
LockFreeQueue<T>::~LockFreeQueue() = default;

template <typename T>
bool LockFreeQueue<T>::enqueue(const T& value) {
    uint32_t tail = tail_.load(std::memory_order_acquire);
    uint32_t next_tail = (tail + 1) & mask_;
    
    if (next_tail == head_.load(std::memory_order_acquire)) {
        return false;  // Queue full
    }
    
    buffer_[tail].data = value;
    tail_.store(next_tail, std::memory_order_release);
    return true;
}

template <typename T>
bool LockFreeQueue<T>::dequeue(T& value) {
    uint32_t head = head_.load(std::memory_order_acquire);
    
    if (head == tail_.load(std::memory_order_acquire)) {
        return false;  // Queue empty
    }
    
    value = buffer_[head].data;
    uint32_t next_head = (head + 1) & mask_;
    head_.store(next_head, std::memory_order_release);
    return true;
}

template <typename T>
bool LockFreeQueue<T>::try_enqueue(const T& value) {
    return enqueue(value);
}

template <typename T>
bool LockFreeQueue<T>::try_dequeue(T& value) {
    return dequeue(value);
}

template <typename T>
uint32_t LockFreeQueue<T>::size() const {
    uint32_t h = head_.load(std::memory_order_acquire);
    uint32_t t = tail_.load(std::memory_order_acquire);
    return (t - h) & mask_;
}

template <typename T>
bool LockFreeQueue<T>::empty() const {
    return head_.load(std::memory_order_acquire) == 
           tail_.load(std::memory_order_acquire);
}

template <typename T>
bool LockFreeQueue<T>::full() const {
    uint32_t next_tail = (tail_.load(std::memory_order_acquire) + 1) & mask_;
    return next_tail == head_.load(std::memory_order_acquire);
}

template <typename T>
uint32_t LockFreeQueue<T>::capacity() const {
    return capacity_;
}

template <typename T>
double LockFreeQueue<T>::fill_ratio() const {
    return static_cast<double>(size()) / capacity_;
}

template <typename T>
void LockFreeQueue<T>::clear() {
    head_.store(0, std::memory_order_release);
    tail_.store(0, std::memory_order_release);
}


// RingBuffer implementation
template <typename T>
RingBuffer<T>::RingBuffer(uint32_t capacity)
    : buffer_(capacity), capacity_(capacity) {}

template <typename T>
bool RingBuffer<T>::push_back(const T& value) {
    uint32_t tail = tail_.load(std::memory_order_acquire);
    uint32_t next_tail = (tail + 1) % capacity_;
    
    if (next_tail == head_.load(std::memory_order_acquire)) {
        return false;  // Full
    }
    
    buffer_[tail] = value;
    tail_.store(next_tail, std::memory_order_release);
    return true;
}

template <typename T>
bool RingBuffer<T>::pop_front(T& value) {
    uint32_t head = head_.load(std::memory_order_acquire);
    
    if (head == tail_.load(std::memory_order_acquire)) {
        return false;  // Empty
    }
    
    value = buffer_[head];
    head_.store((head + 1) % capacity_, std::memory_order_release);
    return true;
}

template <typename T>
uint32_t RingBuffer<T>::size() const {
    uint32_t h = head_.load(std::memory_order_acquire);
    uint32_t t = tail_.load(std::memory_order_acquire);
    return t >= h ? (t - h) : (capacity_ - h + t);
}

template <typename T>
bool RingBuffer<T>::empty() const {
    return head_.load(std::memory_order_acquire) == 
           tail_.load(std::memory_order_acquire);
}

template <typename T>
bool RingBuffer<T>::full() const {
    return (tail_.load(std::memory_order_acquire) + 1) % capacity_ == 
           head_.load(std::memory_order_acquire);
}

template <typename T>
uint32_t RingBuffer<T>::capacity() const {
    return capacity_;
}

template <typename T>
const T& RingBuffer<T>::peek_front() const {
    return buffer_[head_.load(std::memory_order_acquire)];
}

template <typename T>
void RingBuffer<T>::clear() {
    head_.store(0, std::memory_order_release);
    tail_.store(0, std::memory_order_release);
}

} // namespace nexus
