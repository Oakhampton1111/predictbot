"""
PredictBot Stack - Test Configuration
======================================

Pytest fixtures and configuration for all tests.
"""

import os
import sys
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Async Event Loop
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Environment Setup
# =============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        "DRY_RUN": "1",
        "LOG_LEVEL": "DEBUG",
        "REDIS_URL": "redis://localhost:6379",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "OPENROUTER_API_KEY": "test-key",
        "OPENROUTER_ENABLED": "true",
        "OLLAMA_ENABLED": "false",
        "KALSHI_API_KEY": "test-kalshi-key",
        "KALSHI_API_SECRET": "test-kalshi-secret",
        "NEWSAPI_KEY": "test-newsapi-key",
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


# =============================================================================
# Mock Redis
# =============================================================================

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.publish = AsyncMock(return_value=1)
    redis.subscribe = AsyncMock()
    redis.close = AsyncMock()
    
    # For scan_iter
    async def mock_scan_iter(pattern):
        return
        yield  # Make it an async generator
    redis.scan_iter = mock_scan_iter
    
    return redis


# =============================================================================
# Mock HTTP Session
# =============================================================================

@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session."""
    session = AsyncMock()
    
    # Mock response
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={})
    response.text = AsyncMock(return_value="")
    response.raise_for_status = MagicMock()
    
    # Context manager for requests
    session.get = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=response)))
    session.post = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=response)))
    session.close = AsyncMock()
    session.closed = False
    
    return session


# =============================================================================
# Mock Event Bus
# =============================================================================

@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    event_bus.subscribe = AsyncMock()
    event_bus.unsubscribe = AsyncMock()
    event_bus.close = AsyncMock()
    return event_bus


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "market_id": "0x123abc",
        "platform": "polymarket",
        "question": "Will Bitcoin reach $100k by end of 2024?",
        "yes_price": 0.65,
        "no_price": 0.35,
        "volume": 150000,
        "liquidity": 50000,
    }


@pytest.fixture
def sample_trade_intent():
    """Sample trade intent for testing."""
    return {
        "strategy": "arbitrage",
        "platform": "polymarket",
        "market_id": "0x123abc",
        "direction": "buy",
        "side": "yes",
        "size": 100.0,
        "priority": 80,
    }


@pytest.fixture
def sample_news_article():
    """Sample news article for testing."""
    from datetime import datetime
    return {
        "id": "abc123",
        "title": "Bitcoin Surges Past $90,000",
        "description": "Cryptocurrency markets rally as Bitcoin reaches new highs.",
        "content": "Full article content here...",
        "url": "https://example.com/article",
        "source": "newsapi",
        "source_name": "CryptoNews",
        "published_at": datetime.utcnow().isoformat(),
        "author": "John Doe",
    }


@pytest.fixture
def sample_orderbook():
    """Sample orderbook data for testing."""
    return {
        "market_ticker": "BTC-100K-2024",
        "yes_bids": [{"price": 65, "quantity": 100}, {"price": 64, "quantity": 200}],
        "yes_asks": [{"price": 66, "quantity": 150}, {"price": 67, "quantity": 100}],
        "no_bids": [{"price": 34, "quantity": 100}],
        "no_asks": [{"price": 35, "quantity": 150}],
    }


# =============================================================================
# LLM Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "content": "Based on my analysis, the probability is 0.72.",
        "model": "anthropic/claude-3.5-sonnet",
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 50,
            "total_tokens": 200,
        },
        "finish_reason": "stop",
    }


@pytest.fixture
def mock_openrouter_adapter(mock_llm_response):
    """Create a mock OpenRouter adapter."""
    adapter = AsyncMock()
    adapter.model_name = "openrouter/anthropic/claude-3.5-sonnet"
    adapter.set_model = MagicMock()
    adapter.set_fallbacks = MagicMock()
    
    # Mock response object
    from dataclasses import dataclass
    
    @dataclass
    class MockResponse:
        content: str = mock_llm_response["content"]
        model: str = mock_llm_response["model"]
        usage: dict = None
        finish_reason: str = "stop"
        latency_ms: float = 150.0
        cost: float = 0.001
        
        def __post_init__(self):
            if self.usage is None:
                self.usage = mock_llm_response["usage"]
    
    adapter.ainvoke = AsyncMock(return_value=MockResponse())
    adapter.close = AsyncMock()
    adapter.get_stats = MagicMock(return_value={"total_cost": 0.01})
    
    return adapter


# =============================================================================
# Database Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# =============================================================================
# Cleanup
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test."""
    yield
    # Any cleanup code here
