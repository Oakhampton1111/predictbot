"""
PredictBot - Strategy Conflict Detection
=========================================

Advanced conflict detection and resolution for multi-strategy trading.

Features:
- Market locking to prevent simultaneous trades
- Strategy priority queue
- Position conflict detection
- Capital allocation conflict resolution
- Cross-platform arbitrage conflict handling

This module ensures that multiple strategies don't compete for the same
markets or exceed risk limits when operating simultaneously.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from .logging_config import get_logger
    from .metrics import get_metrics_registry
    from .event_bus import EventBus
except ImportError:
    import logging
    def get_logger(name: str, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_metrics_registry():
        return None
    
    EventBus = None


class StrategyPriority(int, Enum):
    """Strategy priority levels (higher = more priority)."""
    EMERGENCY = 100      # Emergency stop, risk management
    ARBITRAGE = 80       # Time-sensitive arbitrage
    AI_TRADING = 60      # AI-driven trades
    SPIKE = 50           # Spike trading
    MARKET_MAKING = 40   # Market making
    MANUAL = 30          # Manual trades from admin
    DEFAULT = 10         # Default priority


class ConflictType(str, Enum):
    """Types of conflicts."""
    MARKET_LOCK = "market_lock"           # Market already locked by another strategy
    POSITION_LIMIT = "position_limit"     # Would exceed position limits
    CAPITAL_LIMIT = "capital_limit"       # Would exceed capital allocation
    OPPOSING_TRADE = "opposing_trade"     # Conflicting trade direction
    RATE_LIMIT = "rate_limit"             # Platform rate limit
    COOLDOWN = "cooldown"                 # Strategy cooldown period


@dataclass
class MarketLock:
    """Represents a lock on a market."""
    market_id: str
    platform: str
    strategy: str
    priority: int
    locked_at: datetime
    expires_at: datetime
    trade_direction: Optional[str] = None  # "buy" or "sell"
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "market_id": self.market_id,
            "platform": self.platform,
            "strategy": self.strategy,
            "priority": self.priority,
            "locked_at": self.locked_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "trade_direction": self.trade_direction,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketLock":
        return cls(
            market_id=data["market_id"],
            platform=data["platform"],
            strategy=data["strategy"],
            priority=data["priority"],
            locked_at=datetime.fromisoformat(data["locked_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            trade_direction=data.get("trade_direction"),
        )


@dataclass
class TradeIntent:
    """Represents an intent to trade."""
    strategy: str
    platform: str
    market_id: str
    direction: str  # "buy" or "sell"
    side: str       # "yes" or "no"
    size: float     # USD value
    priority: int = StrategyPriority.DEFAULT
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictResult:
    """Result of conflict check."""
    allowed: bool
    conflict_type: Optional[ConflictType] = None
    reason: Optional[str] = None
    blocking_strategy: Optional[str] = None
    wait_time_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "conflict_type": self.conflict_type.value if self.conflict_type else None,
            "reason": self.reason,
            "blocking_strategy": self.blocking_strategy,
            "wait_time_seconds": self.wait_time_seconds,
        }


class ConflictDetector:
    """
    Detects and resolves conflicts between trading strategies.
    
    Usage:
        detector = ConflictDetector(redis_url="redis://localhost:6379")
        
        # Check if trade is allowed
        intent = TradeIntent(
            strategy="arbitrage",
            platform="polymarket",
            market_id="0x123...",
            direction="buy",
            side="yes",
            size=100,
            priority=StrategyPriority.ARBITRAGE
        )
        
        result = await detector.check_conflict(intent)
        if result.allowed:
            # Acquire lock and execute trade
            lock = await detector.acquire_lock(intent)
            try:
                # Execute trade
                pass
            finally:
                await detector.release_lock(lock)
        else:
            print(f"Conflict: {result.reason}")
    """
    
    # Redis key prefixes
    LOCK_PREFIX = "predictbot:lock:"
    POSITION_PREFIX = "predictbot:position:"
    COOLDOWN_PREFIX = "predictbot:cooldown:"
    CAPITAL_PREFIX = "predictbot:capital:"
    
    # Default lock duration
    DEFAULT_LOCK_DURATION = 30  # seconds
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        event_bus: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize conflict detector.
        
        Args:
            redis_url: Redis connection URL
            event_bus: Optional EventBus for publishing events
            config: Optional configuration overrides
        """
        self.logger = get_logger("conflict_detector")
        self.metrics = get_metrics_registry()
        self.event_bus = event_bus
        
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._redis: Optional[redis.Redis] = None
        
        # Configuration
        self.config = config or {}
        self.max_position_per_market = self.config.get("max_position_per_market", 500)  # USD
        self.max_total_position = self.config.get("max_total_position", 5000)  # USD
        self.strategy_capital_limits = self.config.get("strategy_capital_limits", {
            "arbitrage": 2000,
            "market_making": 1500,
            "spike": 1000,
            "ai_trading": 1500,
        })
        self.cooldown_periods = self.config.get("cooldown_periods", {
            "spike": 60,      # 60 seconds between spike trades on same market
            "ai_trading": 300,  # 5 minutes between AI trades on same market
        })
        
        # In-memory fallback if Redis unavailable
        self._local_locks: Dict[str, MarketLock] = {}
        self._local_positions: Dict[str, float] = {}
        
        self.logger.info("Conflict detector initialized")
    
    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis connection."""
        if not REDIS_AVAILABLE:
            return None
        
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url)
                await self._redis.ping()
            except Exception as e:
                self.logger.warning(f"Redis connection failed, using local fallback: {e}")
                self._redis = None
        
        return self._redis
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    def _get_lock_key(self, platform: str, market_id: str) -> str:
        """Generate Redis key for market lock."""
        return f"{self.LOCK_PREFIX}{platform}:{market_id}"
    
    def _get_position_key(self, platform: str, market_id: str) -> str:
        """Generate Redis key for position tracking."""
        return f"{self.POSITION_PREFIX}{platform}:{market_id}"
    
    def _get_cooldown_key(self, strategy: str, platform: str, market_id: str) -> str:
        """Generate Redis key for cooldown tracking."""
        return f"{self.COOLDOWN_PREFIX}{strategy}:{platform}:{market_id}"
    
    async def check_conflict(self, intent: TradeIntent) -> ConflictResult:
        """
        Check if a trade intent conflicts with existing locks or limits.
        
        Args:
            intent: Trade intent to check
            
        Returns:
            ConflictResult indicating if trade is allowed
        """
        # Check market lock
        lock_result = await self._check_market_lock(intent)
        if not lock_result.allowed:
            return lock_result
        
        # Check position limits
        position_result = await self._check_position_limits(intent)
        if not position_result.allowed:
            return position_result
        
        # Check capital allocation
        capital_result = await self._check_capital_limits(intent)
        if not capital_result.allowed:
            return capital_result
        
        # Check cooldown
        cooldown_result = await self._check_cooldown(intent)
        if not cooldown_result.allowed:
            return cooldown_result
        
        # Check for opposing trades
        opposing_result = await self._check_opposing_trades(intent)
        if not opposing_result.allowed:
            return opposing_result
        
        return ConflictResult(allowed=True)
    
    async def _check_market_lock(self, intent: TradeIntent) -> ConflictResult:
        """Check if market is locked by another strategy."""
        lock_key = self._get_lock_key(intent.platform, intent.market_id)
        
        redis_client = await self._get_redis()
        if redis_client:
            lock_data = await redis_client.get(lock_key)
            if lock_data:
                lock = MarketLock.from_dict(json.loads(lock_data))
                if not lock.is_expired:
                    # Check if current strategy has higher priority
                    if intent.priority > lock.priority:
                        # Higher priority can preempt
                        return ConflictResult(allowed=True)
                    
                    wait_time = (lock.expires_at - datetime.utcnow()).total_seconds()
                    return ConflictResult(
                        allowed=False,
                        conflict_type=ConflictType.MARKET_LOCK,
                        reason=f"Market locked by {lock.strategy}",
                        blocking_strategy=lock.strategy,
                        wait_time_seconds=max(0, wait_time),
                    )
        else:
            # Local fallback
            if lock_key in self._local_locks:
                lock = self._local_locks[lock_key]
                if not lock.is_expired:
                    if intent.priority > lock.priority:
                        return ConflictResult(allowed=True)
                    
                    wait_time = (lock.expires_at - datetime.utcnow()).total_seconds()
                    return ConflictResult(
                        allowed=False,
                        conflict_type=ConflictType.MARKET_LOCK,
                        reason=f"Market locked by {lock.strategy}",
                        blocking_strategy=lock.strategy,
                        wait_time_seconds=max(0, wait_time),
                    )
        
        return ConflictResult(allowed=True)
    
    async def _check_position_limits(self, intent: TradeIntent) -> ConflictResult:
        """Check if trade would exceed position limits."""
        position_key = self._get_position_key(intent.platform, intent.market_id)
        
        current_position = 0.0
        redis_client = await self._get_redis()
        if redis_client:
            pos_data = await redis_client.get(position_key)
            if pos_data:
                current_position = float(pos_data)
        else:
            current_position = self._local_positions.get(position_key, 0.0)
        
        # Check market position limit
        new_position = current_position + intent.size
        if new_position > self.max_position_per_market:
            return ConflictResult(
                allowed=False,
                conflict_type=ConflictType.POSITION_LIMIT,
                reason=f"Would exceed market position limit (${new_position:.2f} > ${self.max_position_per_market})",
            )
        
        # Check total position limit
        total_position = await self._get_total_position()
        if total_position + intent.size > self.max_total_position:
            return ConflictResult(
                allowed=False,
                conflict_type=ConflictType.POSITION_LIMIT,
                reason=f"Would exceed total position limit (${total_position + intent.size:.2f} > ${self.max_total_position})",
            )
        
        return ConflictResult(allowed=True)
    
    async def _check_capital_limits(self, intent: TradeIntent) -> ConflictResult:
        """Check if trade would exceed strategy capital allocation."""
        strategy_limit = self.strategy_capital_limits.get(intent.strategy, float('inf'))
        
        # Get current strategy allocation
        current_allocation = await self._get_strategy_allocation(intent.strategy)
        
        if current_allocation + intent.size > strategy_limit:
            return ConflictResult(
                allowed=False,
                conflict_type=ConflictType.CAPITAL_LIMIT,
                reason=f"Would exceed {intent.strategy} capital limit (${current_allocation + intent.size:.2f} > ${strategy_limit})",
            )
        
        return ConflictResult(allowed=True)
    
    async def _check_cooldown(self, intent: TradeIntent) -> ConflictResult:
        """Check if strategy is in cooldown for this market."""
        cooldown_period = self.cooldown_periods.get(intent.strategy, 0)
        if cooldown_period == 0:
            return ConflictResult(allowed=True)
        
        cooldown_key = self._get_cooldown_key(intent.strategy, intent.platform, intent.market_id)
        
        redis_client = await self._get_redis()
        if redis_client:
            cooldown_until = await redis_client.get(cooldown_key)
            if cooldown_until:
                cooldown_time = datetime.fromisoformat(cooldown_until.decode())
                if datetime.utcnow() < cooldown_time:
                    wait_time = (cooldown_time - datetime.utcnow()).total_seconds()
                    return ConflictResult(
                        allowed=False,
                        conflict_type=ConflictType.COOLDOWN,
                        reason=f"Strategy {intent.strategy} in cooldown for this market",
                        wait_time_seconds=wait_time,
                    )
        
        return ConflictResult(allowed=True)
    
    async def _check_opposing_trades(self, intent: TradeIntent) -> ConflictResult:
        """Check for opposing trades on the same market."""
        lock_key = self._get_lock_key(intent.platform, intent.market_id)
        
        redis_client = await self._get_redis()
        if redis_client:
            lock_data = await redis_client.get(lock_key)
            if lock_data:
                lock = MarketLock.from_dict(json.loads(lock_data))
                if not lock.is_expired and lock.trade_direction:
                    # Check if directions conflict
                    if lock.trade_direction != intent.direction:
                        return ConflictResult(
                            allowed=False,
                            conflict_type=ConflictType.OPPOSING_TRADE,
                            reason=f"Opposing trade in progress ({lock.strategy} is {lock.trade_direction}ing)",
                            blocking_strategy=lock.strategy,
                        )
        
        return ConflictResult(allowed=True)
    
    async def _get_total_position(self) -> float:
        """Get total position across all markets."""
        total = 0.0
        
        redis_client = await self._get_redis()
        if redis_client:
            async for key in redis_client.scan_iter(f"{self.POSITION_PREFIX}*"):
                value = await redis_client.get(key)
                if value:
                    total += float(value)
        else:
            total = sum(self._local_positions.values())
        
        return total
    
    async def _get_strategy_allocation(self, strategy: str) -> float:
        """Get current capital allocation for a strategy."""
        # This would typically query the database for open positions
        # For now, return 0 as a placeholder
        return 0.0
    
    async def acquire_lock(
        self,
        intent: TradeIntent,
        duration_seconds: int = DEFAULT_LOCK_DURATION,
    ) -> Optional[MarketLock]:
        """
        Acquire a lock on a market for trading.
        
        Args:
            intent: Trade intent
            duration_seconds: Lock duration
            
        Returns:
            MarketLock if acquired, None if failed
        """
        lock_key = self._get_lock_key(intent.platform, intent.market_id)
        now = datetime.utcnow()
        
        lock = MarketLock(
            market_id=intent.market_id,
            platform=intent.platform,
            strategy=intent.strategy,
            priority=intent.priority,
            locked_at=now,
            expires_at=now + timedelta(seconds=duration_seconds),
            trade_direction=intent.direction,
        )
        
        redis_client = await self._get_redis()
        if redis_client:
            # Use SET NX for atomic lock acquisition
            success = await redis_client.set(
                lock_key,
                json.dumps(lock.to_dict()),
                nx=True,
                ex=duration_seconds,
            )
            
            if not success:
                # Check if we can preempt
                existing_data = await redis_client.get(lock_key)
                if existing_data:
                    existing = MarketLock.from_dict(json.loads(existing_data))
                    if intent.priority > existing.priority:
                        # Preempt lower priority lock
                        await redis_client.set(
                            lock_key,
                            json.dumps(lock.to_dict()),
                            ex=duration_seconds,
                        )
                        self.logger.info(
                            f"Preempted {existing.strategy} lock with {intent.strategy} "
                            f"(priority {existing.priority} < {intent.priority})"
                        )
                    else:
                        return None
        else:
            # Local fallback
            if lock_key in self._local_locks:
                existing = self._local_locks[lock_key]
                if not existing.is_expired and intent.priority <= existing.priority:
                    return None
            
            self._local_locks[lock_key] = lock
        
        self.logger.debug(f"Acquired lock: {intent.strategy} on {intent.platform}:{intent.market_id}")
        
        # Publish lock event
        if self.event_bus:
            await self.event_bus.publish("conflict.lock_acquired", lock.to_dict())
        
        return lock
    
    async def release_lock(self, lock: MarketLock) -> bool:
        """
        Release a market lock.
        
        Args:
            lock: Lock to release
            
        Returns:
            True if released successfully
        """
        lock_key = self._get_lock_key(lock.platform, lock.market_id)
        
        redis_client = await self._get_redis()
        if redis_client:
            # Verify we own the lock before releasing
            existing_data = await redis_client.get(lock_key)
            if existing_data:
                existing = MarketLock.from_dict(json.loads(existing_data))
                if existing.strategy == lock.strategy:
                    await redis_client.delete(lock_key)
                    self.logger.debug(f"Released lock: {lock.strategy} on {lock.platform}:{lock.market_id}")
                    return True
        else:
            if lock_key in self._local_locks:
                if self._local_locks[lock_key].strategy == lock.strategy:
                    del self._local_locks[lock_key]
                    return True
        
        return False
    
    async def set_cooldown(
        self,
        strategy: str,
        platform: str,
        market_id: str,
        duration_seconds: Optional[int] = None,
    ) -> None:
        """
        Set cooldown for a strategy on a market.
        
        Args:
            strategy: Strategy name
            platform: Platform name
            market_id: Market identifier
            duration_seconds: Cooldown duration (uses default if not specified)
        """
        if duration_seconds is None:
            duration_seconds = self.cooldown_periods.get(strategy, 60)
        
        cooldown_key = self._get_cooldown_key(strategy, platform, market_id)
        cooldown_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        redis_client = await self._get_redis()
        if redis_client:
            await redis_client.set(
                cooldown_key,
                cooldown_until.isoformat(),
                ex=duration_seconds,
            )
        
        self.logger.debug(f"Set cooldown: {strategy} on {platform}:{market_id} for {duration_seconds}s")
    
    async def update_position(
        self,
        platform: str,
        market_id: str,
        delta: float,
    ) -> float:
        """
        Update position tracking for a market.
        
        Args:
            platform: Platform name
            market_id: Market identifier
            delta: Position change (positive for buy, negative for sell)
            
        Returns:
            New position value
        """
        position_key = self._get_position_key(platform, market_id)
        
        redis_client = await self._get_redis()
        if redis_client:
            new_value = await redis_client.incrbyfloat(position_key, delta)
            return float(new_value)
        else:
            current = self._local_positions.get(position_key, 0.0)
            new_value = current + delta
            self._local_positions[position_key] = new_value
            return new_value
    
    async def get_active_locks(self) -> List[MarketLock]:
        """Get all active market locks."""
        locks = []
        
        redis_client = await self._get_redis()
        if redis_client:
            async for key in redis_client.scan_iter(f"{self.LOCK_PREFIX}*"):
                data = await redis_client.get(key)
                if data:
                    lock = MarketLock.from_dict(json.loads(data))
                    if not lock.is_expired:
                        locks.append(lock)
        else:
            for lock in self._local_locks.values():
                if not lock.is_expired:
                    locks.append(lock)
        
        return locks
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get conflict detector statistics."""
        active_locks = await self.get_active_locks()
        total_position = await self._get_total_position()
        
        return {
            "active_locks": len(active_locks),
            "locks_by_strategy": {},
            "total_position": total_position,
            "max_position_per_market": self.max_position_per_market,
            "max_total_position": self.max_total_position,
            "strategy_capital_limits": self.strategy_capital_limits,
        }


# Convenience function to create detector from environment
def create_conflict_detector(
    event_bus: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None,
) -> ConflictDetector:
    """
    Create a conflict detector from environment variables.
    
    Args:
        event_bus: Optional EventBus for publishing events
        config: Optional configuration overrides
        
    Returns:
        Configured ConflictDetector
    """
    return ConflictDetector(
        redis_url=os.environ.get("REDIS_URL"),
        event_bus=event_bus,
        config=config,
    )
