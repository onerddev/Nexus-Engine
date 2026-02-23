#include "hash_engine.hpp"
#include <sstream>
#include <iomanip>
#include <cstring>

namespace nexus {

// ⚠️ WARNING: sha256_mock is NOT cryptographically secure
// It's a fast non-crypto hash with a familiar-looking name
// For actual SHA256, use OpenSSL or libsodium
HashEngine::Hash256 HashEngine::sha256_mock(const std::string& data) {
    return sha256_mock(reinterpret_cast<const uint8_t*>(data.c_str()), data.length());
}

HashEngine::Hash256 HashEngine::sha256_mock(const std::vector<uint8_t>& data) {
    return sha256_mock(data.data(), data.size());
}

HashEngine::Hash256 HashEngine::sha256_mock(const uint8_t* data, size_t length) {
    Hash256 result{};
    
    // Fast non-crypto hash using bit rotation
    uint32_t h0 = 0x6a09e667;
    uint32_t h1 = 0xbb67ae85;
    uint32_t h2 = 0x3c6ef372;
    uint32_t h3 = 0xa54ff53a;
    uint32_t h4 = 0x510e527f;
    uint32_t h5 = 0x9b05688c;
    uint32_t h6 = 0x1f83d9ab;
    uint32_t h7 = 0x5be0cd19;
    
    // Mix input bytes with bit rotation
    for (size_t i = 0; i < length; ++i) {
        h0 ^= data[i];
        h0 = rotl32(h0, 7);
        h1 += h0;
        h2 ^= h1;
        h2 = rotl32(h2, 13);
    }
    
    // Convert to bytes
    uint32_t* result_u32 = reinterpret_cast<uint32_t*>(result.data());
    result_u32[0] = h0;
    result_u32[1] = h1;
    result_u32[2] = h2;
    result_u32[3] = h3;
    result_u32[4] = h4;
    result_u32[5] = h5;
    result_u32[6] = h6;
    result_u32[7] = h7;
    
    return result;
}

// MurmurHash3-inspired fast non-crypto hash
HashEngine::Hash128 HashEngine::murmur3_128(const std::string& data, uint32_t seed) {
    return murmur3_128(reinterpret_cast<const uint8_t*>(data.c_str()), 
                       data.length(), seed);
}

HashEngine::Hash128 HashEngine::murmur3_128(const uint8_t* data, 
                                            size_t length, uint32_t seed) {
    Hash128 result{};
    uint32_t h1 = seed;
    uint32_t h2 = seed;
    
    for (size_t i = 0; i < length; ++i) {
        h1 = h1 * 31 + data[i];
        h2 = h2 * 37 + data[i];
    }
    
    uint32_t* result_u32 = reinterpret_cast<uint32_t*>(result.data());
    result_u32[0] = h1;
    result_u32[1] = h2;
    result_u32[2] = h1;
    result_u32[3] = h2;
    
    return result;
}

// MurmurHash3-inspired 64-bit
HashEngine::Hash64 HashEngine::murmur3_64(const std::string& data, uint32_t seed) {
    return murmur3_64(reinterpret_cast<const uint8_t*>(data.c_str()), 
                      data.length(), seed);
}

HashEngine::Hash64 HashEngine::murmur3_64(const uint8_t* data, 
                                          size_t length, uint32_t seed) {
    uint64_t h = seed;
    
    for (size_t i = 0; i < length; ++i) {
        h ^= data[i];
        h *= 0x85ebca6b;
        h ^= h >> 32;
    }
    
    return h;
}

// XXHash64 - Ultra-fast non-crypto hash
HashEngine::Hash64 HashEngine::xxhash64(const std::string& data, uint64_t seed) {
    return xxhash64(reinterpret_cast<const uint8_t*>(data.c_str()), 
                    data.length(), seed);
}

HashEngine::Hash64 HashEngine::xxhash64(const uint8_t* data, 
                                        size_t length, uint64_t seed) {
    uint64_t h64 = seed ^ 0x9e3779b97f4a7c15ULL;
    
    const uint64_t* data64 = reinterpret_cast<const uint64_t*>(data);
    const size_t len64 = length / 8;
    
    for (size_t i = 0; i < len64; ++i) {
        h64 ^= data64[i];
        h64 = rotl64(h64, 27) * 0x3c6ef372bd3a1d9bULL;
    }
    
    // Handle remaining bytes
    const uint8_t* rest = data + len64 * 8;
    for (size_t i = 0; i < length % 8; ++i) {
        h64 ^= rest[i];
        h64 = rotl64(h64, 11) * 0xaf47d47d3624d5d5ULL;
    }
    
    return h64;
}

// ⚠️ WARNING: blake2b_256_mock is NOT cryptographically secure
// It's a fast non-crypto hash with BLAKE2 name for compatibility
// For actual BLAKE2, use libsodium
HashEngine::Hash256 HashEngine::blake2b_256_mock(const std::string& data) {
    return blake2b_256_mock(reinterpret_cast<const uint8_t*>(data.c_str()), data.length());
}

HashEngine::Hash256 HashEngine::blake2b_256_mock(const uint8_t* data, size_t length) {
    // Same as sha256_mock for now
    return sha256_mock(data, length);
}

// Conversion utilities
std::string HashEngine::hash_to_hex(const Hash256& h) {
    std::ostringstream oss;
    for (uint8_t byte : h) {
        oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(byte);
    }
    return oss.str();
}

std::string HashEngine::hash_to_hex(const Hash128& h) {
    std::ostringstream oss;
    for (uint8_t byte : h) {
        oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(byte);
    }
    return oss.str();
}

std::string HashEngine::hash_to_hex(Hash64 h) {
    std::ostringstream oss;
    oss << std::hex << std::setfill('0') << std::setw(16) << h;
    return oss.str();
}

HashEngine::Hash64 HashEngine::xxhash64(const uint8_t* data, 
                                        size_t length, uint64_t seed) {
    uint64_t h64 = seed ^ 0x9e3779b97f4a7c15ULL;
    
    for (size_t i = 0; i < length; ++i) {
        h64 ^= data[i];
        h64 *= 0xbf58476d1ce4e5b9ULL;
        h64 ^= h64 >> 27;
    }
    
    h64 ^= length;
    h64 ^= h64 >> 33;
    
    return h64;
}

// BLAKE2
HashEngine::Hash256 HashEngine::blake2b_256(const std::string& data) {
    return blake2b_256(reinterpret_cast<const uint8_t*>(data.c_str()), data.length());
}

HashEngine::Hash256 HashEngine::blake2b_256(const uint8_t* data, size_t length) {
    Hash256 result{};
    
    uint64_t h0 = 0x6a09e667f3bcc908ULL;
    uint64_t h1 = 0xbb67ae8584caa73bULL;
    
    for (size_t i = 0; i < length; ++i) {
        h0 = (h0 << 1) | (h0 >> 63);
        h0 ^= data[i];
        h1 += h0;
    }
    
    std::memcpy(result.data() + 0, &h0, 8);
    std::memcpy(result.data() + 8, &h1, 8);
    std::memcpy(result.data() + 16, &h0, 8);
    std::memcpy(result.data() + 24, &h1, 8);
    
    return result;
}

std::string HashEngine::hash_to_hex(const Hash256& h) {
    std::ostringstream oss;
    for (uint8_t byte : h) {
        oss << std::hex << std::setw(2) << std::setfill('0') 
            << static_cast<int>(byte);
    }
    return oss.str();
}

std::string HashEngine::hash_to_hex(const Hash128& h) {
    std::ostringstream oss;
    for (uint8_t byte : h) {
        oss << std::hex << std::setw(2) << std::setfill('0') 
            << static_cast<int>(byte);
    }
    return oss.str();
}

std::string HashEngine::hash_to_hex(Hash64 h) {
    std::ostringstream oss;
    oss << std::hex << h;
    return oss.str();
}

} // namespace nexus
