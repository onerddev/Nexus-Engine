#include "matrix_engine.hpp"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <random>

namespace nexus {

MatrixEngine::Matrix MatrixEngine::create_zeros(uint32_t rows, uint32_t cols) {
    return Matrix(rows, std::vector<double>(cols, 0.0));
}

MatrixEngine::Matrix MatrixEngine::create_ones(uint32_t rows, uint32_t cols) {
    return Matrix(rows, std::vector<double>(cols, 1.0));
}

MatrixEngine::Matrix MatrixEngine::create_identity(uint32_t size) {
    auto m = create_zeros(size, size);
    for (uint32_t i = 0; i < size; ++i) {
        m[i][i] = 1.0;
    }
    return m;
}

MatrixEngine::Matrix MatrixEngine::create_random(uint32_t rows, uint32_t cols, 
                                                 double min, double max) {
    std::mt19937 gen(std::random_device{}());
    std::uniform_real_distribution<double> dist(min, max);
    
    Matrix m(rows);
    for (auto& row : m) {
        row.resize(cols);
        for (auto& elem : row) {
            elem = dist(gen);
        }
    }
    return m;
}

MatrixEngine::Matrix MatrixEngine::add(const Matrix& a, const Matrix& b) {
    auto result = a;
    add_inplace(result, b);
    return result;
}

MatrixEngine::Matrix MatrixEngine::subtract(const Matrix& a, const Matrix& b) {
    auto result = a;
    subtract_inplace(result, b);
    return result;
}

MatrixEngine::Matrix MatrixEngine::multiply(const Matrix& a, const Matrix& b) {
    uint32_t m = rows(a);
    uint32_t n = cols(a);
    uint32_t p = cols(b);
    
    auto result = create_zeros(m, p);
    
    #pragma omp parallel for collapse(2)
    for (uint32_t i = 0; i < m; ++i) {
        for (uint32_t j = 0; j < p; ++j) {
            double sum = 0.0;
            for (uint32_t k = 0; k < n; ++k) {
                sum += a[i][k] * b[k][j];
            }
            result[i][j] = sum;
        }
    }
    
    return result;
}

MatrixEngine::Matrix MatrixEngine::element_wise_multiply(const Matrix& a, 
                                                         const Matrix& b) {
    auto result = a;
    #pragma omp parallel for
    for (uint32_t i = 0; i < rows(a); ++i) {
        for (uint32_t j = 0; j < cols(a); ++j) {
            result[i][j] *= b[i][j];
        }
    }
    return result;
}

MatrixEngine::Matrix MatrixEngine::scalar_multiply(const Matrix& a, double scalar) {
    auto result = a;
    scale_inplace(result, scalar);
    return result;
}

MatrixEngine::Matrix MatrixEngine::transpose(const Matrix& m) {
    uint32_t r = rows(m);
    uint32_t c = cols(m);
    
    auto result = create_zeros(c, r);
    #pragma omp parallel for collapse(2)
    for (uint32_t i = 0; i < r; ++i) {
        for (uint32_t j = 0; j < c; ++j) {
            result[j][i] = m[i][j];
        }
    }
    return result;
}

double MatrixEngine::determinant(const Matrix& m) {
    if (!is_square(m)) return 0.0;
    
    uint32_t n = rows(m);
    auto temp = m;
    double det = 1.0;
    
    for (uint32_t i = 0; i < n; ++i) {
        // Find pivot
        uint32_t pivot = i;
        for (uint32_t k = i + 1; k < n; ++k) {
            if (std::abs(temp[k][i]) > std::abs(temp[pivot][i])) {
                pivot = k;
            }
        }
        
        if (std::abs(temp[pivot][i]) < 1e-10) return 0.0;
        
        if (pivot != i) {
            std::swap(temp[i], temp[pivot]);
            det *= -1.0;
        }
        
        det *= temp[i][i];
        
        for (uint32_t k = i + 1; k < n; ++k) {
            double factor = temp[k][i] / temp[i][i];
            for (uint32_t j = i; j < n; ++j) {
                temp[k][j] -= factor * temp[i][j];
            }
        }
    }
    
    return det;
}

MatrixEngine::Matrix MatrixEngine::inverse(const Matrix& m) {
    if (!is_square(m)) return create_zeros(rows(m), cols(m));
    
    uint32_t n = rows(m);
    auto augmented = create_zeros(n, 2 * n);
    
    for (uint32_t i = 0; i < n; ++i) {
        for (uint32_t j = 0; j < n; ++j) {
            augmented[i][j] = m[i][j];
        }
        augmented[i][n + i] = 1.0;
    }
    
    // Gauss-Jordan elimination
    for (uint32_t i = 0; i < n; ++i) {
        // Find pivot
        uint32_t pivot = i;
        for (uint32_t k = i + 1; k < n; ++k) {
            if (std::abs(augmented[k][i]) > std::abs(augmented[pivot][i])) {
                pivot = k;
            }
        }
        std::swap(augmented[i], augmented[pivot]);
        
        // Scale pivot row
        double pivot_val = augmented[i][i];
        for (uint32_t j = 0; j < 2 * n; ++j) {
            augmented[i][j] /= pivot_val;
        }
        
        // Eliminate column
        for (uint32_t k = 0; k < n; ++k) {
            if (k == i) continue;
            double factor = augmented[k][i];
            for (uint32_t j = 0; j < 2 * n; ++j) {
                augmented[k][j] -= factor * augmented[i][j];
            }
        }
    }
    
    auto result = create_zeros(n, n);
    for (uint32_t i = 0; i < n; ++i) {
        for (uint32_t j = 0; j < n; ++j) {
            result[i][j] = augmented[i][n + j];
        }
    }
    return result;
}

double MatrixEngine::trace(const Matrix& m) {
    if (!is_square(m)) return 0.0;
    
    double sum = 0.0;
    for (uint32_t i = 0; i < rows(m); ++i) {
        sum += m[i][i];
    }
    return sum;
}

MatrixEngine::MatrixStats MatrixEngine::compute_statistics(const Matrix& m) {
    MatrixStats stats;
    
    for (const auto& row : m) {
        for (double val : row) {
            stats.sum += val;
            stats.min = std::min(stats.min, val);
            stats.max = std::max(stats.max, val);
        }
    }
    
    uint64_t total_elems = rows(m) * cols(m);
    stats.mean = stats.sum / total_elems;
    
    double variance = 0.0;
    for (const auto& row : m) {
        for (double val : row) {
            variance += (val - stats.mean) * (val - stats.mean);
        }
    }
    stats.stddev = std::sqrt(variance / total_elems);
    
    return stats;
}

void MatrixEngine::add_inplace(Matrix& a, const Matrix& b) {
    #pragma omp parallel for
    for (uint32_t i = 0; i < rows(a); ++i) {
        for (uint32_t j = 0; j < cols(a); ++j) {
            a[i][j] += b[i][j];
        }
    }
}

void MatrixEngine::subtract_inplace(Matrix& a, const Matrix& b) {
    #pragma omp parallel for
    for (uint32_t i = 0; i < rows(a); ++i) {
        for (uint32_t j = 0; j < cols(a); ++j) {
            a[i][j] -= b[i][j];
        }
    }
}

void MatrixEngine::scale_inplace(Matrix& m, double scalar) {
    #pragma omp parallel for
    for (uint32_t i = 0; i < rows(m); ++i) {
        for (uint32_t j = 0; j < cols(m); ++j) {
            m[i][j] *= scalar;
        }
    }
}

uint32_t MatrixEngine::rows(const Matrix& m) {
    return m.size();
}

uint32_t MatrixEngine::cols(const Matrix& m) {
    return m.empty() ? 0 : m[0].size();
}

bool MatrixEngine::is_square(const Matrix& m) {
    return rows(m) == cols(m);
}

double MatrixEngine::frobenius_norm(const Matrix& m) {
    double sum = 0.0;
    for (const auto& row : m) {
        for (double val : row) {
            sum += val * val;
        }
    }
    return std::sqrt(sum);
}

std::pair<MatrixEngine::Matrix, MatrixEngine::Matrix> 
MatrixEngine::qr_decomposition(const Matrix& m) {
    // Simplified Gram-Schmidt QR
    uint32_t m_rows = rows(m);
    uint32_t m_cols = cols(m);
    
    auto Q = create_zeros(m_rows, m_cols);
    auto R = create_zeros(m_cols, m_cols);
    
    for (uint32_t j = 0; j < m_cols; ++j) {
        // Copy column
        for (uint32_t i = 0; i < m_rows; ++i) {
            Q[i][j] = m[i][j];
        }
        
        // Gram-Schmidt orthogonalization
        for (uint32_t k = 0; k < j; ++k) {
            double dot = 0.0;
            for (uint32_t i = 0; i < m_rows; ++i) {
                dot += Q[i][k] * Q[i][j];
            }
            R[k][j] = dot;
            
            for (uint32_t i = 0; i < m_rows; ++i) {
                Q[i][j] -= dot * Q[i][k];
            }
        }
        
        // Normalization
        double norm = 0.0;
        for (uint32_t i = 0; i < m_rows; ++i) {
            norm += Q[i][j] * Q[i][j];
        }
        norm = std::sqrt(norm);
        R[j][j] = norm;
        
        if (norm > 1e-10) {
            for (uint32_t i = 0; i < m_rows; ++i) {
                Q[i][j] /= norm;
            }
        }
    }
    
    return {Q, R};
}

std::tuple<MatrixEngine::Matrix, std::vector<double>, MatrixEngine::Matrix> 
MatrixEngine::svd(const Matrix& m) {
    // Simplified SVD - return approximate decomposition
    auto [Q, R] = qr_decomposition(m);
    
    std::vector<double> singular_values;
    for (uint32_t i = 0; i < std::min(rows(R), cols(R)); ++i) {
        singular_values.push_back(std::abs(R[i][i]));
    }
    
    return {Q, singular_values, R};
}

std::vector<double> MatrixEngine::normalize_rows(Matrix& m) {
    std::vector<double> norms;
    for (auto& row : m) {
        double norm = 0.0;
        for (double val : row) {
            norm += val * val;
        }
        norm = std::sqrt(norm);
        norms.push_back(norm);
        
        if (norm > 1e-10) {
            for (auto& val : row) {
                val /= norm;
            }
        }
    }
    return norms;
}

std::vector<double> MatrixEngine::normalize_cols(Matrix& m) {
    std::vector<double> norms(cols(m), 0.0);
    
    for (const auto& row : m) {
        for (uint32_t j = 0; j < cols(m); ++j) {
            norms[j] += row[j] * row[j];
        }
    }
    
    for (auto& n : norms) {
        n = std::sqrt(n);
    }
    
    for (auto& row : m) {
        for (uint32_t j = 0; j < cols(m); ++j) {
            if (norms[j] > 1e-10) {
                row[j] /= norms[j];
            }
        }
    }
    
    return norms;
}

} // namespace nexus
