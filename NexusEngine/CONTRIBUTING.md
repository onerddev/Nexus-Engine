# Contributing to NexusEngine Omega

We welcome contributions! This guide will help you get started.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Constructive criticism only
- Report issues privately to maintainers

## Getting Started

### Development Setup

```bash
# Clone and setup
git clone https://github.com/nexusengine/nexus-omega.git
cd NexusEngine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build C++ core
mkdir cpp/build && cd cpp/build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
cd ../..

# Build Cython bindings
python setup.py build_ext --inplace

# Verify setup
python -c "import nexus_engine; print('✓ Setup successful')"
```

### Project Structure

```
NexusEngine/
├── cpp/              # C++20 core (modify carefully)
├── cython/          # Python-C++ bridge
├── python/          # Pure Python modules
├── api/             # FastAPI application
├── sql/             # Database schema
├── tests/           # Test suite
├── docs/            # Documentation
└── ...
```

## Development Workflow

### 1. Fork & Branch

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Or hotfix from main
git checkout main
git checkout -b hotfix/my-fix
```

### 2. Make Changes

```bash
# Python changes
cd python/
# Edit files...

# C++ changes
cd cpp/src/
# Edit files...

# Rebuild if needed
cd cpp/build && make -j$(nproc) && cd ../..
```

### 3. Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_binary_processor.py::test_xor -v

# Coverage
pytest --cov=api --cov=python --cov-report=html

# Benchmark
python tests/benchmark.py
```

### 4. Code Quality

```bash
# Format code
black python/ api/ tests/

# Import sorting
isort python/ api/ tests/

# Type checking
mypy python/ --ignore-missing-imports

# Linting
flake8 python/ api/ --max-line-length=120

# Security scan
bandit -r python/ api/
```

### 5. Commit & Push

```bash
# Commit with clear message
git add .
git commit -m "feat: add feature description"

# Or for fixes
git commit -m "fix: specific fix description"

# Push to fork
git push origin feature/my-feature
```

### 6. Pull Request

1. Go to GitHub
2. Create PR from your branch → upstream develop
3. Fill PR template:
   - Description of changes
   - Tests added
   - Documentation updates
   - Breaking changes (if any)
4. Wait for CI checks to pass
5. Request review from maintainers

## Commit Message Guidelines

### Format
```
<type>: <subject>

<body>

<footer>
```

### Types
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting, missing semicolons)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Adding/updating tests
- `build` - Build system changes
- `ci` - CI/CD pipeline changes

### Example
```
feat: implement lock-free queue algorithm

- Add atomic operations for thread-safe operations
- Reduce latency to sub-microsecond levels
- Include comprehensive performance tests

Closes #42
```

## Code Style

### Python
```python
# Use type hints
def compute(value: int, iterations: int) -> float:
    """Compute result using algorithm.
    
    Args:
        value: Input integer value
        iterations: Number of iterations
        
    Returns:
        Computed result as float
    """
    pass

# Use f-strings
result = f"Value: {value}, Iterations: {iterations}"

# Use pathlib
from pathlib import Path
config_file = Path("config.json")
```

### C++
```cpp
// Use modern C++ features
auto result = vector | std::views::filter([](int x) { return x > 0; });

// Use const correctly
const auto& metrics = engine.get_metrics();

// Use noexcept where applicable
void process() noexcept { }

// Meaningful variable names
auto processed_items = metrics.processed_items;
```

## Testing Requirements

### Python Tests
```python
import pytest

def test_binary_xor():
    """Test XOR operation."""
    result = compute_xor(0b1010, 0b1100)
    assert result == 0b0110

@pytest.mark.parametrize("a,b,expected", [
    (1, 1, 0),
    (1, 0, 1),
])
def test_xor_table(a, b, expected):
    assert compute_xor(a, b) == expected
```

### C++ Tests
```cpp
#include <gtest/gtest.h>
#include "binary_processor.hpp"

TEST(BinaryProcessor, XorOperation) {
    uint64_t result = nexus::BinaryProcessor::xor_op(0xFFFF, 0xAAAA);
    EXPECT_EQ(result, 0x5555);
}
```

### Test Coverage
- Aim for >80% code coverage
- Test happy paths AND edge cases
- Test error conditions
- No test should depend on another

## Documentation

### Docstring Format (Python)
```python
def process_data(input: np.ndarray) -> np.ndarray:
    """Process input data using algorithm.
    
    This function applies the core algorithm to the input data,
    returning the processed result.
    
    Args:
        input: Input numpy array of shape (N, M)
        
    Returns:
        Processed array of shape (N, M)
        
    Raises:
        ValueError: If input shape is invalid
        
    Example:
        >>> data = np.array([[1, 2], [3, 4]])
        >>> result = process_data(data)
        >>> result.shape
        (2, 2)
    """
```

### Update Documentation
- Add feature docs to [docs/](docs/)
- Update [README.md](README.md) if needed
- Add examples to docstrings
- Update API docs
- Add architecture notes if major change

## Performance Considerations

### Before Submitting
- Profile your changes
- Ensure no performance regression
- Add benchmarks for new features
- Document any trade-offs

```bash
# Profile Python code
python -m cProfile -s cumulative your_script.py | head -20

# Profile C++ code
perf record -g ./nexus_engine
perf report

# Benchmark
python tests/benchmark.py
```

## Review Process

### For Contributors
```
Your PR
  ↓
Automated Checks (tests, linting)
  ↓
Code Review (maintainers)
  ↓
Requested Changes (if any)
  ↓
Approval
  ↓
Merge
```

### For Reviewers
- Check code quality (style, tests)
- Verify tests are added
- Check for performance issues
- Verify documentation is updated
- Ensure no breaking changes (or noted)

## Branching Strategy

### Branch Names
```
feature/add-new-algorithm
fix/resolve-latency-issue
docs/update-api-reference
refactor/optimize-queue
test/improve-coverage
```

### Branch Protection
- `main` - Production ready, tagged releases
- `develop` - Integration branch
- Feature branches - Merged with PR

## Release Process

### Version Format: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Release Steps
```bash
# Update version
# Update CHANGELOG.md
# Create PR to main
# Merge and tag
git tag v1.0.0
git push --tags

# Build and publish
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Reporting Issues

### Use Issue Templates
1. **Bug Report** - Include:
   - Environment (OS, Python version, hardware)
   - Reproduction steps
   - Expected vs actual behavior
   - Error logs/traces

2. **Feature Request** - Include:
   - Use case/motivation
   - Proposed solution
   - Alternative approaches

3. **Documentation** - Include:
   - Section/file affected
   - Suggested improvement

## Getting Help

- **Questions** - Start a GitHub Discussion
- **Issues** - Search existing, then create issue
- **Chat** - Join community Discord/Slack
- **Email** - team@nexusengine.dev

## Maintainer Information

**Lead Maintainers:**
- @username1 - Core engine
- @username2 - API layer
- @username3 - Database/infrastructure

## License

By contributing, you agree your code will be under MIT License.

---

Thank you for contributing to NexusEngine Omega! 🚀
