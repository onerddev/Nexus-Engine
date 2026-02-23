"""
Validation utilities for NexusEngine API
Provides consistent input validation and error handling
"""

from typing import Any, Union
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ==================== Constants ====================

# Maximum values for resource limiting
MAX_MATRIX_ROWS = 10000
MAX_MATRIX_COLS = 10000
MAX_MATRIX_SIZE = 100_000_000  # Total elements limit

MAX_QUBITS = 32
MIN_QUBITS = 1

MAX_INT_VALUE = 2**63 - 1
MIN_INT_VALUE = -(2**63)

MAX_THREADS = 256
MIN_THREADS = 1

MAX_QUEUE_CAPACITY = 10_000_000
MIN_QUEUE_CAPACITY = 1000

# Rate limiting
MAX_REQUESTS_PER_SECOND = 1000
MAX_REQUEST_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


# ==================== Validation Functions ====================

def validate_matrix_dimensions(rows: int, cols: int) -> bool:
    """
    Validate matrix dimensions.
    
    Args:
        rows: Number of rows
        cols: Number of columns
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If dimensions exceed limits
    """
    if rows < 1 or rows > MAX_MATRIX_ROWS:
        raise ValueError(f"rows must be 1-{MAX_MATRIX_ROWS}, got {rows}")
    
    if cols < 1 or cols > MAX_MATRIX_COLS:
        raise ValueError(f"cols must be 1-{MAX_MATRIX_COLS}, got {cols}")
    
    if rows * cols > MAX_MATRIX_SIZE:
        raise ValueError(
            f"matrix size {rows}x{cols} exceeds maximum {MAX_MATRIX_SIZE} elements"
        )
    
    return True


def validate_integer_value(value: int, name: str = "value") -> bool:
    """
    Validate integer is within safe bounds.
    
    Args:
        value: Integer value to validate
        name: Parameter name for error messages
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If out of bounds
    """
    if value < MIN_INT_VALUE or value > MAX_INT_VALUE:
        raise ValueError(
            f"{name} must be between {MIN_INT_VALUE} and {MAX_INT_VALUE}, "
            f"got {value}"
        )
    return True


def validate_qubit_count(qubits: int) -> bool:
    """
    Validate qubit count is within reasonable limits.
    
    Args:
        qubits: Number of qubits
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If out of bounds
    """
    if qubits < MIN_QUBITS or qubits > MAX_QUBITS:
        raise ValueError(
            f"qubits must be {MIN_QUBITS}-{MAX_QUBITS}, got {qubits}"
        )
    return True


def validate_thread_count(threads: int) -> bool:
    """
    Validate thread count is reasonable.
    
    Args:
        threads: Number of threads
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If out of bounds
    """
    if threads < MIN_THREADS or threads > MAX_THREADS:
        raise ValueError(
            f"threads must be {MIN_THREADS}-{MAX_THREADS}, got {threads}"
        )
    return True


def validate_queue_capacity(capacity: int) -> bool:
    """
    Validate queue capacity is within limits.
    
    Args:
        capacity: Queue capacity
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If out of bounds
    """
    if capacity < MIN_QUEUE_CAPACITY or capacity > MAX_QUEUE_CAPACITY:
        raise ValueError(
            f"queue_capacity must be {MIN_QUEUE_CAPACITY}-{MAX_QUEUE_CAPACITY}, "
            f"got {capacity}"
        )
    return True


# ==================== Schemas ====================

class EngineStartRequestV2(BaseModel):
    """Engine startup request with full validation"""
    
    threads: int = Field(
        default=4,
        ge=MIN_THREADS,
        le=MAX_THREADS,
        description="Number of worker threads"
    )
    queue_capacity: int = Field(
        default=100000,
        ge=MIN_QUEUE_CAPACITY,
        le=MAX_QUEUE_CAPACITY,
        description="Task queue capacity"
    )
    
    @validator('threads')
    def validate_threads_field(cls, v):
        validate_thread_count(v)
        return v
    
    @validator('queue_capacity')
    def validate_queue_capacity_field(cls, v):
        validate_queue_capacity(v)
        return v


class BinaryOperationRequestV2(BaseModel):
    """Binary operation request with validation"""
    
    operation: str = Field(
        ...,
        description="Operation: xor, and, or, not",
        regex="^(xor|and|or|not)$"
    )
    value_a: int = Field(
        ...,
        le=MAX_INT_VALUE,
        ge=MIN_INT_VALUE,
        description="First integer value"
    )
    value_b: Union[int, None] = Field(
        default=None,
        le=MAX_INT_VALUE,
        ge=MIN_INT_VALUE,
        description="Second integer value (optional)"
    )
    
    @validator('operation')
    def validate_operation_field(cls, v):
        valid_ops = {'xor', 'and', 'or', 'not'}
        if v.lower() not in valid_ops:
            raise ValueError(f"operation must be one of {valid_ops}, got {v}")
        return v.lower()


class MatrixOperationRequestV2(BaseModel):
    """Matrix operation request with dimension validation"""
    
    operation: str = Field(
        ...,
        description="Operation: create, zeros, ones, identity, random",
        regex="^(create|zeros|ones|identity|random)$"
    )
    rows: int = Field(
        default=256,
        ge=1,
        le=MAX_MATRIX_ROWS,
        description="Number of rows"
    )
    cols: int = Field(
        default=256,
        ge=1,
        le=MAX_MATRIX_COLS,
        description="Number of columns"
    )
    
    @validator('operation')
    def validate_operation_field(cls, v):
        valid_ops = {'create', 'zeros', 'ones', 'identity', 'random'}
        if v.lower() not in valid_ops:
            raise ValueError(f"operation must be one of {valid_ops}, got {v}")
        return v.lower()
    
    @root_validator
    def validate_dimensions(cls, values):
        rows = values.get('rows')
        cols = values.get('cols')
        
        if rows and cols:
            try:
                validate_matrix_dimensions(rows, cols)
            except ValueError as e:
                raise ValueError(f"Invalid matrix dimensions: {e}")
        
        return values


class QuantumSimulatorRequestV2(BaseModel):
    """Quantum simulator request with validation"""
    
    qubits: int = Field(
        default=6,
        ge=MIN_QUBITS,
        le=MAX_QUBITS,
        description="Number of qubits"
    )
    operation: str = Field(
        default="init",
        description="Operation: init, hadamard, measure"
    )
    qubit_index: Union[int, None] = Field(
        default=None,
        ge=0,
        description="Target qubit index"
    )
    
    @validator('qubits')
    def validate_qubits_field(cls, v):
        validate_qubit_count(v)
        return v
    
    @root_validator
    def validate_qubit_index(cls, values):
        qubits = values.get('qubits')
        qubit_index = values.get('qubit_index')
        
        if qubit_index is not None and qubits is not None:
            if qubit_index >= qubits:
                raise ValueError(
                    f"qubit_index {qubit_index} out of range [0, {qubits-1}]"
                )
        
        return values


# ==================== Error Handling ====================

class ValidationError(Exception):
    """Custom validation error with detailed context"""
    
    def __init__(self, message: str, field: str = None, context: dict = None):
        self.message = message
        self.field = field
        self.context = context or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "error": "validation_error",
            "message": self.message,
            "field": self.field,
            "context": self.context
        }


def safe_validate(model_class, data: dict) -> Union[BaseModel, ValidationError]:
    """
    Safely validate input against Pydantic model.
    
    Args:
        model_class: Pydantic BaseModel class
        data: Input dictionary
    
    Returns:
        Validated model or ValidationError
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        
        # Extract first error
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field = '.'.join(str(x) for x in first_error['loc'])
            message = first_error['msg']
            
            return ValidationError(message, field=field)
        
        return ValidationError(str(e))


# ==================== Rate Limiting ====================

class RateLimiter:
    """Simple token bucket rate limiter"""
    
    def __init__(self, requests_per_second: int = MAX_REQUESTS_PER_SECOND):
        self.capacity = requests_per_second
        self.tokens = requests_per_second
        self.last_refill = None
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        import time
        
        now = time.time()
        if self.last_refill is None:
            self.last_refill = now
            self.tokens = self.capacity
        
        # Refill tokens
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.capacity
        )
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        
        return False
