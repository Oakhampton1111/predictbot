"""
PredictBot Stack - Shared Utilities
====================================

This package contains shared utilities used across all Python services
in the PredictBot stack.

Modules:
    logging_config: Structured JSON logging with correlation ID support
    metrics: Prometheus metrics collection and export
    event_bus: Redis Pub/Sub based event bus for inter-service communication
    event_schemas: Pydantic models for all event types
    alert_service: Multi-channel alert notification system
    audit_logger: Comprehensive audit logging for compliance
    websocket_server: Real-time WebSocket updates
    kalshi_websocket: Real-time Kalshi market data streaming
    news_feed: Multi-source news aggregation
    conflict_detector: Strategy conflict detection and resolution

Usage:
    from shared.logging_config import get_logger, log_trade_execution
    from shared.metrics import get_metrics_registry, MetricsRegistry
    from shared.event_bus import AsyncEventBus, EventType, EventPriority
    from shared.alert_service import AlertService, Alert
    from shared.audit_logger import AuditLogger, AuditAction
    from shared.websocket_server import WebSocketManager
    from shared.kalshi_websocket import KalshiWebSocketClient
    from shared.news_feed import NewsFeedAggregator
    from shared.conflict_detector import ConflictDetector
"""

# Logging
from shared.logging_config import (
    get_logger,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    log_critical_junction,
    with_correlation_id,
    CriticalJunctions,
    log_trade_execution,
    log_ai_decision,
    log_circuit_breaker,
    log_position_opened,
    log_position_closed,
    log_api_error,
    log_daily_loss_limit,
)

# Metrics
from shared.metrics import (
    get_metrics_registry,
    MetricsRegistry,
    record_trade,
    record_error,
    record_ai_decision,
    get_metrics,
)

# Event Bus (lazy import to avoid Redis dependency issues)
try:
    from shared.event_bus import (
        EventBus,
        AsyncEventBus,
        EventType,
        EventPriority,
        Event,
        create_event_bus,
    )
    EVENT_BUS_AVAILABLE = True
except ImportError:
    EVENT_BUS_AVAILABLE = False

# Event Schemas
try:
    from shared.event_schemas import (
        AlertSeverity,
        TradeExecutedData,
        PositionClosedData,
        StrategyStartedData,
        AICycleCompletedData,
        AIForecastGeneratedData,
        CircuitBreakerTriggeredData,
        DailyLossLimitReachedData,
        validate_event_data,
    )
    EVENT_SCHEMAS_AVAILABLE = True
except ImportError:
    EVENT_SCHEMAS_AVAILABLE = False

# Alert Service
try:
    from shared.alert_service import (
        AlertService,
        Alert,
        NotificationChannel,
        create_alert_service,
    )
    ALERT_SERVICE_AVAILABLE = True
except ImportError:
    ALERT_SERVICE_AVAILABLE = False

# Audit Logger
try:
    from shared.audit_logger import (
        AuditLogger,
        AuditAction,
        AuditLog,
        create_audit_logger,
    )
    AUDIT_LOGGER_AVAILABLE = True
except ImportError:
    AUDIT_LOGGER_AVAILABLE = False

# WebSocket Server
try:
    from shared.websocket_server import (
        WebSocketManager,
        WebSocketClient,
        MessageType,
        SubscriptionChannel,
        EventBusWebSocketBridge,
        create_websocket_manager,
    )
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

# Kalshi WebSocket
try:
    from shared.kalshi_websocket import (
        KalshiWebSocketClient,
        KalshiOrderbook,
        KalshiTrade,
        KalshiChannel,
        create_kalshi_websocket_client,
    )
    KALSHI_WEBSOCKET_AVAILABLE = True
except ImportError:
    KALSHI_WEBSOCKET_AVAILABLE = False

# News Feed
try:
    from shared.news_feed import (
        NewsFeedAggregator,
        NewsFeedConfig,
        NewsArticle,
        NewsSource,
        create_news_aggregator,
    )
    NEWS_FEED_AVAILABLE = True
except ImportError:
    NEWS_FEED_AVAILABLE = False

# Conflict Detector
try:
    from shared.conflict_detector import (
        ConflictDetector,
        ConflictResult,
        ConflictType,
        TradeIntent,
        MarketLock,
        StrategyPriority,
        create_conflict_detector,
    )
    CONFLICT_DETECTOR_AVAILABLE = True
except ImportError:
    CONFLICT_DETECTOR_AVAILABLE = False

__all__ = [
    # Logging
    "get_logger",
    "get_correlation_id",
    "set_correlation_id",
    "clear_correlation_id",
    "log_critical_junction",
    "with_correlation_id",
    "CriticalJunctions",
    "log_trade_execution",
    "log_ai_decision",
    "log_circuit_breaker",
    "log_position_opened",
    "log_position_closed",
    "log_api_error",
    "log_daily_loss_limit",
    # Metrics
    "get_metrics_registry",
    "MetricsRegistry",
    "record_trade",
    "record_error",
    "record_ai_decision",
    "get_metrics",
    # Event Bus
    "EventBus",
    "AsyncEventBus",
    "EventType",
    "EventPriority",
    "Event",
    "create_event_bus",
    "EVENT_BUS_AVAILABLE",
    # Event Schemas
    "AlertSeverity",
    "TradeExecutedData",
    "PositionClosedData",
    "StrategyStartedData",
    "AICycleCompletedData",
    "AIForecastGeneratedData",
    "CircuitBreakerTriggeredData",
    "DailyLossLimitReachedData",
    "validate_event_data",
    "EVENT_SCHEMAS_AVAILABLE",
    # Alert Service
    "AlertService",
    "Alert",
    "NotificationChannel",
    "create_alert_service",
    "ALERT_SERVICE_AVAILABLE",
    # Audit Logger
    "AuditLogger",
    "AuditAction",
    "AuditLog",
    "create_audit_logger",
    "AUDIT_LOGGER_AVAILABLE",
    # WebSocket Server
    "WebSocketManager",
    "WebSocketClient",
    "MessageType",
    "SubscriptionChannel",
    "EventBusWebSocketBridge",
    "create_websocket_manager",
    "WEBSOCKET_AVAILABLE",
    # Kalshi WebSocket
    "KalshiWebSocketClient",
    "KalshiOrderbook",
    "KalshiTrade",
    "KalshiChannel",
    "create_kalshi_websocket_client",
    "KALSHI_WEBSOCKET_AVAILABLE",
    # News Feed
    "NewsFeedAggregator",
    "NewsFeedConfig",
    "NewsArticle",
    "NewsSource",
    "create_news_aggregator",
    "NEWS_FEED_AVAILABLE",
    # Conflict Detector
    "ConflictDetector",
    "ConflictResult",
    "ConflictType",
    "TradeIntent",
    "MarketLock",
    "StrategyPriority",
    "create_conflict_detector",
    "CONFLICT_DETECTOR_AVAILABLE",
]

__version__ = "0.3.0"
