"""
Event Bus Module for PredictBot Stack

Provides Redis Pub/Sub based event bus for inter-service communication.
Supports async operations, event filtering, and automatic reconnection.
"""

import redis
import redis.asyncio as aioredis
import json
import asyncio
import threading
import logging
import uuid
from typing import Callable, Dict, Any, Optional, List, Set
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
from functools import wraps

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of all event types in the PredictBot system."""
    
    # Trading events
    TRADE_EXECUTED = "trade.executed"
    TRADE_FAILED = "trade.failed"
    POSITION_OPENED = "position.opened"
    POSITION_CLOSED = "position.closed"
    ORDER_PLACED = "order.placed"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_FILLED = "order.filled"
    
    # Strategy events
    STRATEGY_STARTED = "strategy.started"
    STRATEGY_PAUSED = "strategy.paused"
    STRATEGY_STOPPED = "strategy.stopped"
    STRATEGY_ERROR = "strategy.error"
    STRATEGY_CONFIG_UPDATED = "strategy.config.updated"
    
    # AI events
    AI_CYCLE_STARTED = "ai.cycle.started"
    AI_CYCLE_COMPLETED = "ai.cycle.completed"
    AI_FORECAST_GENERATED = "ai.forecast.generated"
    AI_SIGNAL_GENERATED = "ai.signal.generated"
    AI_MODEL_UPDATED = "ai.model.updated"
    AI_CONFIDENCE_LOW = "ai.confidence.low"
    
    # Risk events
    CIRCUIT_BREAKER_TRIGGERED = "risk.circuit_breaker"
    DAILY_LOSS_LIMIT_REACHED = "risk.daily_loss_limit"
    POSITION_LIMIT_REACHED = "risk.position_limit"
    EXPOSURE_WARNING = "risk.exposure_warning"
    VOLATILITY_SPIKE = "risk.volatility_spike"
    
    # System events
    SERVICE_STARTED = "system.service.started"
    SERVICE_STOPPED = "system.service.stopped"
    SERVICE_ERROR = "system.service.error"
    SERVICE_HEALTH_CHECK = "system.service.health"
    CONFIG_CHANGED = "system.config.changed"
    EMERGENCY_STOP = "system.emergency.stop"
    
    # Alert events
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_RESOLVED = "alert.resolved"
    
    # User events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_ACTION = "user.action"
    
    # Market events
    MARKET_DATA_UPDATE = "market.data.update"
    MARKET_CLOSED = "market.closed"
    MARKET_OPENED = "market.opened"


class EventPriority(Enum):
    """Event priority levels for processing order."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


@dataclass
class Event:
    """Base event structure for all events in the system."""
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    source_service: str
    correlation_id: str
    priority: int = EventPriority.NORMAL.value
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "source_service": self.source_service,
            "correlation_id": self.correlation_id,
            "priority": self.priority,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            event_type=data["event_type"],
            data=data["data"],
            timestamp=data["timestamp"],
            source_service=data["source_service"],
            correlation_id=data["correlation_id"],
            priority=data.get("priority", EventPriority.NORMAL.value),
            metadata=data.get("metadata")
        )


class EventBus:
    """
    Synchronous Event Bus using Redis Pub/Sub.
    
    Provides publish/subscribe functionality for inter-service communication.
    Supports multiple handlers per event type and wildcard subscriptions.
    """
    
    CHANNEL_PREFIX = "predictbot:events:"
    
    def __init__(
        self,
        redis_url: str,
        service_name: str = "unknown",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the Event Bus.
        
        Args:
            redis_url: Redis connection URL
            service_name: Name of the service using this event bus
            max_retries: Maximum number of retry attempts for failed operations
            retry_delay: Delay between retry attempts in seconds
        """
        self.redis_url = redis_url
        self.service_name = service_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.handlers: Dict[str, List[Callable]] = {}
        self.pattern_handlers: Dict[str, List[Callable]] = {}
        
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        self._connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to Redis.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            self.redis.ping()
            self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            self._connected = True
            logger.info(f"Event bus connected to Redis for service: {self.service_name}")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Redis and cleanup resources."""
        self._running = False
        
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=5.0)
        
        if self.pubsub:
            try:
                self.pubsub.close()
            except Exception as e:
                logger.warning(f"Error closing pubsub: {e}")
        
        if self.redis:
            try:
                self.redis.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
        
        self._connected = False
        logger.info(f"Event bus disconnected for service: {self.service_name}")
    
    def _get_channel(self, event_type: EventType) -> str:
        """Get the Redis channel name for an event type."""
        return f"{self.CHANNEL_PREFIX}{event_type.value}"
    
    def _get_pattern(self, pattern: str) -> str:
        """Get the Redis pattern for wildcard subscriptions."""
        return f"{self.CHANNEL_PREFIX}{pattern}"
    
    def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish an event to the event bus.
        
        Args:
            event_type: Type of event to publish
            data: Event payload data
            priority: Event priority level
            correlation_id: Optional correlation ID for tracing
            metadata: Optional additional metadata
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self._connected:
            logger.error("Cannot publish: Event bus not connected")
            return False
        
        event = Event(
            event_type=event_type.value,
            data=data,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=self.service_name,
            correlation_id=correlation_id or str(uuid.uuid4()),
            priority=priority.value,
            metadata=metadata
        )
        
        channel = self._get_channel(event_type)
        message = json.dumps(event.to_dict())
        
        for attempt in range(self.max_retries):
            try:
                subscribers = self.redis.publish(channel, message)
                logger.debug(
                    f"Published event {event_type.value} to {subscribers} subscribers"
                )
                return True
            except redis.ConnectionError as e:
                logger.warning(
                    f"Publish attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    threading.Event().wait(self.retry_delay)
                    self.connect()
        
        logger.error(f"Failed to publish event {event_type.value} after {self.max_retries} attempts")
        return False
    
    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None]
    ):
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Callback function to handle events
        """
        channel = self._get_channel(event_type)
        
        if channel not in self.handlers:
            self.handlers[channel] = []
            if self.pubsub:
                self.pubsub.subscribe(channel)
        
        self.handlers[channel].append(handler)
        logger.info(f"Subscribed to {event_type.value}")
    
    def subscribe_pattern(
        self,
        pattern: str,
        handler: Callable[[Event], None]
    ):
        """
        Subscribe to events matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "trade.*" for all trade events)
            handler: Callback function to handle events
        """
        redis_pattern = self._get_pattern(pattern)
        
        if redis_pattern not in self.pattern_handlers:
            self.pattern_handlers[redis_pattern] = []
            if self.pubsub:
                self.pubsub.psubscribe(redis_pattern)
        
        self.pattern_handlers[redis_pattern].append(handler)
        logger.info(f"Subscribed to pattern: {pattern}")
    
    def unsubscribe(self, event_type: EventType):
        """Unsubscribe from a specific event type."""
        channel = self._get_channel(event_type)
        
        if channel in self.handlers:
            del self.handlers[channel]
            if self.pubsub:
                self.pubsub.unsubscribe(channel)
            logger.info(f"Unsubscribed from {event_type.value}")
    
    def start_listening(self):
        """Start listening for events in a background thread."""
        if self._running:
            logger.warning("Listener already running")
            return
        
        if not self._connected:
            if not self.connect():
                logger.error("Cannot start listening: Connection failed")
                return
        
        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name=f"EventBus-{self.service_name}"
        )
        self._listener_thread.start()
        logger.info("Event bus listener started")
    
    def stop_listening(self):
        """Stop the event listener."""
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=5.0)
        logger.info("Event bus listener stopped")
    
    def _listen_loop(self):
        """Main listening loop for processing events."""
        while self._running:
            try:
                message = self.pubsub.get_message(timeout=1.0)
                if message:
                    self._process_message(message)
            except redis.ConnectionError as e:
                logger.error(f"Connection lost: {e}")
                self._reconnect()
            except Exception as e:
                logger.error(f"Error in listener loop: {e}")
    
    def _process_message(self, message: Dict[str, Any]):
        """Process a received message."""
        if message["type"] not in ("message", "pmessage"):
            return
        
        try:
            event_data = json.loads(message["data"])
            event = Event.from_dict(event_data)
            
            # Handle direct subscriptions
            channel = message.get("channel")
            if channel and channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
            
            # Handle pattern subscriptions
            pattern = message.get("pattern")
            if pattern and pattern in self.pattern_handlers:
                for handler in self.pattern_handlers[pattern]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Pattern handler error: {e}")
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _reconnect(self):
        """Attempt to reconnect to Redis."""
        for attempt in range(self.max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}")
            if self.connect():
                # Resubscribe to all channels
                for channel in self.handlers.keys():
                    self.pubsub.subscribe(channel)
                for pattern in self.pattern_handlers.keys():
                    self.pubsub.psubscribe(pattern)
                return
            threading.Event().wait(self.retry_delay * (attempt + 1))
        
        logger.error("Failed to reconnect after all attempts")
        self._running = False


class AsyncEventBus:
    """
    Asynchronous Event Bus using Redis Pub/Sub.
    
    Provides async publish/subscribe functionality for inter-service communication.
    Designed for use with asyncio-based services.
    """
    
    CHANNEL_PREFIX = "predictbot:events:"
    
    def __init__(
        self,
        redis_url: str,
        service_name: str = "unknown",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the Async Event Bus.
        
        Args:
            redis_url: Redis connection URL
            service_name: Name of the service using this event bus
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.redis_url = redis_url
        self.service_name = service_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.handlers: Dict[str, List[Callable]] = {}
        self.pattern_handlers: Dict[str, List[Callable]] = {}
        
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Establish async connection to Redis.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            await self.redis.ping()
            self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            self._connected = True
            logger.info(f"Async event bus connected for service: {self.service_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis and cleanup resources."""
        self._running = False
        
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            try:
                await self.pubsub.close()
            except Exception as e:
                logger.warning(f"Error closing pubsub: {e}")
        
        if self.redis:
            try:
                await self.redis.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
        
        self._connected = False
        logger.info(f"Async event bus disconnected for service: {self.service_name}")
    
    def _get_channel(self, event_type: EventType) -> str:
        """Get the Redis channel name for an event type."""
        return f"{self.CHANNEL_PREFIX}{event_type.value}"
    
    def _get_pattern(self, pattern: str) -> str:
        """Get the Redis pattern for wildcard subscriptions."""
        return f"{self.CHANNEL_PREFIX}{pattern}"
    
    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish an event to the event bus asynchronously.
        
        Args:
            event_type: Type of event to publish
            data: Event payload data
            priority: Event priority level
            correlation_id: Optional correlation ID for tracing
            metadata: Optional additional metadata
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self._connected:
            logger.error("Cannot publish: Event bus not connected")
            return False
        
        event = Event(
            event_type=event_type.value,
            data=data,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_service=self.service_name,
            correlation_id=correlation_id or str(uuid.uuid4()),
            priority=priority.value,
            metadata=metadata
        )
        
        channel = self._get_channel(event_type)
        message = json.dumps(event.to_dict())
        
        for attempt in range(self.max_retries):
            try:
                subscribers = await self.redis.publish(channel, message)
                logger.debug(
                    f"Published event {event_type.value} to {subscribers} subscribers"
                )
                return True
            except Exception as e:
                logger.warning(f"Publish attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    await self.connect()
        
        logger.error(f"Failed to publish event {event_type.value}")
        return False
    
    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any]
    ):
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Async callback function to handle events
        """
        channel = self._get_channel(event_type)
        
        if channel not in self.handlers:
            self.handlers[channel] = []
            if self.pubsub:
                await self.pubsub.subscribe(channel)
        
        self.handlers[channel].append(handler)
        logger.info(f"Subscribed to {event_type.value}")
    
    async def subscribe_pattern(
        self,
        pattern: str,
        handler: Callable[[Event], Any]
    ):
        """
        Subscribe to events matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "trade.*")
            handler: Async callback function to handle events
        """
        redis_pattern = self._get_pattern(pattern)
        
        if redis_pattern not in self.pattern_handlers:
            self.pattern_handlers[redis_pattern] = []
            if self.pubsub:
                await self.pubsub.psubscribe(redis_pattern)
        
        self.pattern_handlers[redis_pattern].append(handler)
        logger.info(f"Subscribed to pattern: {pattern}")
    
    async def unsubscribe(self, event_type: EventType):
        """Unsubscribe from a specific event type."""
        channel = self._get_channel(event_type)
        
        if channel in self.handlers:
            del self.handlers[channel]
            if self.pubsub:
                await self.pubsub.unsubscribe(channel)
            logger.info(f"Unsubscribed from {event_type.value}")
    
    async def start_listening(self):
        """Start listening for events asynchronously."""
        if self._running:
            logger.warning("Listener already running")
            return
        
        if not self._connected:
            if not await self.connect():
                logger.error("Cannot start listening: Connection failed")
                return
        
        self._running = True
        self._listener_task = asyncio.create_task(
            self._listen_loop(),
            name=f"EventBus-{self.service_name}"
        )
        logger.info("Async event bus listener started")
    
    async def stop_listening(self):
        """Stop the event listener."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        logger.info("Async event bus listener stopped")
    
    async def _listen_loop(self):
        """Main async listening loop for processing events."""
        while self._running:
            try:
                message = await self.pubsub.get_message(timeout=1.0)
                if message:
                    await self._process_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in listener loop: {e}")
                await self._reconnect()
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process a received message asynchronously."""
        if message["type"] not in ("message", "pmessage"):
            return
        
        try:
            event_data = json.loads(message["data"])
            event = Event.from_dict(event_data)
            
            # Handle direct subscriptions
            channel = message.get("channel")
            if channel and channel in self.handlers:
                for handler in self.handlers[channel]:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"Handler error: {e}")
            
            # Handle pattern subscriptions
            pattern = message.get("pattern")
            if pattern and pattern in self.pattern_handlers:
                for handler in self.pattern_handlers[pattern]:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"Pattern handler error: {e}")
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _reconnect(self):
        """Attempt to reconnect to Redis asynchronously."""
        for attempt in range(self.max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}")
            if await self.connect():
                # Resubscribe to all channels
                for channel in self.handlers.keys():
                    await self.pubsub.subscribe(channel)
                for pattern in self.pattern_handlers.keys():
                    await self.pubsub.psubscribe(pattern)
                return
            await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        logger.error("Failed to reconnect after all attempts")
        self._running = False


def create_event_bus(
    redis_url: str,
    service_name: str,
    async_mode: bool = False
) -> EventBus | AsyncEventBus:
    """
    Factory function to create an event bus instance.
    
    Args:
        redis_url: Redis connection URL
        service_name: Name of the service
        async_mode: Whether to create async event bus
        
    Returns:
        EventBus or AsyncEventBus instance
    """
    if async_mode:
        return AsyncEventBus(redis_url, service_name)
    return EventBus(redis_url, service_name)
