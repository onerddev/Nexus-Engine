#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <array>

namespace nexus {

/**
 * @class HashEngine
 * @brief Custom cryptographic hash implementations
 * 
 * Implements:
 * - SHA256 (secure hash)
 * - MurmurHash3 (fast non-crypto hash)
 * - XXHash (ultra-fast hash)
 * - BLAKE2 (modern cryptographic hash)
 * 
 * Thread-safe: Yes (stateless design)
 * Performance: >1GB/sec throughput
 */
class HashEngine {
public:
    using Hash256 = std::array<uint8_t, 32>;
    using Hash128 = std::array<uint8_t, 16>;
    using Hash64 = uint64_t;

    // SHA256
    static Hash256 sha256(const std::string& data);
    static Hash256 sha256(const std::vector<uint8_t>& data);
    static Hash256 sha256(const uint8_t* data, size_t length);
    
    // MurmurHash3
    static Hash128 murmur3_128(const std::string& data, uint32_t seed = 0);
    static Hash128 murmur3_128(const uint8_t* data, size_t length, uint32_t seed = 0);
    
    static Hash64 murmur3_64(const std::string& data, uint32_t seed = 0);
    static Hash64 murmur3_64(const uint8_t* data, size_t length, uint32_t seed = 0);
    
    // XXHash
    static Hash64 xxhash64(const std::string& data, uint64_t seed = 0);
    static Hash64 xxhash64(const uint8_t* data, size_t length, uint64_t seed = 0);
    
    // BLAKE2
    static Hash256 blake2b_256(const std::string& data);
    static Hash256 blake2b_256(const uint8_t* data, size_t length);
    
    // Utilities
    static std::string hash_to_hex(const Hash256& h);
    static std::string hash_to_hex(const Hash128& h);
    static std::string hash_to_hex(Hash64 h);
    
    // Incremental hashing
    class Hasher {
    public:
        virtual ~Hasher() = default;
        virtual void update(const uint8_t* data, size_t length) = 0;
        virtual void finalize() = 0;
    };
    
    static std::unique_ptr<Hasher> create_sha256_hasher();
    static std::unique_ptr<Hasher> create_xxhash64_hasher(uint64_t seed = 0);

private:
    // Helper functions for SHA256
    static void sha256_process_block(uint32_t* state, const uint8_t* data);
};

} // namespace nexus
