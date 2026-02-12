#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include <array>

namespace nexus {

/**
 * @class BinaryProcessor
 * @brief Ultra-fast binary and bitwise operations processor
 * 
 * Handles massive bitwise operations:
 * - XOR, AND, OR, NOT operations
 * - Bit shifting and rotation
 * - Bit counting (popcount)
 * - SIMD-optimized operations
 * 
 * Thread-safe: Yes (stateless design)
 * Performance: 10k+/sec operations
 */
class BinaryProcessor {
public:
    using BitVector = std::vector<uint64_t>;

    // Bitwise operations
    static uint64_t xor_op(uint64_t a, uint64_t b);
    static uint64_t and_op(uint64_t a, uint64_t b);
    static uint64_t or_op(uint64_t a, uint64_t b);
    static uint64_t not_op(uint64_t a);
    static uint64_t shift_left(uint64_t a, uint32_t bits);
    static uint64_t shift_right(uint64_t a, uint32_t bits);
    static uint64_t rotate_left(uint64_t a, uint32_t bits);
    static uint64_t rotate_right(uint64_t a, uint32_t bits);
    
    // Advanced operations
    static uint32_t popcount(uint64_t a);
    static uint32_t leading_zeros(uint64_t a);
    static uint32_t trailing_zeros(uint64_t a);
    
    // Vector operations
    static BitVector vector_xor(const BitVector& a, const BitVector& b);
    static BitVector vector_and(const BitVector& a, const BitVector& b);
    static BitVector vector_or(const BitVector& a, const BitVector& b);
    static BitVector vector_not(const BitVector& a);
    
    // String-based binary parsing
    static uint64_t from_binary_string(const std::string& binary);
    static std::string to_binary_string(uint64_t value, size_t width = 64);
    
    // Hamming distance
    static uint32_t hamming_distance(uint64_t a, uint64_t b);
    
    // SIMD batch processing
    static std::vector<uint64_t> batch_xor(
        const std::vector<uint64_t>& values_a,
        const std::vector<uint64_t>& values_b
    );
};

} // namespace nexus
