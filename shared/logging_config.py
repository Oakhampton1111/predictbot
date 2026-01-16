"""
PredictBot Stack - Structured Logging Configuration
====================================================

This module provides a unified logging configuration for all Python services
in the PredictBot stack. It outputs structured JSON logs that are compatible
with Loki/Promtail for aggregation and Grafana for visualization.

Features:
- Structured JSON logging format
- Correlation ID support for request tracing
- Critical junction markers for important events
- Non-blocking async logging support
- Log level configuration via environment variables

Usage:
    from shared.logging_config import get_logger, log_critical_junction
    
    logger = get_logger(__name__)
    logger.info("Service started", extra={"port": 8080})
    
    # For critical junctions
    log_critical_junction(
        logger,
        junction_name="trade_execution",
        message="Trade executed successfully",
        extra={"trade_id": "123", "amount": 100.0}
    )
"""

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set a correlation ID in the current context.
    
    Args:
        correlation_id: Optional ID to set. If None, generates a new UUID.
    
    Returns:
        The correlation ID that was set.
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    correlation_id_var.set(None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Outputs logs in a format compatible with Loki/Promtail parsing.
    """
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # Base log structure
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service_name": self.service_name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if present
        correlation_id = get_correlation_id()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        # Add extra fields from the record
        if hasattr(record, 'extra') and record.extra:
            log_entry["extra"] = record.extra
        
        # Add any additional attributes passed via extra={}
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'extra', 'message', 'taskName'
        }
        
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                extra_fields[key] = value
        
        if extra_fields:
            if "extra" not in log_entry:
                log_entry["extra"] = {}
            log_entry["extra"].update(extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add critical junction marker if present
        if hasattr(record, 'critical_junction'):
            log_entry["critical_junction"] = record.critical_junction
        
        return json.dumps(log_entry, default=str)


class ContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes context information.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the logging call to add context."""
        extra = kwargs.get('extra', {})
        
        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            extra['correlation_id'] = correlation_id
        
        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(
    name: str,
    service_name: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        service_name: Service name for log entries. Defaults to PREDICTBOT_SERVICE_NAME env var.
        level: Log level. Defaults to LOG_LEVEL env var or INFO.
    
    Returns:
        Configured logger instance.
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", extra={"request_id": "123"})
    """
    # Get configuration from environment
    if service_name is None:
        service_name = os.environ.get('PREDICTBOT_SERVICE_NAME', 'predictbot')
    
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Create JSON handler for stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter(service_name))
        logger.addHandler(handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


def log_critical_junction(
    logger: logging.Logger,
    junction_name: str,
    message: str,
    level: str = "INFO",
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a critical junction event.
    
    Critical junctions are important events that should be tracked for
    monitoring and alerting purposes.
    
    Args:
        logger: Logger instance to use
        junction_name: Name of the critical junction (e.g., "trade_execution")
        message: Log message
        level: Log level (default: INFO)
        extra: Additional fields to include
    
    Example:
        log_critical_junction(
            logger,
            junction_name="trade_execution",
            message="Trade executed on Polymarket",
            extra={"trade_id": "123", "amount": 100.0, "market": "BTC-USD"}
        )
    """
    log_extra = extra or {}
    log_extra['critical_junction'] = junction_name
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, f"[{junction_name.upper()}] {message}", extra=log_extra)


def with_correlation_id(func: Callable) -> Callable:
    """
    Decorator to automatically set a correlation ID for a function.
    
    Example:
        @with_correlation_id
        async def handle_request(request):
            logger.info("Processing request")  # Will include correlation ID
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if correlation ID is already set
        if get_correlation_id() is None:
            set_correlation_id()
        try:
            return func(*args, **kwargs)
        finally:
            clear_correlation_id()
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if get_correlation_id() is None:
            set_correlation_id()
        try:
            return await func(*args, **kwargs)
        finally:
            clear_correlation_id()
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


# =============================================================================
# Critical Junction Constants
# =============================================================================

class CriticalJunctions:
    """Constants for critical junction names."""
    
    TRADE_EXECUTION = "trade_execution"
    AI_DECISION = "ai_decision"
    CIRCUIT_BREAKER_TRIGGER = "circuit_breaker_trigger"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    API_ERROR = "api_error"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    CONFIG_RELOAD = "config_reload"
    HEALTH_CHECK_FAILED = "health_check_failed"


# =============================================================================
# Convenience Functions for Common Log Events
# =============================================================================

def log_trade_execution(
    logger: logging.Logger,
    trade_id: str,
    platform: str,
    market: str,
    side: str,
    amount: float,
    price: float,
    **extra
) -> None:
    """Log a trade execution event."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.TRADE_EXECUTION,
        message=f"Trade executed: {side} {amount} @ {price} on {platform}/{market}",
        extra={
            "trade_id": trade_id,
            "platform": platform,
            "market": market,
            "side": side,
            "amount": amount,
            "price": price,
            **extra
        }
    )


def log_ai_decision(
    logger: logging.Logger,
    decision_id: str,
    model: str,
    market: str,
    action: str,
    confidence: float,
    reasoning: Optional[str] = None,
    **extra
) -> None:
    """Log an AI trading decision."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.AI_DECISION,
        message=f"AI decision: {action} on {market} (confidence: {confidence:.2%})",
        extra={
            "decision_id": decision_id,
            "model": model,
            "market": market,
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            **extra
        }
    )


def log_circuit_breaker(
    logger: logging.Logger,
    reason: str,
    trigger_count: int,
    cooldown_seconds: int,
    **extra
) -> None:
    """Log a circuit breaker trigger event."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.CIRCUIT_BREAKER_TRIGGER,
        message=f"Circuit breaker triggered: {reason}",
        level="CRITICAL",
        extra={
            "reason": reason,
            "trigger_count": trigger_count,
            "cooldown_seconds": cooldown_seconds,
            **extra
        }
    )


def log_position_opened(
    logger: logging.Logger,
    position_id: str,
    platform: str,
    market: str,
    side: str,
    size: float,
    entry_price: float,
    **extra
) -> None:
    """Log a position opened event."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.POSITION_OPENED,
        message=f"Position opened: {side} {size} on {platform}/{market} @ {entry_price}",
        extra={
            "position_id": position_id,
            "platform": platform,
            "market": market,
            "side": side,
            "size": size,
            "entry_price": entry_price,
            **extra
        }
    )


def log_position_closed(
    logger: logging.Logger,
    position_id: str,
    platform: str,
    market: str,
    pnl: float,
    pnl_percent: float,
    hold_duration_seconds: int,
    **extra
) -> None:
    """Log a position closed event."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.POSITION_CLOSED,
        message=f"Position closed: PnL ${pnl:.2f} ({pnl_percent:.2%}) on {platform}/{market}",
        extra={
            "position_id": position_id,
            "platform": platform,
            "market": market,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "hold_duration_seconds": hold_duration_seconds,
            **extra
        }
    )


def log_api_error(
    logger: logging.Logger,
    api_name: str,
    endpoint: str,
    error_code: Optional[int],
    error_message: str,
    **extra
) -> None:
    """Log an API error event."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.API_ERROR,
        message=f"API error from {api_name}: {error_message}",
        level="ERROR",
        extra={
            "api_name": api_name,
            "endpoint": endpoint,
            "error_code": error_code,
            "error_message": error_message,
            **extra
        }
    )


def log_daily_loss_limit(
    logger: logging.Logger,
    current_loss: float,
    limit: float,
    **extra
) -> None:
    """Log a daily loss limit trigger event."""
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.DAILY_LOSS_LIMIT,
        message=f"Daily loss limit reached: ${current_loss:.2f} / ${limit:.2f}",
        level="CRITICAL",
        extra={
            "current_loss": current_loss,
            "limit": limit,
            **extra
        }
    )


# =============================================================================
# Module Initialization
# =============================================================================

# Create a default logger for the shared module
_default_logger = get_logger("predictbot.shared")


def debug(msg: str, **kwargs) -> None:
    """Log a debug message using the default logger."""
    _default_logger.debug(msg, extra=kwargs)


def info(msg: str, **kwargs) -> None:
    """Log an info message using the default logger."""
    _default_logger.info(msg, extra=kwargs)


def warning(msg: str, **kwargs) -> None:
    """Log a warning message using the default logger."""
    _default_logger.warning(msg, extra=kwargs)


def error(msg: str, **kwargs) -> None:
    """Log an error message using the default logger."""
    _default_logger.error(msg, extra=kwargs)


def critical(msg: str, **kwargs) -> None:
    """Log a critical message using the default logger."""
    _default_logger.critical(msg, extra=kwargs)
