"""
Unit Tests - Event Bus
======================

Tests for the Redis-based event bus system.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.event_bus import (
    EventBus,
    AsyncEventBus,
    Event,
    EventType,
    EventPriority,
    create_event_bus,
)


class TestEventType:
    """Tests for EventType enum."""
    
    def test_trading_event_types(self):
        """Test trading event types exist."""
        assert EventType.TRADE_EXECUTED.value == "trade.executed"
        assert EventType.TRADE_FAILED.value == "trade.failed"
        assert EventType.ORDER_PLACED.value == "order.placed"
    
    def test_strategy_event_types(self):
        """Test strategy event types exist."""
        assert EventType.STRATEGY_STARTED.value == "strategy.started"
        assert EventType.STRATEGY_STOPPED.value == "strategy.stopped"
    
    def test_ai_event_types(self):
        """Test AI event types exist."""
        assert EventType.AI_CYCLE_STARTED.value == "ai.cycle.started"
        assert EventType.AI_SIGNAL_GENERATED.value == "ai.signal.generated"
    
    def test_risk_event_types(self):
        """Test risk event types exist."""
        assert EventType.CIRCUIT_BREAKER_TRIGGERED.value == "risk.circuit_breaker"
        assert EventType.DAILY_LOSS_LIMIT_REACHED.value == "risk.daily_loss_limit"


class TestEventPriority:
    """Tests for EventPriority enum."""
    
    def test_priority_values(self):
        """Test priority ordering."""
        assert EventPriority.CRITICAL.value < EventPriority.HIGH.value
        assert EventPriority.HIGH.value < EventPriority.NORMAL.value
        assert EventPriority.NORMAL.value < EventPriority.LOW.value
    
    def test_specific_values(self):
        """Test specific priority values."""
        assert EventPriority.CRITICAL.value == 1
        assert EventPriority.HIGH.value == 2
        assert EventPriority.NORMAL.value == 3
        assert EventPriority.LOW.value == 4


class TestEvent:
    """Tests for Event dataclass."""
    
    def test_create_event(self):
        """Test creating an event."""
        event = Event(
            event_type="trade.executed",
            data={"trade_id": "123", "amount": 100},
            timestamp="2024-01-15T10:00:00Z",
            source_service="executor",
            correlation_id="corr-456",
        )
        
        assert event.event_type == "trade.executed"
        assert event.data["trade_id"] == "123"
        assert event.source_service == "executor"
    
    def test_event_with_priority(self):
        """Test event with custom priority."""
        event = Event(
            event_type="risk.circuit_breaker",
            data={"reason": "Loss limit"},
            timestamp="2024-01-15T10:00:00Z",
            source_service="risk_manager",
            correlation_id="corr-789",
            priority=EventPriority.CRITICAL.value,
        )
        
        assert event.priority == EventPriority.CRITICAL.value
    
    def test_event_default_priority(self):
        """Test event default priority."""
        event = Event(
            event_type="market.data.update",
            data={},
            timestamp="2024-01-15T10:00:00Z",
            source_service="market_feed",
            correlation_id="corr-000",
        )
        
        assert event.priority == EventPriority.NORMAL.value
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = Event(
            event_type="trade.executed",
            data={"trade_id": "123"},
            timestamp="2024-01-15T10:00:00Z",
            source_service="executor",
            correlation_id="corr-456",
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "trade.executed"
        assert data["source_service"] == "executor"
        assert "timestamp" in data
        assert "correlation_id" in data
    
    def test_event_from_dict(self):
        """Test creating event from dictionary."""
        data = {
            "event_type": "ai.signal.generated",
            "data": {"signal": "buy"},
            "timestamp": "2024-01-15T10:00:00Z",
            "source_service": "ai_agent",
            "correlation_id": "corr-abc",
            "priority": 2,
        }
        
        event = Event.from_dict(data)
        
        assert event.event_type == "ai.signal.generated"
        assert event.source_service == "ai_agent"
        assert event.priority == 2


class TestEventBus:
    """Tests for synchronous EventBus class."""
    
    @pytest.fixture
    def event_bus(self):
        """Create an event bus for testing."""
        bus = EventBus(
            redis_url="redis://localhost:6379",
            service_name="test_service"
        )
        return bus
    
    def test_init(self, event_bus):
        """Test event bus initialization."""
        assert event_bus.service_name == "test_service"
        assert event_bus.redis_url == "redis://localhost:6379"
        assert event_bus._connected is False
    
    def test_get_channel(self, event_bus):
        """Test channel name generation."""
        channel = event_bus._get_channel(EventType.TRADE_EXECUTED)
        assert channel == "predictbot:events:trade.executed"
    
    def test_get_pattern(self, event_bus):
        """Test pattern generation."""
        pattern = event_bus._get_pattern("trade.*")
        assert pattern == "predictbot:events:trade.*"
    
    @patch('redis.from_url')
    def test_connect_success(self, mock_redis_from_url, event_bus):
        """Test successful connection."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.pubsub.return_value = MagicMock()
        mock_redis_from_url.return_value = mock_redis
        
        result = event_bus.connect()
        
        assert result is True
        assert event_bus._connected is True
    
    @patch('redis.from_url')
    def test_connect_failure(self, mock_redis_from_url, event_bus):
        """Test connection failure."""
        import redis
        mock_redis_from_url.side_effect = redis.ConnectionError("Connection refused")
        
        result = event_bus.connect()
        
        assert result is False
        assert event_bus._connected is False


class TestAsyncEventBus:
    """Tests for AsyncEventBus class."""
    
    @pytest.fixture
    def async_event_bus(self):
        """Create an async event bus for testing."""
        bus = AsyncEventBus(
            redis_url="redis://localhost:6379",
            service_name="async_test_service"
        )
        return bus
    
    def test_init(self, async_event_bus):
        """Test async event bus initialization."""
        assert async_event_bus.service_name == "async_test_service"
        assert async_event_bus._connected is False
        assert async_event_bus._running is False
    
    @pytest.mark.asyncio
    async def test_connect_success(self, async_event_bus):
        """Test successful async connection."""
        with patch('redis.asyncio.from_url', new_callable=AsyncMock) as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.pubsub.return_value = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            result = await async_event_bus.connect()
            
            assert result is True
            assert async_event_bus._connected is True


class TestCreateEventBus:
    """Tests for factory function."""
    
    def test_create_sync_event_bus(self):
        """Test creating synchronous event bus."""
        bus = create_event_bus(
            redis_url="redis://localhost:6379",
            service_name="test",
            async_mode=False
        )
        
        assert isinstance(bus, EventBus)
    
    def test_create_async_event_bus(self):
        """Test creating asynchronous event bus."""
        bus = create_event_bus(
            redis_url="redis://localhost:6379",
            service_name="test",
            async_mode=True
        )
        
        assert isinstance(bus, AsyncEventBus)
