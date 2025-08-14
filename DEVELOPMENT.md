# Development Guide

This document provides comprehensive guidance for developers working on the data-sources project.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [CI/CD Pipeline](#cicd-pipeline)
- [Contributing](#contributing)
- [Performance Guidelines](#performance-guidelines)
- [Security Considerations](#security-considerations)

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Make (optional, for convenience commands)

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/williamzujkowski/data-sources.git
   cd data-sources
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Verify setup:**
   ```bash
   python -m pytest tests/unit/
   python tools/validate_sources.py
   ```

### Development Tools

The project uses several development tools configured in `pyproject.toml`:

- **Black**: Code formatting (88 char line length)
- **isort**: Import sorting
- **flake8**: Linting with additional plugins
- **mypy**: Static type checking
- **bandit**: Security scanning
- **pytest**: Testing framework with coverage
- **pre-commit**: Git hooks for quality assurance

## Project Structure

```
data-sources/
├── .github/                    # GitHub workflows and configurations
│   ├── workflows/             # CI/CD workflows
│   └── dependabot.yml         # Dependabot configuration
├── config/                    # Configuration files
├── data-sources/              # Data source JSON files (organized by category)
├── docs/                      # Documentation
├── schemas/                   # JSON schemas for validation
├── tests/                     # Test suite
│   ├── benchmarks/           # Performance benchmarks
│   ├── fixtures/             # Test fixtures
│   ├── integration/          # Integration tests
│   └── unit/                 # Unit tests
├── tools/                     # Python tools and utilities
│   ├── fetch_sources.py      # Source data fetching
│   ├── score_sources.py      # Quality scoring
│   ├── validate_sources.py   # Schema validation
│   └── index_sources.py      # Search indexing
├── CLAUDE.md                  # AI development guidelines
├── DEVELOPMENT.md             # This file
├── pyproject.toml             # Project configuration
└── README.md                  # Project overview
```

### Key Components

- **Data Sources**: JSON files containing metadata about external data feeds
- **Schemas**: JSON schemas for validating data source structure
- **Tools**: Python utilities for managing, validating, and scoring data sources
- **Tests**: Comprehensive test suite including unit, integration, and benchmark tests

## Development Workflow

### Branch Strategy

- **main**: Production-ready code, protected branch
- **develop**: Integration branch for features (optional)
- **feature/\***: Feature development branches
- **hotfix/\***: Critical bug fixes
- **release/\***: Release preparation branches

### Development Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes following coding standards**

3. **Run tests and quality checks:**
   ```bash
   # Run all tests
   pytest
   
   # Run pre-commit hooks
   pre-commit run --all-files
   
   # Validate data sources
   python tools/validate_sources.py
   ```

4. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Create PR via GitHub interface
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/modifications
- `chore:` Maintenance tasks

## Testing

### Test Structure

- **Unit Tests**: Test individual functions and modules
- **Integration Tests**: Test component interactions
- **Benchmark Tests**: Performance measurement
- **End-to-End Tests**: Full workflow testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tools

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/benchmarks/

# Run tests for specific module
pytest tests/unit/test_fetch_sources.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Writing Tests

Follow these patterns when writing tests:

```python
import pytest
from unittest.mock import patch, mock_open

class TestYourFunction:
    """Test class for your_function."""
    
    def test_function_success(self):
        """Test successful execution."""
        # Arrange
        input_data = {"key": "value"}
        expected = "expected_result"
        
        # Act
        result = your_function(input_data)
        
        # Assert
        assert result == expected
    
    def test_function_error_handling(self):
        """Test error handling."""
        with pytest.raises(YourCustomError, match="Expected error message"):
            your_function(invalid_input)
    
    @patch('your_module.external_dependency')
    def test_function_with_mock(self, mock_dependency):
        """Test with mocked dependencies."""
        mock_dependency.return_value = "mocked_result"
        
        result = your_function()
        
        mock_dependency.assert_called_once()
        assert result == "expected_result"
```

### Test Coverage Requirements

- **Minimum coverage**: 80% overall
- **Critical components**: 95% coverage
- **New features**: 100% coverage required

## Code Quality

### Coding Standards

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions under 50 lines when possible
- Use descriptive variable and function names

### Type Annotations

```python
from typing import Dict, List, Optional, Any

def process_sources(
    sources: List[Dict[str, Any]], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """Process sources and return quality scores.
    
    Args:
        sources: List of source metadata dictionaries
        config: Optional configuration parameters
        
    Returns:
        Dictionary mapping source IDs to quality scores
        
    Raises:
        ValueError: If sources list is empty
    """
    if not sources:
        raise ValueError("Sources list cannot be empty")
    
    # Implementation here
    return {}
```

### Error Handling

- Use custom exception classes for specific error conditions
- Provide informative error messages
- Log errors with appropriate context
- Handle edge cases gracefully

```python
class DataSourceError(Exception):
    """Base exception for data source operations."""
    pass

class SourceValidationError(DataSourceError):
    """Exception raised when source validation fails."""
    pass

def validate_source(source: Dict[str, Any]) -> None:
    """Validate source data structure."""
    if not isinstance(source, dict):
        raise SourceValidationError(
            f"Expected dict, got {type(source).__name__}"
        )
    
    if "id" not in source:
        raise SourceValidationError("Missing required 'id' field")
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- **Formatting**: Black, isort
- **Linting**: flake8, mypy
- **Security**: bandit
- **Documentation**: markdownlint, yamllint
- **Testing**: pytest unit tests
- **Validation**: Custom data source validation

## CI/CD Pipeline

### GitHub Actions Workflows

1. **CI Workflow** (`.github/workflows/ci.yml`):
   - Linting and formatting checks
   - Multi-version Python testing (3.8-3.12)
   - Code coverage reporting
   - Security scanning
   - Performance benchmarking
   - Data source validation
   - Documentation building

2. **Security Workflow** (`.github/workflows/security.yml`):
   - SAST (Static Application Security Testing)
   - Dependency vulnerability scanning
   - Secret detection
   - License compliance

3. **Release Workflow** (`.github/workflows/release.yml`):
   - Semantic versioning
   - Automated releases
   - Package building
   - Asset uploads

4. **Performance Monitoring** (`.github/workflows/performance.yml`):
   - Benchmark execution
   - Memory profiling
   - Load testing
   - Performance regression detection

### Dependabot Configuration

Automated dependency updates are configured in `.github/dependabot.yml`:

- **Python dependencies**: Weekly updates on Mondays
- **GitHub Actions**: Weekly updates on Mondays
- **Automatic PR creation** with proper labeling and assignment

## Contributing

### Pull Request Process

1. **Fork and clone** the repository
2. **Create feature branch** from `main`
3. **Make changes** following coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Run quality checks** locally
7. **Submit PR** with clear description
8. **Respond to feedback** promptly

### PR Requirements

- [ ] All tests pass
- [ ] Code coverage maintained/improved
- [ ] Pre-commit hooks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] Semantic commit messages used

### Review Criteria

PRs are reviewed for:

- **Functionality**: Does it work as intended?
- **Code quality**: Follows standards and best practices?
- **Testing**: Adequate test coverage?
- **Documentation**: Clear and complete?
- **Security**: No security vulnerabilities?
- **Performance**: No significant regressions?

## Performance Guidelines

### Performance Targets

- **Source loading**: < 100ms per 100 sources
- **Schema validation**: < 50ms per source
- **Quality scoring**: < 10ms per source
- **Memory usage**: < 100MB for 1000 sources

### Optimization Strategies

1. **Use efficient data structures**
2. **Implement caching where appropriate**
3. **Minimize I/O operations**
4. **Use streaming for large datasets**
5. **Profile performance regularly**

### Benchmarking

Run performance benchmarks to ensure targets are met:

```bash
# Run benchmark tests
pytest tests/benchmarks/

# Profile memory usage
python -m memory_profiler tools/fetch_sources.py

# Time operations
time python tools/validate_sources.py
```

## Security Considerations

### Security Practices

1. **Input validation**: Validate all external inputs
2. **Secure dependencies**: Regular vulnerability scanning
3. **Secrets management**: Never commit secrets to repository
4. **Access control**: Principle of least privilege
5. **Logging**: No sensitive data in logs

### Security Tools

- **Bandit**: SAST for Python code
- **Safety**: Dependency vulnerability scanning
- **Semgrep**: Advanced static analysis
- **TruffleHog**: Secret detection
- **Dependabot**: Automated dependency updates

### Vulnerability Response

1. **Assessment**: Evaluate severity and impact
2. **Mitigation**: Develop and test fix
3. **Disclosure**: Follow responsible disclosure
4. **Documentation**: Update security documentation

## Troubleshooting

### Common Issues

**Tests failing locally:**
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"

# Clear pytest cache
pytest --cache-clear
```

**Pre-commit hooks failing:**
```bash
# Update pre-commit hooks
pre-commit autoupdate

# Run specific hook
pre-commit run black --all-files
```

**Import errors in tests:**
```bash
# Install package in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### Getting Help

- **Documentation**: Check docs/ directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Request review from maintainers

## Additional Resources

- [Project README](README.md)
- [CLAUDE.md](CLAUDE.md) - AI development guidelines
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Issue Templates](.github/ISSUE_TEMPLATE/)
- [GitHub Discussions](https://github.com/williamzujkowski/data-sources/discussions)

---

**Note**: This documentation is living and should be updated as the project evolves. All developers are encouraged to contribute improvements to this guide.
