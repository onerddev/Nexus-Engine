#include "metrics_collector.hpp"
#include <algorithm>
#include <sstream>
#include <iomanip>

namespace nexus {

MetricsCollector::MetricsCollector() 
    : start_time_(std::chrono::high_resolution_clock::now()) {}

void MetricsCollector::record_operation(uint64_t latency_us, bool success) {
    total_operations_.fetch_add(1, std::memory_order_release);
    
    if (!success) {
        total_errors_.fetch_add(1, std::memory_order_release);
    }
    
    latency_sum_us_.fetch_add(latency_us, std::memory_order_release);
    
    uint64_t min_val = min_latency_us_.load(std::memory_order_acquire);
    while (latency_us < min_val && !min_latency_us_.compare_exchange_weak(
        min_val, latency_us, std::memory_order_release)) {
        min_val = min_latency_us_.load(std::memory_order_acquire);
    }
    
    uint64_t max_val = max_latency_us_.load(std::memory_order_acquire);
    while (latency_us > max_val && !max_latency_us_.compare_exchange_weak(
        max_val, latency_us, std::memory_order_release)) {
        max_val = max_latency_us_.load(std::memory_order_acquire);
    }
    
    latency_samples_.push_back(latency_us);
}

void MetricsCollector::record_queue_size(uint32_t size) {
    queue_size_.store(size, std::memory_order_release);
}

void MetricsCollector::record_cpu_usage(double usage) {
    cpu_usage_.store(usage, std::memory_order_release);
}

void MetricsCollector::record_memory_usage(uint64_t bytes) {
    memory_bytes_.store(bytes, std::memory_order_release);
}

MetricsCollector::AggregatedMetrics MetricsCollector::get_aggregated() const {
    AggregatedMetrics agg;
    
    agg.total_operations = total_operations_.load(std::memory_order_acquire);
    agg.total_errors = total_errors_.load(std::memory_order_acquire);
    agg.error_rate = agg.total_operations > 0 ? 
        static_cast<double>(agg.total_errors) / agg.total_operations : 0.0;
    
    uint64_t latency_sum = latency_sum_us_.load(std::memory_order_acquire);
    agg.latency_us.mean = agg.total_operations > 0 ? 
        static_cast<double>(latency_sum) / agg.total_operations : 0.0;
    
    agg.latency_us.min = min_latency_us_.load(std::memory_order_acquire);
    agg.latency_us.max = max_latency_us_.load(std::memory_order_acquire);
    
    agg.queue_size = queue_size_.load(std::memory_order_acquire);
    agg.cpu_usage_percent = cpu_usage_.load(std::memory_order_acquire);
    agg.memory_bytes = memory_bytes_.load(std::memory_order_acquire);
    
    auto now = std::chrono::high_resolution_clock::now();
    auto uptime = std::chrono::duration_cast<std::chrono::seconds>(now - start_time_);
    agg.uptime_seconds = uptime.count();
    
    if (agg.uptime_seconds > 0) {
        agg.throughput_ops_sec = static_cast<double>(agg.total_operations) / agg.uptime_seconds;
    }
    
    agg.latency_us = calculate_percentiles();
    
    return agg;
}

MetricsCollector::AggregatedMetrics MetricsCollector::get_windowed(std::chrono::seconds window) {
    // Simplified windowed metrics - just returns aggregate
    return get_aggregated();
}

void MetricsCollector::reset() {
    total_operations_.store(0, std::memory_order_release);
    total_errors_.store(0, std::memory_order_release);
    latency_sum_us_.store(0, std::memory_order_release);
    min_latency_us_.store(UINT64_MAX, std::memory_order_release);
    max_latency_us_.store(0, std::memory_order_release);
    latency_samples_.clear();
    start_time_ = std::chrono::high_resolution_clock::now();
}

std::string MetricsCollector::to_json() const {
    auto agg = get_aggregated();
    
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2);
    
    oss << "{\n"
        << "  \"total_operations\": " << agg.total_operations << ",\n"
        << "  \"total_errors\": " << agg.total_errors << ",\n"
        << "  \"error_rate\": " << agg.error_rate << ",\n"
        << "  \"latency_us\": {\n"
        << "    \"p50\": " << agg.latency_us.p50 << ",\n"
        << "    \"p95\": " << agg.latency_us.p95 << ",\n"
        << "    \"p99\": " << agg.latency_us.p99 << ",\n"
        << "    \"p999\": " << agg.latency_us.p999 << ",\n"
        << "    \"mean\": " << agg.latency_us.mean << ",\n"
        << "    \"min\": " << agg.latency_us.min << ",\n"
        << "    \"max\": " << agg.latency_us.max << "\n"
        << "  },\n"
        << "  \"throughput_ops_sec\": " << agg.throughput_ops_sec << ",\n"
        << "  \"queue_size\": " << agg.queue_size << ",\n"
        << "  \"cpu_usage_percent\": " << agg.cpu_usage_percent << ",\n"
        << "  \"memory_bytes\": " << agg.memory_bytes << ",\n"
        << "  \"uptime_seconds\": " << agg.uptime_seconds << "\n"
        << "}";
    
    return oss.str();
}

MetricsCollector::PercentileMetrics MetricsCollector::calculate_percentiles() const {
    PercentileMetrics percentiles;
    
    if (latency_samples_.empty()) {
        return percentiles;
    }
    
    auto sorted = latency_samples_;
    std::sort(sorted.begin(), sorted.end());
    
    size_t size = sorted.size();
    
    percentiles.p50 = sorted[size / 2];
    percentiles.p95 = sorted[static_cast<size_t>(size * 0.95)];
    percentiles.p99 = sorted[static_cast<size_t>(size * 0.99)];
    percentiles.p999 = sorted[size - 1];
    
    uint64_t sum = 0;
    for (uint64_t val : sorted) {
        sum += val;
    }
    percentiles.mean = static_cast<double>(sum) / size;
    
    return percentiles;
}

} // namespace nexus
