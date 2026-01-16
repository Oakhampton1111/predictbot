"""
PredictBot Stack - Test Suite
==============================

Comprehensive test suite covering:
- Unit tests for shared modules
- Unit tests for AI orchestrator
- Integration tests for service communication
- End-to-end dry-run tests

Test Categories:
- tests/unit/          - Unit tests for individual components
- tests/integration/   - Integration tests for service interactions
- tests/e2e/           - End-to-end tests for full workflows

Running Tests:
    # Run all tests
    pytest tests/ -v

    # Run unit tests only
    pytest tests/unit/ -v

    # Run integration tests only
    pytest tests/integration/ -v

    # Run with coverage
    pytest tests/ --cov=shared --cov=modules --cov-report=html
"""

__version__ = "1.0.0"
