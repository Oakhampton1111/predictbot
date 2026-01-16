# Testing Guide

## Overview

The PredictBot Stack includes a comprehensive test suite covering unit tests, integration tests, and end-to-end tests. All tests are designed to run in **dry-run mode** by default, meaning no real trades are executed.

## Test Structure

```
tests/
├── __init__.py              # Test suite documentation
├── conftest.py              # Pytest fixtures and configuration
├── pytest.ini               # Pytest settings
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_conflict_detector.py
│   ├── test_news_feed.py
│   ├── test_kalshi_websocket.py
│   ├── test_event_bus.py
│   ├── test_openrouter_adapter.py
│   ├── test_llm_router.py
│   └── test_agents.py
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_event_bus_integration.py
│   ├── test_ai_orchestrator_integration.py
│   └── test_trading_integration.py
└── e2e/                     # End-to-end tests
    ├── __init__.py
    └── test_dry_run_trading.py
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
python scripts/run_tests.py

# Run specific test types
python scripts/run_tests.py --unit          # Unit tests only
python scripts/run_tests.py --integration   # Integration tests only
python scripts/run_tests.py --e2e           # End-to-end tests only
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_event_bus.py

# Run specific test function
pytest tests/unit/test_event_bus.py::TestEventBus::test_publish_event

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Runner Options

```bash
python scripts/run_tests.py --help

Options:
  --unit, -u          Run unit tests only
  --integration, -i   Run integration tests only
  --e2e, -e           Run end-to-end tests only
  -t, --test PATH     Run specific test file
  --coverage, -c      Generate coverage report
  --verbose, -v       Verbose output
  --fast, -f          Skip slow tests
  --parallel, -p      Run tests in parallel
  --output, -o FILE   Output results to file (JUnit XML)
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation using mocks.

**Coverage:**
- `test_conflict_detector.py` - Strategy conflict detection and resolution
- `test_news_feed.py` - Multi-source news aggregation
- `test_kalshi_websocket.py` - Kalshi WebSocket streaming
- `test_event_bus.py` - Redis-based event bus
- `test_openrouter_adapter.py` - OpenRouter LLM adapter
- `test_llm_router.py` - Multi-provider LLM routing
- `test_agents.py` - AI trading agents

**Example:**
```python
@pytest.mark.asyncio
async def test_publish_event(event_bus, mock_redis):
    """Test publishing an event."""
    mock_redis.publish = AsyncMock(return_value=1)
    
    event = Event(
        type=EventType.TRADE_SIGNAL,
        source="test",
        data={"market_id": "0x123"},
    )
    
    result = await event_bus.publish(event)
    
    assert result is True
    mock_redis.publish.assert_called_once()
```

### Integration Tests

Integration tests verify communication between services.

**Coverage:**
- `test_event_bus_integration.py` - Service-to-service messaging
- `test_ai_orchestrator_integration.py` - Agent orchestration
- `test_trading_integration.py` - Trading workflow coordination

**Example:**
```python
@pytest.mark.asyncio
async def test_arbitrage_to_executor_flow(mock_redis):
    """Test event flow from arbitrage agent to executor."""
    executor_received = []
    
    bus = EventBus(redis_url="redis://localhost:6379")
    bus._redis = mock_redis
    
    async def executor_handler(event):
        executor_received.append(event)
    
    await bus.subscribe([EventType.TRADE_SIGNAL], executor_handler)
    
    # Arbitrage agent publishes trade signal
    signal = Event(
        type=EventType.TRADE_SIGNAL,
        source="arbitrage_agent",
        data={"opportunity_id": "arb-123"},
    )
    
    await bus._dispatch(signal)
    
    assert len(executor_received) == 1
```

### End-to-End Tests

E2E tests verify complete trading workflows in dry-run mode.

**Coverage:**
- `test_dry_run_trading.py` - Complete trading workflows
  - Arbitrage detection → Risk check → Simulated execution
  - News sentiment → Signal generation → Dry-run trade
  - Risk management enforcement
  - System health monitoring
  - Error recovery scenarios

**Example:**
```python
@pytest.mark.asyncio
async def test_complete_arbitrage_flow_dry_run(trading_system):
    """Test complete arbitrage flow from detection to simulated execution."""
    execution_log = []
    
    # Step 1: Market data shows arbitrage opportunity
    market_data = {
        "polymarket": {"market_id": "election-2024", "yes_price": 0.55},
        "kalshi": {"market_id": "PRES-2024", "yes_price": 0.50},
    }
    
    # Step 2: Arbitrage agent analyzes
    arb_result = await trading_system["agents"]["arbitrage"].analyze_opportunity(
        market_a=market_data["polymarket"],
        market_b=market_data["kalshi"],
    )
    
    # ... continues through risk check and simulated execution
    
    assert simulated_execution["dry_run"] is True
```

## Fixtures

Common fixtures are defined in `conftest.py`:

```python
# Mock Redis client
@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.publish = AsyncMock(return_value=1)
    return redis

# Mock HTTP session
@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.post = AsyncMock()
    return session

# Mock OpenRouter adapter
@pytest.fixture
def mock_openrouter_adapter():
    """Create a mock OpenRouter adapter."""
    adapter = AsyncMock()
    adapter.complete = AsyncMock(return_value=MagicMock(
        content='{"result": "success"}',
        model="anthropic/claude-3.5-sonnet",
    ))
    return adapter

# Sample data fixtures
@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "market_id": "0x123abc",
        "platform": "polymarket",
        "yes_price": 0.55,
        "no_price": 0.45,
        "volume_24h": 50000,
    }
```

## CI/CD Integration

Tests run automatically on GitHub Actions:

```yaml
# .github/workflows/ci.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements-test.txt
      - run: pytest tests/unit/ --cov=. --cov-report=xml

  integration-tests:
    needs: unit-tests
    services:
      redis:
        image: redis:7-alpine
    steps:
      - run: pytest tests/integration/

  e2e-tests:
    needs: integration-tests
    steps:
      - run: pytest tests/e2e/
```

## Coverage Requirements

- **Minimum coverage:** 60%
- **Target coverage:** 80%

Generate coverage report:
```bash
pytest tests/ --cov=. --cov-report=html
open coverage_report/index.html
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit Tests - Component Name
===========================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

class TestComponentName:
    """Tests for ComponentName class."""
    
    @pytest.fixture
    def component(self, mock_redis):
        """Create component with mocked dependencies."""
        comp = ComponentName()
        comp._redis = mock_redis
        return comp
    
    @pytest.mark.asyncio
    async def test_feature_success(self, component):
        """Test successful feature execution."""
        result = await component.do_something()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_feature_error_handling(self, component):
        """Test error handling."""
        component._dependency.method = AsyncMock(
            side_effect=Exception("Error")
        )
        
        with pytest.raises(Exception):
            await component.do_something()
```

### Integration Test Template

```python
"""
Integration Tests - Feature Name
================================
"""

import pytest

class TestFeatureIntegration:
    """Integration tests for feature."""
    
    @pytest.mark.asyncio
    async def test_service_communication(self, mock_redis):
        """Test communication between services."""
        # Set up services
        service_a = ServiceA()
        service_b = ServiceB()
        
        # Test interaction
        result = await service_a.call_service_b()
        
        assert result is not None
```

## Troubleshooting

### Common Issues

1. **Async test not running:**
   ```python
   # Ensure you have the marker
   @pytest.mark.asyncio
   async def test_async_function():
       pass
   ```

2. **Mock not working:**
   ```python
   # Use AsyncMock for async functions
   mock.async_method = AsyncMock(return_value=result)
   
   # Use MagicMock for sync functions
   mock.sync_method = MagicMock(return_value=result)
   ```

3. **Redis connection error:**
   ```bash
   # Start Redis for integration tests
   docker run -d -p 6379:6379 redis:7-alpine
   ```

4. **Import errors:**
   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=$PWD
   pytest tests/
   ```

## Best Practices

1. **Isolate tests** - Each test should be independent
2. **Use fixtures** - Share common setup code
3. **Mock external services** - Don't call real APIs in tests
4. **Test edge cases** - Include error scenarios
5. **Keep tests fast** - Mark slow tests with `@pytest.mark.slow`
6. **Use descriptive names** - Test names should explain what's being tested
7. **Dry-run by default** - Never execute real trades in tests
