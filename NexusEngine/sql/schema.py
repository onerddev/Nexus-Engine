"""
PostgreSQL schema initialization for NexusEngine
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# SQL schema definitions
CREATE_TABLES_SQL = """
-- Process results table
CREATE TABLE IF NOT EXISTS process_results (
    id BIGSERIAL PRIMARY KEY,
    process_id UUID NOT NULL,
    operation_type VARCHAR(64) NOT NULL,
    input_data BYTEA NOT NULL,
    output_data BYTEA,
    execution_time_us BIGINT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'SUCCESS',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_process_results_process_id ON process_results(process_id);
CREATE INDEX idx_process_results_created_at ON process_results(created_at DESC);
CREATE INDEX idx_process_results_status ON process_results(status);


-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(128) NOT NULL,
    metric_value DOUBLE PRECISION,
    metric_unit VARCHAR(64),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX idx_metrics_name_time ON metrics(metric_name, timestamp DESC);
CREATE INDEX idx_metrics_tags ON metrics USING GIN(tags);


-- Benchmark results table
CREATE TABLE IF NOT EXISTS benchmark_results (
    id BIGSERIAL PRIMARY KEY,
    benchmark_name VARCHAR(128) NOT NULL,
    operation_type VARCHAR(64) NOT NULL,
    thread_count INT NOT NULL,
    iteration_count INT NOT NULL,
    total_operations BIGINT NOT NULL,
    successful_operations BIGINT NOT NULL,
    failed_operations BIGINT NOT NULL,
    throughput_ops_sec DOUBLE PRECISION NOT NULL,
    min_latency_us BIGINT,
    max_latency_us BIGINT,
    avg_latency_us DOUBLE PRECISION,
    p50_latency_us BIGINT,
    p95_latency_us BIGINT,
    p99_latency_us BIGINT,
    p999_latency_us BIGINT,
    cpu_usage_percent DOUBLE PRECISION,
    memory_usage_bytes BIGINT,
    execution_time_seconds INT,
    status VARCHAR(32) DEFAULT 'SUCCESS',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_benchmark_results_name ON benchmark_results(benchmark_name);
CREATE INDEX idx_benchmark_results_created_at ON benchmark_results(created_at DESC);


-- Plugin logs table
CREATE TABLE IF NOT EXISTS plugin_logs (
    id BIGSERIAL PRIMARY KEY,
    plugin_name VARCHAR(128) NOT NULL,
    plugin_version VARCHAR(32),
    log_level VARCHAR(16) NOT NULL,
    log_message TEXT NOT NULL,
    execution_time_us BIGINT,
    success BOOLEAN DEFAULT TRUE,
    error_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plugin_logs_plugin_name ON plugin_logs(plugin_name);
CREATE INDEX idx_plugin_logs_created_at ON plugin_logs(created_at DESC);
CREATE INDEX idx_plugin_logs_log_level ON plugin_logs(log_level);


-- Operations log table
CREATE TABLE IF NOT EXISTS operations_log (
    id BIGSERIAL PRIMARY KEY,
    operation_id UUID NOT NULL,
    operation_type VARCHAR(64) NOT NULL,
    user_id VARCHAR(128),
    input_hash VARCHAR(64),
    output_hash VARCHAR(64),
    latency_us BIGINT,
    status VARCHAR(32),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operations_log_operation_id ON operations_log(operation_id);
CREATE INDEX idx_operations_log_created_at ON operations_log(created_at DESC);
CREATE INDEX idx_operations_log_operation_type ON operations_log(operation_type);
CREATE INDEX idx_operations_log_user_id ON operations_log(user_id);


-- Engine state table
CREATE TABLE IF NOT EXISTS engine_state (
    id BIGSERIAL PRIMARY KEY,
    state VARCHAR(32) NOT NULL,
    thread_count INT,
    queue_size INT,
    processed_items BIGINT,
    failed_items BIGINT,
    uptime_seconds BIGINT,
    cpu_usage_percent DOUBLE PRECISION,
    memory_usage_bytes BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_engine_state_created_at ON engine_state(created_at DESC);


-- Distributed tracing table
CREATE TABLE IF NOT EXISTS traces (
    id BIGSERIAL PRIMARY KEY,
    trace_id UUID NOT NULL,
    span_id UUID NOT NULL,
    parent_span_id UUID,
    operation_name VARCHAR(128),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_us BIGINT,
    status VARCHAR(32),
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_traces_trace_id ON traces(trace_id);
CREATE INDEX idx_traces_span_id ON traces(span_id);
CREATE INDEX idx_traces_created_at ON traces(created_at DESC);

-- Time-series specific optimizations
CREATE TABLE IF NOT EXISTS metrics_timeseries (
    time TIMESTAMP,
    metric_name TEXT,
    value DOUBLE PRECISION,
    labels JSONB
) PARTITION BY RANGE (time);

CREATE INDEX idx_metrics_timeseries_time ON metrics_timeseries(time DESC);
"""


def init_database():
    """Initialize database schema"""
    try:
        import psycopg2
        from psycopg2.extras import execute_values
        
        # Get database connection parameters
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", 5432))
        db_name = os.getenv("DB_NAME", "nexus_engine")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        cursor = conn.cursor()
        
        # Execute schema creation
        for statement in CREATE_TABLES_SQL.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Database schema initialized successfully on {db_host}:{db_port}/{db_name}")
        
    except ImportError:
        logger.warning("psycopg2 not installed. Skipping database initialization.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    init_database()
