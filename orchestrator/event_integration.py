"""
Event Bus Integration for Orchestrator

Provides event publishing capabilities for the orchestrator service.
Integrates with the shared event bus for inter-service communication.
"""

import os
import sys
import asyncio
import threading
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Add shared module to path
sys.path.insert(0, '/app')

logger = logging.getLogger(__name__)

# Try to import event bus components
try:
    from shared.event_bus import AsyncEventBus, EventBus, EventType, EventPriority, Event
    from shared.event_schemas import (
        StrategyStartedData, StrategyPausedData, StrategyStoppedData,
        CircuitBreakerTriggeredData, DailyLossLimitReachedData,
        ServiceStartedData, ServiceStoppedData, ServiceHealthCheckData,
        EmergencyStopData
    )
    EVENT_BUS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Event bus not available: {e}")
    EVENT_BUS_AVAILABLE = False
    EventType = None
    EventPriority = None


class OrchestratorEventPublisher:
    """
    Event publisher for the orchestrator service.
    
    Publishes events for:
    - Service lifecycle (start, stop, health)
    - Risk events (circuit breaker, daily loss limit)
    - Strategy state changes
    - Emergency stop commands
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the event publisher.
        
        Args:
            redis_url: Redis connection URL (defaults to env var)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379')
        self.service_name = "orchestrator"
        self.event_bus: Optional[EventBus] = None
        self._async_event_bus: Optional[AsyncEventBus] = None
        self._connected = False
        self._event_handlers: Dict[str, Callable] = {}
    
    def connect(self) -> bool:
        """
        Connect to the event bus (synchronous).
        
        Returns:
            True if connected successfully
        """
        if not EVENT_BUS_AVAILABLE:
            logger.warning("Event bus not available, skipping connection")
            return False
        
        try:
            self.event_bus = EventBus(self.redis_url, self.service_name)
            if self.event_bus.connect():
                self._connected = True
                logger.info("Orchestrator connected to event bus")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to event bus: {e}")
        
        return False
    
    async def connect_async(self) -> bool:
        """
        Connect to the event bus (asynchronous).
        
        Returns:
            True if connected successfully
        """
        if not EVENT_BUS_AVAILABLE:
            logger.warning("Event bus not available, skipping connection")
            return False
        
        try:
            self._async_event_bus = AsyncEventBus(self.redis_url, self.service_name)
            if await self._async_event_bus.connect():
                self._connected = True
                logger.info("Orchestrator connected to async event bus")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to async event bus: {e}")
        
        return False
    
    def disconnect(self):
        """Disconnect from the event bus."""
        if self.event_bus:
            self.event_bus.disconnect()
        self._connected = False
        logger.info("Orchestrator disconnected from event bus")
    
    async def disconnect_async(self):
        """Disconnect from the async event bus."""
        if self._async_event_bus:
            await self._async_event_bus.disconnect()
        self._connected = False
        logger.info("Orchestrator disconnected from async event bus")
    
    def subscribe_to_emergency_stop(self, handler: Callable):
        """
        Subscribe to emergency stop commands.
        
        Args:
            handler: Callback function to handle emergency stop
        """
        if not EVENT_BUS_AVAILABLE or not self.event_bus:
            return
        
        def _handler(event: Event):
            logger.warning(f"Emergency stop received: {event.data}")
            handler(event.data)
        
        self.event_bus.subscribe(EventType.EMERGENCY_STOP, _handler)
        self._event_handlers['emergency_stop'] = _handler
        logger.info("Subscribed to emergency stop events")
    
    def start_listening(self):
        """Start listening for events in background thread."""
        if self.event_bus:
            self.event_bus.start_listening()
    
    def stop_listening(self):
        """Stop listening for events."""
        if self.event_bus:
            self.event_bus.stop_listening()
    
    # =========================================================================
    # Service Lifecycle Events
    # =========================================================================
    
    def publish_service_started(
        self,
        version: str,
        host: str = "0.0.0.0",
        port: int = 8080,
        config_hash: Optional[str] = None
    ):
        """Publish service started event."""
        if not self._can_publish():
            return
        
        import uuid
        instance_id = os.getenv('HOSTNAME', str(uuid.uuid4())[:8])
        
        self.event_bus.publish(
            EventType.SERVICE_STARTED,
            {
                "service_name": self.service_name,
                "service_version": version,
                "instance_id": instance_id,
                "host": host,
                "port": port,
                "config_hash": config_hash
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published service started event: {self.service_name} v{version}")
    
    def publish_service_stopped(
        self,
        stop_reason: str,
        uptime_seconds: int,
        graceful: bool = True
    ):
        """Publish service stopped event."""
        if not self._can_publish():
            return
        
        import uuid
        instance_id = os.getenv('HOSTNAME', str(uuid.uuid4())[:8])
        
        self.event_bus.publish(
            EventType.SERVICE_STOPPED,
            {
                "service_name": self.service_name,
                "instance_id": instance_id,
                "stop_reason": stop_reason,
                "uptime_seconds": uptime_seconds,
                "graceful": graceful
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published service stopped event: {stop_reason}")
    
    def publish_health_status(
        self,
        status: str,
        checks: Dict[str, bool],
        metrics: Dict[str, float],
        uptime_seconds: int
    ):
        """Publish health check event."""
        if not self._can_publish():
            return
        
        import uuid
        instance_id = os.getenv('HOSTNAME', str(uuid.uuid4())[:8])
        
        self.event_bus.publish(
            EventType.SERVICE_HEALTH_CHECK,
            {
                "service_name": self.service_name,
                "instance_id": instance_id,
                "status": status,
                "checks": checks,
                "metrics": metrics,
                "uptime_seconds": uptime_seconds
            },
            priority=EventPriority.LOW
        )
    
    # =========================================================================
    # Risk Events
    # =========================================================================
    
    def publish_circuit_breaker_triggered(
        self,
        trigger_type: str,
        trigger_reason: str,
        affected_strategies: list,
        threshold_value: float,
        actual_value: float,
        cooldown_seconds: int,
        auto_resume: bool = False
    ):
        """Publish circuit breaker triggered event."""
        if not self._can_publish():
            return
        
        import uuid
        trigger_id = str(uuid.uuid4())
        
        self.event_bus.publish(
            EventType.CIRCUIT_BREAKER_TRIGGERED,
            {
                "trigger_id": trigger_id,
                "trigger_type": trigger_type,
                "trigger_reason": trigger_reason,
                "affected_strategies": affected_strategies,
                "threshold_value": threshold_value,
                "actual_value": actual_value,
                "cooldown_seconds": cooldown_seconds,
                "auto_resume": auto_resume
            },
            priority=EventPriority.CRITICAL
        )
        logger.warning(f"Published circuit breaker event: {trigger_reason}")
    
    def publish_daily_loss_limit_reached(
        self,
        date: str,
        daily_loss: float,
        daily_limit: float,
        loss_percent: float,
        affected_strategies: list,
        action_taken: str
    ):
        """Publish daily loss limit reached event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.DAILY_LOSS_LIMIT_REACHED,
            {
                "date": date,
                "daily_loss": daily_loss,
                "daily_limit": daily_limit,
                "loss_percent": loss_percent,
                "affected_strategies": affected_strategies,
                "action_taken": action_taken
            },
            priority=EventPriority.CRITICAL
        )
        logger.warning(f"Published daily loss limit event: ${daily_loss:.2f} / ${daily_limit:.2f}")
    
    # =========================================================================
    # Strategy Events
    # =========================================================================
    
    def publish_strategy_started(
        self,
        strategy_id: str,
        strategy_name: str,
        strategy_type: str,
        config: Dict[str, Any],
        markets: list,
        initial_capital: Optional[float] = None
    ):
        """Publish strategy started event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.STRATEGY_STARTED,
            {
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "strategy_type": strategy_type,
                "config": config,
                "markets": markets,
                "initial_capital": initial_capital
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published strategy started event: {strategy_name}")
    
    def publish_strategy_paused(
        self,
        strategy_id: str,
        strategy_name: str,
        pause_reason: str,
        paused_by: str = "system",
        open_positions: int = 0,
        pending_orders: int = 0
    ):
        """Publish strategy paused event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.STRATEGY_PAUSED,
            {
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "pause_reason": pause_reason,
                "paused_by": paused_by,
                "open_positions": open_positions,
                "pending_orders": pending_orders
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published strategy paused event: {strategy_name} - {pause_reason}")
    
    def publish_strategy_stopped(
        self,
        strategy_id: str,
        strategy_name: str,
        stop_reason: str,
        stopped_by: str = "system",
        final_pnl: Optional[float] = None,
        total_trades: int = 0,
        runtime_seconds: int = 0
    ):
        """Publish strategy stopped event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.STRATEGY_STOPPED,
            {
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
                "stop_reason": stop_reason,
                "stopped_by": stopped_by,
                "final_pnl": final_pnl,
                "total_trades": total_trades,
                "runtime_seconds": runtime_seconds
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published strategy stopped event: {strategy_name} - {stop_reason}")
    
    # =========================================================================
    # Trading Events
    # =========================================================================
    
    def publish_trade_executed(
        self,
        trade_id: str,
        strategy_id: str,
        market_id: str,
        platform: str,
        side: str,
        quantity: float,
        price: float,
        total_value: float,
        fees: float = 0,
        slippage: Optional[float] = None,
        execution_time_ms: Optional[int] = None
    ):
        """Publish trade executed event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.TRADE_EXECUTED,
            {
                "trade_id": trade_id,
                "strategy_id": strategy_id,
                "market_id": market_id,
                "platform": platform,
                "side": side,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "fees": fees,
                "slippage": slippage,
                "execution_time_ms": execution_time_ms
            },
            priority=EventPriority.NORMAL
        )
    
    def publish_position_closed(
        self,
        position_id: str,
        strategy_id: str,
        market_id: str,
        platform: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_percent: float,
        hold_duration_seconds: int,
        close_reason: str
    ):
        """Publish position closed event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.POSITION_CLOSED,
            {
                "position_id": position_id,
                "strategy_id": strategy_id,
                "market_id": market_id,
                "platform": platform,
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "hold_duration_seconds": hold_duration_seconds,
                "close_reason": close_reason
            },
            priority=EventPriority.NORMAL
        )
    
    # =========================================================================
    # Emergency Events
    # =========================================================================
    
    def publish_emergency_stop(
        self,
        triggered_by: str,
        reason: str,
        scope: str = "all",
        affected_strategies: list = None,
        close_positions: bool = False,
        cancel_orders: bool = True
    ):
        """Publish emergency stop event."""
        if not self._can_publish():
            return
        
        self.event_bus.publish(
            EventType.EMERGENCY_STOP,
            {
                "triggered_by": triggered_by,
                "reason": reason,
                "scope": scope,
                "affected_strategies": affected_strategies or [],
                "close_positions": close_positions,
                "cancel_orders": cancel_orders
            },
            priority=EventPriority.CRITICAL
        )
        logger.critical(f"Published emergency stop event: {reason}")
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _can_publish(self) -> bool:
        """Check if we can publish events."""
        if not EVENT_BUS_AVAILABLE:
            return False
        if not self._connected or not self.event_bus:
            return False
        return True


def create_event_publisher(redis_url: Optional[str] = None) -> OrchestratorEventPublisher:
    """
    Factory function to create an event publisher.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        OrchestratorEventPublisher instance
    """
    return OrchestratorEventPublisher(redis_url)
