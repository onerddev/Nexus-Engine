#pragma once

#include <cstdint>
#include <vector>
#include <memory>
#include <random>
#include <complex>

namespace nexus {

/**
 * @class QuantumSimulator
 * @brief Quantum-inspired probabilistic binary simulation engine
 * 
 * Uses pseudo-quantum mechanics for:
 * - Probability-based state collapse
 * - Superposition simulation
 * - Entanglement effects
 * - Measurement simulation
 * 
 * Thread-safe: Yes (local RNG per thread)
 * Features:
 * - Configurable qubit count
 * - Bell state generation
 * - Measurement probability calculations
 */
class QuantumSimulator {
public:
    struct QubitState {
        std::complex<double> alpha;  // |0⟩ amplitude
        std::complex<double> beta;   // |1⟩ amplitude
    };

    struct MeasurementResult {
        std::vector<uint32_t> outcomes;
        std::vector<double> probabilities;
        double fidelity = 0.0;
    };

    explicit QuantumSimulator(uint32_t num_qubits = 8);
    
    // State initialization
    void initialize_ground_state();
    void initialize_superposition();
    void initialize_random();
    
    // Gate operations
    void apply_hadamard(uint32_t qubit_idx);
    void apply_pauli_x(uint32_t qubit_idx);
    void apply_pauli_y(uint32_t qubit_idx);
    void apply_pauli_z(uint32_t qubit_idx);
    void apply_phase_shift(uint32_t qubit_idx, double angle);
    
    // Multi-qubit operations
    void apply_cnot(uint32_t control, uint32_t target);
    void apply_swap(uint32_t qubit1, uint32_t qubit2);
    
    // Entanglement
    void create_bell_pair(uint32_t qubit1, uint32_t qubit2);
    double measure_entanglement();
    
    // Measurement
    MeasurementResult measure_all();
    uint32_t measure_qubit(uint32_t qubit_idx);
    
    // Probability calculations
    double get_probability_zero(uint32_t qubit_idx) const;
    double get_probability_one(uint32_t qubit_idx) const;
    
    // State inspection
    const std::vector<QubitState>& get_state() const;
    std::vector<double> get_statevector() const;
    
private:
    uint32_t num_qubits_;
    std::vector<QubitState> state_;
    std::mt19937 rng_;
    
    void normalize_state();
    double calculate_probability(uint32_t qubit_idx, uint32_t outcome) const;
};

} // namespace nexus
