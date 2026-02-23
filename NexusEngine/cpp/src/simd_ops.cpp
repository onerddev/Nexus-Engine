#include "simd_ops.hpp"
#include <immintrin.h>
#include <algorithm>
#include <numeric>

namespace nexus {

double SIMDOptimizedOps::dot_product(const std::vector<double>& a,
                                     const std::vector<double>& b) {
    double result = 0.0;
    
    // Check for AVX2
    size_t i = 0;
    #ifdef __AVX2__
    __m256d sum = _mm256_setzero_pd();
    
    for (; i + 4 <= a.size(); i += 4) {
        __m256d va = _mm256_loadu_pd(&a[i]);
        __m256d vb = _mm256_loadu_pd(&b[i]);
        __m256d prod = _mm256_mul_pd(va, vb);
        sum = _mm256_add_pd(sum, prod);
    }
    
    // Horizontal sum
    __m128d sum_high = _mm256_extractf128_pd(sum, 1);
    __m128d sum_low = _mm256_castpd256_pd128(sum);
    sum_low = _mm_add_pd(sum_low, sum_high);
    sum_low = _mm_add_pd(sum_low, _mm_shuffle_pd(sum_low, sum_low, 1));
    result = _mm_cvtsd_f64(sum_low);
    #endif
    
    // Scalar fallback
    for (; i < a.size(); ++i) {
        result += a[i] * b[i];
    }
    
    return result;
}

std::vector<double> SIMDOptimizedOps::vector_add(const std::vector<double>& a,
                                                  const std::vector<double>& b) {
    std::vector<double> result(a.size());
    
    #ifdef __AVX2__
    size_t i = 0;
    for (; i + 4 <= a.size(); i += 4) {
        __m256d va = _mm256_loadu_pd(&a[i]);
        __m256d vb = _mm256_loadu_pd(&b[i]);
        __m256d sum = _mm256_add_pd(va, vb);
        _mm256_storeu_pd(&result[i], sum);
    }
    
    for (; i < a.size(); ++i) {
        result[i] = a[i] + b[i];
    }
    #else
    std::transform(a.begin(), a.end(), b.begin(), result.begin(),
                   [](double x, double y) { return x + y; });
    #endif
    
    return result;
}

std::vector<double> SIMDOptimizedOps::vector_multiply(const std::vector<double>& a,
                                                       const std::vector<double>& b) {
    std::vector<double> result(a.size());
    
    #ifdef __AVX2__
    size_t i = 0;
    for (; i + 4 <= a.size(); i += 4) {
        __m256d va = _mm256_loadu_pd(&a[i]);
        __m256d vb = _mm256_loadu_pd(&b[i]);
        __m256d prod = _mm256_mul_pd(va, vb);
        _mm256_storeu_pd(&result[i], prod);
    }
    
    for (; i < a.size(); ++i) {
        result[i] = a[i] * b[i];
    }
    #else
    std::transform(a.begin(), a.end(), b.begin(), result.begin(),
                   [](double x, double y) { return x * y; });
    #endif
    
    return result;
}

std::vector<double> SIMDOptimizedOps::scalar_multiply(const std::vector<double>& v,
                                                       double scalar) {
    std::vector<double> result(v.size());
    
    #ifdef __AVX2__
    __m256d scalar_v = _mm256_set1_pd(scalar);
    size_t i = 0;
    
    for (; i + 4 <= v.size(); i += 4) {
        __m256d vv = _mm256_loadu_pd(&v[i]);
        __m256d prod = _mm256_mul_pd(vv, scalar_v);
        _mm256_storeu_pd(&result[i], prod);
    }
    
    for (; i < v.size(); ++i) {
        result[i] = v[i] * scalar;
    }
    #else
    std::transform(v.begin(), v.end(), result.begin(),
                   [scalar](double x) { return x * scalar; });
    #endif
    
    return result;
}

double SIMDOptimizedOps::vector_sum(const std::vector<double>& v) {
    return std::accumulate(v.begin(), v.end(), 0.0);
}

double SIMDOptimizedOps::vector_min(const std::vector<double>& v) {
    return *std::min_element(v.begin(), v.end());
}

double SIMDOptimizedOps::vector_max(const std::vector<double>& v) {
    return *std::max_element(v.begin(), v.end());
}

void SIMDOptimizedOps::parallel_sort(std::vector<uint64_t>& data) {
    std::sort(data.begin(), data.end());
}

uint32_t SIMDOptimizedOps::simd_popcount(const std::vector<uint64_t>& data) {
    uint32_t count = 0;
    for (uint64_t val : data) {
        count += __builtin_popcountll(val);
    }
    return count;
}

std::string SIMDOptimizedOps::get_cpu_features() {
    std::string features;
    
    #ifdef __AVX512F__
    features += "AVX512F ";
    #endif
    
    #ifdef __AVX2__
    features += "AVX2 ";
    #endif
    
    #ifdef __SSE4_2__
    features += "SSE4.2 ";
    #endif
    
    #ifdef __POPCNT__
    features += "POPCNT ";
    #endif
    
    if (features.empty()) {
        features = "SCALAR_ONLY";
    }
    
    return features;
}

} // namespace nexus
