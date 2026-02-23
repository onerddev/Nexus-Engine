#pragma once

#include <cstdint>
#include <vector>
#include <cmath>
#include <memory>

namespace nexus {

/**
 * @class MatrixEngine
 * @brief High-performance matrix computation engine with SIMD optimization
 * 
 * Features:
 * - Matrix multiplication (Strassen algorithm)
 * - Element-wise operations
 * - Matrix decomposition (QR, SVD)
 * - Statistical operations
 * - In-place transformations
 * 
 * Thread-safe: Partial (operations are thread-safe, state management is not)
 * Performance: Handles matrices up to 10k x 10k
 */
class MatrixEngine {
public:
    using Matrix = std::vector<std::vector<double>>;
    
    struct MatrixStats {
        double mean = 0.0;
        double stddev = 0.0;
        double min = 0.0;
        double max = 0.0;
        double sum = 0.0;
    };

    // Matrix creation
    static Matrix create_zeros(uint32_t rows, uint32_t cols);
    static Matrix create_ones(uint32_t rows, uint32_t cols);
    static Matrix create_identity(uint32_t size);
    static Matrix create_random(uint32_t rows, uint32_t cols, double min = 0.0, double max = 1.0);
    
    // Basic operations
    static Matrix add(const Matrix& a, const Matrix& b);
    static Matrix subtract(const Matrix& a, const Matrix& b);
    static Matrix multiply(const Matrix& a, const Matrix& b);
    static Matrix element_wise_multiply(const Matrix& a, const Matrix& b);
    static Matrix scalar_multiply(const Matrix& a, double scalar);
    
    // Linear algebra operations
    static Matrix transpose(const Matrix& m);
    static double determinant(const Matrix& m);
    static Matrix inverse(const Matrix& m);
    static double trace(const Matrix& m);
    
    // Advanced operations
    static std::pair<Matrix, Matrix> qr_decomposition(const Matrix& m);
    static std::tuple<Matrix, std::vector<double>, Matrix> svd(const Matrix& m);
    
    // Statistical operations
    static MatrixStats compute_statistics(const Matrix& m);
    static std::vector<double> normalize_rows(Matrix& m);
    static std::vector<double> normalize_cols(Matrix& m);
    
    // In-place operations
    static void add_inplace(Matrix& a, const Matrix& b);
    static void subtract_inplace(Matrix& a, const Matrix& b);
    static void scale_inplace(Matrix& m, double scalar);
    
    // Utilities
    static uint32_t rows(const Matrix& m);
    static uint32_t cols(const Matrix& m);
    static bool is_square(const Matrix& m);
    static double frobenius_norm(const Matrix& m);

private:
    static Matrix strassen_multiply(const Matrix& a, const Matrix& b);
    static void pad_matrix(Matrix& m, uint32_t size);
};

} // namespace nexus
