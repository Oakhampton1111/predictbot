"""
Event Bus Integration for AI Orchestrator

Provides event publishing capabilities for the AI orchestrator service.
Publishes events for AI cycles, forecasts, signals, and model updates.
"""

import os
import sys
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

# Add shared module to path
sys.path.insert(0, '/app')

logger = logging.getLogger(__name__)

# Try to import event bus components
try:
    from shared.event_bus import AsyncEventBus, EventType, EventPriority, Event
    from shared.event_schemas import (
        AICycleStartedData, AICycleCompletedData,
        AIForecastGeneratedData, AISignalGeneratedData,
        AIModelUpdatedData, AIConfidenceLowData,
        ServiceStartedData, ServiceStoppedData
    )
    EVENT_BUS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Event bus not available: {e}")
    EVENT_BUS_AVAILABLE = False
    EventType = None
    EventPriority = None


class AIEventPublisher:
    """
    Event publisher for the AI orchestrator service.
    
    Publishes events for:
    - AI cycle lifecycle (start, complete)
    - Forecast generation
    - Trading signal generation
    - Model updates
    - Low confidence warnings
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the event publisher.
        
        Args:
            redis_url: Redis connection URL (defaults to env var)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://redis:6379')
        self.service_name = "ai-orchestrator"
        self.event_bus: Optional[AsyncEventBus] = None
        self._connected = False
        self._cycle_counter = 0
        self._emergency_stop_handler: Optional[Callable] = None
    
    async def connect(self) -> bool:
        """
        Connect to the event bus.
        
        Returns:
            True if connected successfully
        """
        if not EVENT_BUS_AVAILABLE:
            logger.warning("Event bus not available, skipping connection")
            return False
        
        try:
            self.event_bus = AsyncEventBus(self.redis_url, self.service_name)
            if await self.event_bus.connect():
                self._connected = True
                logger.info("AI orchestrator connected to event bus")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to event bus: {e}")
        
        return False
    
    async def disconnect(self):
        """Disconnect from the event bus."""
        if self.event_bus:
            await self.event_bus.stop_listening()
            await self.event_bus.disconnect()
        self._connected = False
        logger.info("AI orchestrator disconnected from event bus")
    
    async def subscribe_to_emergency_stop(self, handler: Callable):
        """
        Subscribe to emergency stop commands.
        
        Args:
            handler: Async callback function to handle emergency stop
        """
        if not EVENT_BUS_AVAILABLE or not self.event_bus:
            return
        
        async def _handler(event: Event):
            logger.warning(f"Emergency stop received: {event.data}")
            if asyncio.iscoroutinefunction(handler):
                await handler(event.data)
            else:
                handler(event.data)
        
        await self.event_bus.subscribe(EventType.EMERGENCY_STOP, _handler)
        self._emergency_stop_handler = _handler
        logger.info("Subscribed to emergency stop events")
    
    async def start_listening(self):
        """Start listening for events."""
        if self.event_bus:
            await self.event_bus.start_listening()
    
    async def stop_listening(self):
        """Stop listening for events."""
        if self.event_bus:
            await self.event_bus.stop_listening()
    
    # =========================================================================
    # Service Lifecycle Events
    # =========================================================================
    
    async def publish_service_started(
        self,
        version: str,
        agents_active: List[str],
        host: str = "0.0.0.0",
        port: int = 8081
    ):
        """Publish service started event."""
        if not self._can_publish():
            return
        
        instance_id = os.getenv('HOSTNAME', str(uuid.uuid4())[:8])
        
        await self.event_bus.publish(
            EventType.SERVICE_STARTED,
            {
                "service_name": self.service_name,
                "service_version": version,
                "instance_id": instance_id,
                "host": host,
                "port": port,
                "config_hash": None
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published service started event: {self.service_name} v{version}")
    
    async def publish_service_stopped(
        self,
        stop_reason: str,
        uptime_seconds: int,
        total_cycles: int,
        graceful: bool = True
    ):
        """Publish service stopped event."""
        if not self._can_publish():
            return
        
        instance_id = os.getenv('HOSTNAME', str(uuid.uuid4())[:8])
        
        await self.event_bus.publish(
            EventType.SERVICE_STOPPED,
            {
                "service_name": self.service_name,
                "instance_id": instance_id,
                "stop_reason": stop_reason,
                "uptime_seconds": uptime_seconds,
                "graceful": graceful,
                "total_cycles": total_cycles
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published service stopped event: {stop_reason}")
    
    # =========================================================================
    # AI Cycle Events
    # =========================================================================
    
    async def publish_cycle_started(
        self,
        agents_active: List[str],
        markets_analyzed: int = 0
    ) -> str:
        """
        Publish AI cycle started event.
        
        Args:
            agents_active: List of active agent names
            markets_analyzed: Number of markets to analyze
            
        Returns:
            Cycle ID for tracking
        """
        if not self._can_publish():
            return str(uuid.uuid4())
        
        self._cycle_counter += 1
        cycle_id = str(uuid.uuid4())
        
        await self.event_bus.publish(
            EventType.AI_CYCLE_STARTED,
            {
                "cycle_id": cycle_id,
                "cycle_number": self._cycle_counter,
                "agents_active": agents_active,
                "markets_analyzed": markets_analyzed
            },
            priority=EventPriority.NORMAL
        )
        logger.debug(f"Published cycle started event: {cycle_id}")
        return cycle_id
    
    async def publish_cycle_completed(
        self,
        cycle_id: str,
        duration_seconds: float,
        forecasts_generated: int = 0,
        signals_generated: int = 0,
        errors_encountered: int = 0,
        agent_results: Optional[Dict[str, Any]] = None
    ):
        """Publish AI cycle completed event."""
        if not self._can_publish():
            return
        
        await self.event_bus.publish(
            EventType.AI_CYCLE_COMPLETED,
            {
                "cycle_id": cycle_id,
                "cycle_number": self._cycle_counter,
                "duration_seconds": duration_seconds,
                "forecasts_generated": forecasts_generated,
                "signals_generated": signals_generated,
                "errors_encountered": errors_encountered,
                "agent_results": agent_results or {}
            },
            priority=EventPriority.NORMAL
        )
        logger.debug(f"Published cycle completed event: {cycle_id}")
    
    # =========================================================================
    # Forecast Events
    # =========================================================================
    
    async def publish_forecast_generated(
        self,
        market_id: str,
        platform: str,
        prediction: float,
        confidence: float,
        current_price: float,
        expected_value: float,
        model_version: str = "unknown",
        features_used: Optional[List[str]] = None,
        reasoning: Optional[str] = None
    ) -> str:
        """
        Publish forecast generated event.
        
        Args:
            market_id: Market identifier
            platform: Trading platform
            prediction: Predicted probability (0-1)
            confidence: Confidence level (0-1)
            current_price: Current market price
            expected_value: Expected value of trade
            model_version: Version of model used
            features_used: List of features used
            reasoning: Explanation of forecast
            
        Returns:
            Forecast ID
        """
        if not self._can_publish():
            return str(uuid.uuid4())
        
        forecast_id = str(uuid.uuid4())
        
        await self.event_bus.publish(
            EventType.AI_FORECAST_GENERATED,
            {
                "forecast_id": forecast_id,
                "market_id": market_id,
                "platform": platform,
                "prediction": prediction,
                "confidence": confidence,
                "current_price": current_price,
                "expected_value": expected_value,
                "model_version": model_version,
                "features_used": features_used or [],
                "reasoning": reasoning
            },
            priority=EventPriority.NORMAL
        )
        logger.debug(f"Published forecast event: {forecast_id} for {market_id}")
        
        # Check for low confidence
        confidence_threshold = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.6'))
        if confidence < confidence_threshold:
            await self.publish_low_confidence_warning(
                forecast_id=forecast_id,
                market_id=market_id,
                confidence=confidence,
                threshold=confidence_threshold,
                reason="Confidence below minimum threshold"
            )
        
        return forecast_id
    
    async def publish_signal_generated(
        self,
        forecast_id: str,
        market_id: str,
        platform: str,
        signal_type: str,
        strength: float,
        recommended_size: float,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        time_horizon: str = "short"
    ) -> str:
        """
        Publish trading signal generated event.
        
        Args:
            forecast_id: Related forecast ID
            market_id: Market identifier
            platform: Trading platform
            signal_type: Signal type (buy, sell, hold)
            strength: Signal strength (0-1)
            recommended_size: Recommended position size
            entry_price: Recommended entry price
            stop_loss: Recommended stop loss
            take_profit: Recommended take profit
            time_horizon: Expected time horizon
            
        Returns:
            Signal ID
        """
        if not self._can_publish():
            return str(uuid.uuid4())
        
        signal_id = str(uuid.uuid4())
        
        await self.event_bus.publish(
            EventType.AI_SIGNAL_GENERATED,
            {
                "signal_id": signal_id,
                "forecast_id": forecast_id,
                "market_id": market_id,
                "platform": platform,
                "signal_type": signal_type,
                "strength": strength,
                "recommended_size": recommended_size,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "time_horizon": time_horizon
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published signal event: {signal_type} for {market_id} (strength: {strength:.2f})")
        return signal_id
    
    # =========================================================================
    # Model Events
    # =========================================================================
    
    async def publish_model_updated(
        self,
        model_id: str,
        model_name: str,
        previous_version: str,
        new_version: str,
        update_type: str,
        performance_metrics: Optional[Dict[str, float]] = None
    ):
        """Publish model updated event."""
        if not self._can_publish():
            return
        
        await self.event_bus.publish(
            EventType.AI_MODEL_UPDATED,
            {
                "model_id": model_id,
                "model_name": model_name,
                "previous_version": previous_version,
                "new_version": new_version,
                "update_type": update_type,
                "performance_metrics": performance_metrics or {}
            },
            priority=EventPriority.HIGH
        )
        logger.info(f"Published model updated event: {model_name} {previous_version} -> {new_version}")
    
    async def publish_low_confidence_warning(
        self,
        forecast_id: str,
        market_id: str,
        confidence: float,
        threshold: float,
        reason: str
    ):
        """Publish low confidence warning event."""
        if not self._can_publish():
            return
        
        await self.event_bus.publish(
            EventType.AI_CONFIDENCE_LOW,
            {
                "forecast_id": forecast_id,
                "market_id": market_id,
                "confidence": confidence,
                "threshold": threshold,
                "reason": reason
            },
            priority=EventPriority.NORMAL
        )
        logger.warning(f"Published low confidence warning: {market_id} ({confidence:.2%} < {threshold:.2%})")
    
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
    
    @property
    def cycle_count(self) -> int:
        """Get the current cycle count."""
        return self._cycle_counter


# Singleton instance for easy access
_publisher_instance: Optional[AIEventPublisher] = None


async def get_event_publisher(redis_url: Optional[str] = None) -> AIEventPublisher:
    """
    Get or create the event publisher singleton.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        AIEventPublisher instance
    """
    global _publisher_instance
    
    if _publisher_instance is None:
        _publisher_instance = AIEventPublisher(redis_url)
        await _publisher_instance.connect()
    
    return _publisher_instance


def create_event_publisher(redis_url: Optional[str] = None) -> AIEventPublisher:
    """
    Factory function to create an event publisher.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        AIEventPublisher instance
    """
    return AIEventPublisher(redis_url)
