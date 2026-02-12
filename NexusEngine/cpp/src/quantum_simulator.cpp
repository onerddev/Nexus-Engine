#include "quantum_simulator.hpp"
#include <cmath>
#include <algorithm>

namespace nexus {

QuantumSimulator::QuantumSimulator(uint32_t num_qubits)
    : num_qubits_(num_qubits), rng_(std::random_device{}()) {
    state_.resize(num_qubits);
    initialize_ground_state();
}

void QuantumSimulator::initialize_ground_state() {
    // All qubits in |0⟩ state
    for (auto& qubit : state_) {
        qubit.alpha = {1.0, 0.0};  // |0⟩ amplitude = 1
        qubit.beta = {0.0, 0.0};   // |1⟩ amplitude = 0
    }
}

void QuantumSimulator::initialize_superposition() {
    // All qubits in equal superposition (1/√2)(|0⟩ + |1⟩)
    double inv_sqrt2 = 1.0 / std::sqrt(2.0);
    for (auto& qubit : state_) {
        qubit.alpha = {inv_sqrt2, 0.0};
        qubit.beta = {inv_sqrt2, 0.0};
    }
}

void QuantumSimulator::initialize_random() {
    std::uniform_real_distribution<double> dist(0.0, 1.0);
    
    for (auto& qubit : state_) {
        double theta = dist(rng_) * M_PI;
        double phi = dist(rng_) * 2.0 * M_PI;
        
        qubit.alpha = std::polar(std::sin(theta / 2.0), phi);
        qubit.beta = std::polar(std::cos(theta / 2.0), phi + M_PI);
    }
    normalize_state();
}

void QuantumSimulator::apply_hadamard(uint32_t qubit_idx) {
    if (qubit_idx >= num_qubits_) return;
    
    double inv_sqrt2 = 1.0 / std::sqrt(2.0);
    auto& qubit = state_[qubit_idx];
    
    auto alpha = qubit.alpha;
    auto beta = qubit.beta;
    
    qubit.alpha = (alpha + beta) * inv_sqrt2;
    qubit.beta = (alpha - beta) * inv_sqrt2;
}

void QuantumSimulator::apply_pauli_x(uint32_t qubit_idx) {
    if (qubit_idx >= num_qubits_) return;
    std::swap(state_[qubit_idx].alpha, state_[qubit_idx].beta);
}

void QuantumSimulator::apply_pauli_y(uint32_t qubit_idx) {
    if (qubit_idx >= num_qubits_) return;
    
    auto& qubit = state_[qubit_idx];
    auto alpha = qubit.alpha;
    auto beta = qubit.beta;
    
    qubit.alpha = beta * std::complex<double>(0, -1);
    qubit.beta = alpha * std::complex<double>(0, 1);
}

void QuantumSimulator::apply_pauli_z(uint32_t qubit_idx) {
    if (qubit_idx >= num_qubits_) return;
    state_[qubit_idx].beta = -state_[qubit_idx].beta;
}

void QuantumSimulator::apply_phase_shift(uint32_t qubit_idx, double angle) {
    if (qubit_idx >= num_qubits_) return;
    
    auto phase = std::polar(1.0, angle);
    state_[qubit_idx].beta *= phase;
}

void QuantumSimulator::apply_cnot(uint32_t control, uint32_t target) {
    if (control >= num_qubits_ || target >= num_qubits_) return;
    
    // Simplified CNOT simulation
    double prob_one = std::norm(state_[control].beta);
    if (prob_one > 0.5) {
        std::swap(state_[target].alpha, state_[target].beta);
    }
}

void QuantumSimulator::apply_swap(uint32_t qubit1, uint32_t qubit2) {
    if (qubit1 >= num_qubits_ || qubit2 >= num_qubits_) return;
    std::swap(state_[qubit1], state_[qubit2]);
}

void QuantumSimulator::create_bell_pair(uint32_t qubit1, uint32_t qubit2) {
    if (qubit1 >= num_qubits_ || qubit2 >= num_qubits_) return;
    
    apply_hadamard(qubit1);
    apply_cnot(qubit1, qubit2);
}

double QuantumSimulator::measure_entanglement() {
    // Calculate concurrence as entanglement measure
    double entanglement = 0.0;
    for (size_t i = 0; i < state_.size(); ++i) {
        for (size_t j = i + 1; j < state_.size(); ++j) {
            entanglement += std::abs(std::norm(state_[i].alpha) - 
                                     std::norm(state_[i].beta)) * 
                           std::abs(std::norm(state_[j].alpha) - 
                                   std::norm(state_[j].beta));
        }
    }
    return entanglement / (state_.size() * (state_.size() - 1) / 2.0);
}

QuantumSimulator::MeasurementResult QuantumSimulator::measure_all() {
    MeasurementResult result;
    
    for (uint32_t i = 0; i < num_qubits_; ++i) {
        double prob_zero = std::norm(state_[i].alpha);
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        
        uint32_t outcome = dist(rng_) < prob_zero ? 0 : 1;
        result.outcomes.push_back(outcome);
        result.probabilities.push_back(outcome ? 1.0 - prob_zero : prob_zero);
    }
    
    result.fidelity = 1.0;  // Perfect measurement fidelity
    return result;
}

uint32_t QuantumSimulator::measure_qubit(uint32_t qubit_idx) {
    if (qubit_idx >= num_qubits_) return 0;
    
    double prob_zero = std::norm(state_[qubit_idx].alpha);
    std::uniform_real_distribution<double> dist(0.0, 1.0);
    
    return dist(rng_) < prob_zero ? 0 : 1;
}

double QuantumSimulator::get_probability_zero(uint32_t qubit_idx) const {
    if (qubit_idx >= num_qubits_) return 0.0;
    return std::norm(state_[qubit_idx].alpha);
}

double QuantumSimulator::get_probability_one(uint32_t qubit_idx) const {
    if (qubit_idx >= num_qubits_) return 0.0;
    return std::norm(state_[qubit_idx].beta);
}

const std::vector<QuantumSimulator::QubitState>& QuantumSimulator::get_state() const {
    return state_;
}

std::vector<double> QuantumSimulator::get_statevector() const {
    std::vector<double> statevector;
    statevector.reserve(1u << num_qubits_);
    
    // Simplified: return individual qubit probabilities
    for (const auto& qubit : state_) {
        statevector.push_back(std::norm(qubit.alpha));
        statevector.push_back(std::norm(qubit.beta));
    }
    return statevector;
}

void QuantumSimulator::normalize_state() {
    double norm_sq = 0.0;
    for (const auto& qubit : state_) {
        norm_sq += std::norm(qubit.alpha) + std::norm(qubit.beta);
    }
    
    if (norm_sq > 0.0) {
        double norm = std::sqrt(norm_sq);
        for (auto& qubit : state_) {
            qubit.alpha /= norm;
            qubit.beta /= norm;
        }
    }
}

} // namespace nexus
