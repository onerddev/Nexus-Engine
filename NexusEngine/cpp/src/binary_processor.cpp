#include "binary_processor.hpp"
#include <bitset>
#include <algorithm>
#include <stdexcept>

namespace nexus {

// Single value operations
uint64_t BinaryProcessor::xor_op(uint64_t a, uint64_t b) {
    return a ^ b;
}

uint64_t BinaryProcessor::and_op(uint64_t a, uint64_t b) {
    return a & b;
}

uint64_t BinaryProcessor::or_op(uint64_t a, uint64_t b) {
    return a | b;
}

uint64_t BinaryProcessor::not_op(uint64_t a) {
    return ~a;
}

uint64_t BinaryProcessor::shift_left(uint64_t a, uint32_t bits) {
    if (bits >= 64) return 0;
    return a << bits;
}

uint64_t BinaryProcessor::shift_right(uint64_t a, uint32_t bits) {
    if (bits >= 64) return 0;
    return a >> bits;
}

uint64_t BinaryProcessor::rotate_left(uint64_t a, uint32_t bits) {
    bits &= 63;
    return (a << bits) | (a >> (64 - bits));
}

uint64_t BinaryProcessor::rotate_right(uint64_t a, uint32_t bits) {
    bits &= 63;
    return (a >> bits) | (a << (64 - bits));
}

uint32_t BinaryProcessor::popcount(uint64_t a) {
    return __builtin_popcountll(a);
}

uint32_t BinaryProcessor::leading_zeros(uint64_t a) {
    if (a == 0) return 64;
    return __builtin_clzll(a);
}

uint32_t BinaryProcessor::trailing_zeros(uint64_t a) {
    if (a == 0) return 64;
    return __builtin_ctzll(a);
}

uint64_t BinaryProcessor::from_binary_string(const std::string& binary) {
    if (binary.length() > 64) {
        throw std::invalid_argument("Binary string too long (max 64 bits)");
    }
    
    uint64_t result = 0;
    for (char c : binary) {
        result = result * 2 + (c - '0');
    }
    return result;
}

std::string BinaryProcessor::to_binary_string(uint64_t value, size_t width) {
    std::string result;
    for (size_t i = 0; i < width; ++i) {
        result = (char)('0' + (value & 1)) + result;
        value >>= 1;
    }
    return result;
}

uint32_t BinaryProcessor::hamming_distance(uint64_t a, uint64_t b) {
    return popcount(a ^ b);
}

BinaryProcessor::BitVector BinaryProcessor::vector_xor(
    const BitVector& a, 
    const BitVector& b) {
    BitVector result;
    size_t min_size = std::min(a.size(), b.size());
    result.reserve(min_size);
    
    for (size_t i = 0; i < min_size; ++i) {
        result.push_back(a[i] ^ b[i]);
    }
    return result;
}

BinaryProcessor::BitVector BinaryProcessor::vector_and(
    const BitVector& a, 
    const BitVector& b) {
    BitVector result;
    size_t min_size = std::min(a.size(), b.size());
    result.reserve(min_size);
    
    for (size_t i = 0; i < min_size; ++i) {
        result.push_back(a[i] & b[i]);
    }
    return result;
}

BinaryProcessor::BitVector BinaryProcessor::vector_or(
    const BitVector& a, 
    const BitVector& b) {
    BitVector result;
    size_t max_size = std::max(a.size(), b.size());
    result.reserve(max_size);
    
    for (size_t i = 0; i < max_size; ++i) {
        uint64_t av = i < a.size() ? a[i] : 0;
        uint64_t bv = i < b.size() ? b[i] : 0;
        result.push_back(av | bv);
    }
    return result;
}

BinaryProcessor::BitVector BinaryProcessor::vector_not(const BitVector& a) {
    BitVector result;
    result.reserve(a.size());
    
    for (uint64_t val : a) {
        result.push_back(~val);
    }
    return result;
}

std::vector<uint64_t> BinaryProcessor::batch_xor(
    const std::vector<uint64_t>& values_a,
    const std::vector<uint64_t>& values_b) {
    std::vector<uint64_t> result;
    size_t min_size = std::min(values_a.size(), values_b.size());
    result.reserve(min_size);
    
    for (size_t i = 0; i < min_size; ++i) {
        result.push_back(values_a[i] ^ values_b[i]);
    }
    return result;
}

} // namespace nexus
