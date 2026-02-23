"""
Configuration for NexusEngine
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Engine
    ENGINE_THREADS = int(os.getenv("ENGINE_THREADS", os.cpu_count() or 4))
    ENGINE_QUEUE_CAPACITY = int(os.getenv("ENGINE_QUEUE_CAPACITY", 100000))
    ENGINE_BATCH_SIZE = int(os.getenv("ENGINE_BATCH_SIZE", 1024))
    ENGINE_TIMEOUT_MS = int(os.getenv("ENGINE_TIMEOUT_MS", 5000))
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_WORKERS = int(os.getenv("API_WORKERS", 4))
    API_RELOAD = os.getenv("API_RELOAD", "false").lower() == "true"
    
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME", "nexus_engine")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    LOG_FILE = os.getenv("LOG_FILE", "nexus_engine.log")
    
    # Security
    API_KEY = os.getenv("API_KEY", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Performance
    RATE_LIMIT_RPS = int(os.getenv("RATE_LIMIT_RPS", 1000))
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
    
    # Monitoring
    METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    TRACING_ENABLED = os.getenv("TRACING_ENABLED", "true").lower() == "true"
    PROMETHEUS_METRICS = os.getenv("PROMETHEUS_METRICS", "false").lower() == "true"


# Export configuration
config = Config()
