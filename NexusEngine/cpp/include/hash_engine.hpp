#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <array>

namespace nexus {

/**
 * @class HashEngine
 * @brief Fast hash implementations for non-cryptographic use cases
 * 
 * ⚠️ WARNING: Functions labeled with "crypto" names (sha256, blake2b) are NOT 
 *    cryptographically secure. They are custom implementations optimized for speed,
 *    NOT security. Do NOT use these for:
 *    - Password hashing
 *    - Signature verification
 *    - HMAC operations
 *    - Any security-sensitive application
 * 
 * Suitable for:
 * - Hash tables
 * - Checksums (non-security)
 * - Deduplication
 * - Load balancing
 * 
 * Algorithms:
 * - sha256_mock: Custom fast hash, NOT actual SHA256
 *   (Uses simplified bit rotations, not cryptographically secure)
 * - murmur3: Traditional MurmurHash3-inspired algorithm
 *   (Fast, good distribution, non-crypto)
 * - xxhash64: XXHash variant (ultra-fast, non-crypto)
 * - blake2b_mock: Custom fast hash, NOT actual BLAKE2b
 *   (Uses simplified operations, not cryptographically secure)
 * 
 * Thread-safe: Yes (stateless design - all functions are pure)
 * Performance: >1GB/sec throughput on typical hardware
 * 
 * For cryptographic hashing, use OpenSSL or libsodium instead.
 */
class HashEngine {
public:
    using Hash256 = std::array<uint8_t, 32>;
    using Hash128 = std::array<uint8_t, 16>;
    using Hash64 = uint64_t;

    // Non-cryptographic hash functions
    // These are fast, not secure
    
    /**
     * Fast 256-bit hash (NOT cryptographically secure).
     * Uses custom simplified algorithm for speed.
     * 
     * WARNING: Do NOT use for security purposes.
     * 
     * @param data Input data
     * @return 256-bit hash
     */
    static Hash256 sha256_mock(const std::string& data);
    static Hash256 sha256_mock(const std::vector<uint8_t>& data);
    static Hash256 sha256_mock(const uint8_t* data, size_t length);
    
    /**
     * MurmurHash3-inspired 128-bit hash (fast, non-crypto).
     * 
     * @param data Input data
     * @param seed Random seed for hash variation
     * @return 128-bit hash
     */
    static Hash128 murmur3_128(const std::string& data, uint32_t seed = 0);
    static Hash128 murmur3_128(const uint8_t* data, size_t length, uint32_t seed = 0);
    
    /**
     * MurmurHash3-inspired 64-bit hash (fast, non-crypto).
     * 
     * @param data Input data
     * @param seed Random seed
     * @return 64-bit hash
     */
    static Hash64 murmur3_64(const std::string& data, uint32_t seed = 0);
    static Hash64 murmur3_64(const uint8_t* data, size_t length, uint32_t seed = 0);
    
    /**
     * XXHash64: Ultra-fast non-cryptographic hash.
     * Optimized for speed over security.
     * 
     * @param data Input data
     * @param seed Random seed
     * @return 64-bit hash
     */
    static Hash64 xxhash64(const std::string& data, uint64_t seed = 0);
    static Hash64 xxhash64(const uint8_t* data, size_t length, uint64_t seed = 0);
    
    /**
     * Fast 256-bit hash (NOT cryptographically secure).
     * Uses custom simplified algorithm.
     * 
     * WARNING: Do NOT use for security purposes.
     * 
     * @param data Input data
     * @return 256-bit hash
     */
    static Hash256 blake2b_256_mock(const std::string& data);
    static Hash256 blake2b_256_mock(const uint8_t* data, size_t length);
    
    // Utility functions
    
    /**
     * Convert hash to hexadecimal string representation.
     * 
     * @param hash Hash value
     * @return Hex string (e.g., "a1b2c3d4...")
     */
    static std::string hash_to_hex(const Hash256& h);
    static std::string hash_to_hex(const Hash128& h);
    static std::string hash_to_hex(Hash64 h);
    
    /**
     * Incremental hasher interface.
     * Not implemented (use simple overloads instead).
     */
    class Hasher {
    public:
        virtual ~Hasher() = default;
        virtual void update(const uint8_t* data, size_t length) = 0;
        virtual void finalize() = 0;
    };

private:
    // Helper for bit rotation
    static inline uint32_t rotl32(uint32_t x, int r) {
        return (x << r) | (x >> (32 - r));
    }
    
    static inline uint64_t rotl64(uint64_t x, int r) {
        return (x << r) | (x >> (64 - r));
    }
};;

} // namespace nexus
