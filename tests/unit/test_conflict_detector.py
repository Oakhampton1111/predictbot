"""
Unit Tests - Conflict Detector
==============================

Tests for the strategy conflict detection and resolution module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.conflict_detector import (
    ConflictDetector,
    ConflictResult,
    ConflictType,
    TradeIntent,
    MarketLock,
    StrategyPriority,
    create_conflict_detector,
)


class TestStrategyPriority:
    """Tests for StrategyPriority enum."""
    
    def test_priority_ordering(self):
        """Test that priorities are correctly ordered."""
        assert StrategyPriority.EMERGENCY > StrategyPriority.ARBITRAGE
        assert StrategyPriority.ARBITRAGE > StrategyPriority.AI_TRADING
        assert StrategyPriority.AI_TRADING > StrategyPriority.SPIKE
        assert StrategyPriority.SPIKE > StrategyPriority.MARKET_MAKING
        assert StrategyPriority.MARKET_MAKING > StrategyPriority.MANUAL
        assert StrategyPriority.MANUAL > StrategyPriority.DEFAULT
    
    def test_priority_values(self):
        """Test specific priority values."""
        assert StrategyPriority.EMERGENCY == 100
        assert StrategyPriority.ARBITRAGE == 80
        assert StrategyPriority.DEFAULT == 10


class TestConflictType:
    """Tests for ConflictType enum."""
    
    def test_conflict_types(self):
        """Test all conflict types exist."""
        assert ConflictType.MARKET_LOCK == "market_lock"
        assert ConflictType.POSITION_LIMIT == "position_limit"
        assert ConflictType.CAPITAL_LIMIT == "capital_limit"
        assert ConflictType.OPPOSING_TRADE == "opposing_trade"
        assert ConflictType.RATE_LIMIT == "rate_limit"
        assert ConflictType.COOLDOWN == "cooldown"


class TestTradeIntent:
    """Tests for TradeIntent dataclass."""
    
    def test_create_trade_intent(self):
        """Test creating a trade intent."""
        intent = TradeIntent(
            strategy="arbitrage",
            platform="polymarket",
            market_id="0x123",
            direction="buy",
            side="yes",
            size=100.0,
            priority=StrategyPriority.ARBITRAGE,
        )
        
        assert intent.strategy == "arbitrage"
        assert intent.platform == "polymarket"
        assert intent.market_id == "0x123"
        assert intent.direction == "buy"
        assert intent.side == "yes"
        assert intent.size == 100.0
        assert intent.priority == StrategyPriority.ARBITRAGE
    
    def test_default_priority(self):
        """Test default priority value."""
        intent = TradeIntent(
            strategy="test",
            platform="test",
            market_id="test",
            direction="buy",
            side="yes",
            size=50.0,
        )
        
        assert intent.priority == StrategyPriority.DEFAULT


class TestMarketLock:
    """Tests for MarketLock dataclass."""
    
    def test_create_market_lock(self):
        """Test creating a market lock."""
        now = datetime.utcnow()
        lock = MarketLock(
            market_id="0x123",
            platform="polymarket",
            strategy="arbitrage",
            priority=80,
            locked_at=now,
            expires_at=now + timedelta(seconds=30),
            trade_direction="buy",
        )
        
        assert lock.market_id == "0x123"
        assert lock.platform == "polymarket"
        assert lock.strategy == "arbitrage"
        assert lock.priority == 80
        assert lock.trade_direction == "buy"
    
    def test_is_expired_false(self):
        """Test lock is not expired."""
        now = datetime.utcnow()
        lock = MarketLock(
            market_id="0x123",
            platform="polymarket",
            strategy="arbitrage",
            priority=80,
            locked_at=now,
            expires_at=now + timedelta(seconds=30),
        )
        
        assert lock.is_expired is False
    
    def test_is_expired_true(self):
        """Test lock is expired."""
        now = datetime.utcnow()
        lock = MarketLock(
            market_id="0x123",
            platform="polymarket",
            strategy="arbitrage",
            priority=80,
            locked_at=now - timedelta(seconds=60),
            expires_at=now - timedelta(seconds=30),
        )
        
        assert lock.is_expired is True
    
    def test_to_dict(self):
        """Test converting lock to dictionary."""
        now = datetime.utcnow()
        lock = MarketLock(
            market_id="0x123",
            platform="polymarket",
            strategy="arbitrage",
            priority=80,
            locked_at=now,
            expires_at=now + timedelta(seconds=30),
            trade_direction="buy",
        )
        
        data = lock.to_dict()
        
        assert data["market_id"] == "0x123"
        assert data["platform"] == "polymarket"
        assert data["strategy"] == "arbitrage"
        assert data["priority"] == 80
        assert data["trade_direction"] == "buy"
    
    def test_from_dict(self):
        """Test creating lock from dictionary."""
        now = datetime.utcnow()
        data = {
            "market_id": "0x123",
            "platform": "polymarket",
            "strategy": "arbitrage",
            "priority": 80,
            "locked_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=30)).isoformat(),
            "trade_direction": "buy",
        }
        
        lock = MarketLock.from_dict(data)
        
        assert lock.market_id == "0x123"
        assert lock.platform == "polymarket"
        assert lock.strategy == "arbitrage"
        assert lock.priority == 80


class TestConflictResult:
    """Tests for ConflictResult dataclass."""
    
    def test_allowed_result(self):
        """Test allowed conflict result."""
        result = ConflictResult(allowed=True)
        
        assert result.allowed is True
        assert result.conflict_type is None
        assert result.reason is None
    
    def test_denied_result(self):
        """Test denied conflict result."""
        result = ConflictResult(
            allowed=False,
            conflict_type=ConflictType.MARKET_LOCK,
            reason="Market locked by arbitrage",
            blocking_strategy="arbitrage",
            wait_time_seconds=15.0,
        )
        
        assert result.allowed is False
        assert result.conflict_type == ConflictType.MARKET_LOCK
        assert result.reason == "Market locked by arbitrage"
        assert result.blocking_strategy == "arbitrage"
        assert result.wait_time_seconds == 15.0
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = ConflictResult(
            allowed=False,
            conflict_type=ConflictType.POSITION_LIMIT,
            reason="Would exceed position limit",
        )
        
        data = result.to_dict()
        
        assert data["allowed"] is False
        assert data["conflict_type"] == "position_limit"
        assert data["reason"] == "Would exceed position limit"


class TestConflictDetector:
    """Tests for ConflictDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a conflict detector for testing."""
        detector = ConflictDetector(
            redis_url="redis://localhost:6379",
            config={
                "max_position_per_market": 500,
                "max_total_position": 5000,
                "strategy_capital_limits": {
                    "arbitrage": 2000,
                    "spike": 1000,
                },
                "cooldown_periods": {
                    "spike": 60,
                },
            }
        )
        return detector
    
    def test_init(self, detector):
        """Test detector initialization."""
        assert detector.max_position_per_market == 500
        assert detector.max_total_position == 5000
        assert detector.strategy_capital_limits["arbitrage"] == 2000
    
    def test_get_lock_key(self, detector):
        """Test lock key generation."""
        key = detector._get_lock_key("polymarket", "0x123")
        assert key == "predictbot:lock:polymarket:0x123"
    
    def test_get_position_key(self, detector):
        """Test position key generation."""
        key = detector._get_position_key("polymarket", "0x123")
        assert key == "predictbot:position:polymarket:0x123"
    
    def test_get_cooldown_key(self, detector):
        """Test cooldown key generation."""
        key = detector._get_cooldown_key("spike", "polymarket", "0x123")
        assert key == "predictbot:cooldown:spike:polymarket:0x123"
    
    @pytest.mark.asyncio
    async def test_check_conflict_allowed_no_redis(self, detector):
        """Test conflict check when trade is allowed (no Redis)."""
        intent = TradeIntent(
            strategy="arbitrage",
            platform="polymarket",
            market_id="0x123",
            direction="buy",
            side="yes",
            size=100.0,
            priority=StrategyPriority.ARBITRAGE,
        )
        
        result = await detector.check_conflict(intent)
        
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_acquire_lock_local(self, detector):
        """Test acquiring a market lock (local fallback)."""
        intent = TradeIntent(
            strategy="arbitrage",
            platform="polymarket",
            market_id="0x123",
            direction="buy",
            side="yes",
            size=100.0,
            priority=StrategyPriority.ARBITRAGE,
        )
        
        lock = await detector.acquire_lock(intent, duration_seconds=30)
        
        assert lock is not None
        assert lock.market_id == "0x123"
        assert lock.strategy == "arbitrage"
    
    @pytest.mark.asyncio
    async def test_release_lock_local(self, detector):
        """Test releasing a market lock (local fallback)."""
        intent = TradeIntent(
            strategy="arbitrage",
            platform="polymarket",
            market_id="0x123",
            direction="buy",
            side="yes",
            size=100.0,
            priority=StrategyPriority.ARBITRAGE,
        )
        
        lock = await detector.acquire_lock(intent, duration_seconds=30)
        result = await detector.release_lock(lock)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_position_local(self, detector):
        """Test updating position tracking (local fallback)."""
        new_position = await detector.update_position(
            platform="polymarket",
            market_id="0x123",
            delta=50.0,
        )
        
        assert new_position == 50.0
        
        # Update again
        new_position = await detector.update_position(
            platform="polymarket",
            market_id="0x123",
            delta=25.0,
        )
        
        assert new_position == 75.0
    
    @pytest.mark.asyncio
    async def test_get_stats(self, detector):
        """Test getting detector statistics."""
        stats = await detector.get_stats()
        
        assert "active_locks" in stats
        assert "total_position" in stats
        assert "max_position_per_market" in stats


class TestCreateConflictDetector:
    """Tests for factory function."""
    
    def test_create_from_environment(self):
        """Test creating detector from environment."""
        detector = create_conflict_detector()
        
        assert detector is not None
        assert isinstance(detector, ConflictDetector)
    
    def test_create_with_config(self):
        """Test creating detector with custom config."""
        config = {
            "max_position_per_market": 1000,
            "max_total_position": 10000,
        }
        
        detector = create_conflict_detector(config=config)
        
        assert detector.max_position_per_market == 1000
        assert detector.max_total_position == 10000
