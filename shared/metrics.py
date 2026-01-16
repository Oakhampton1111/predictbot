"""
PredictBot Stack - Prometheus Metrics Utility
==============================================

This module provides a unified metrics collection system for all Python services
in the PredictBot stack. It wraps the Prometheus client library and provides
pre-defined metrics for trading, AI, and system monitoring.

Features:
- Pre-defined trading metrics (trades, P&L, positions)
- AI/LLM metrics (decisions, forecasts, API calls)
- System metrics (errors, latency, health)
- Easy-to-use decorators for timing functions
- Thread-safe metric updates

Usage:
    from shared.metrics import get_metrics_registry, MetricsRegistry
    
    # Get the singleton registry
    registry = get_metrics_registry()
    
    # Record a trade
    registry.record_trade(platform="polymarket", side="BUY", amount=100.0)
    
    # Time a function
    @registry.time_function("trade_execution")
    def execute_trade():
        ...
"""

import os
import time
from contextlib import contextmanager
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, Generator, Optional

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Info,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
        multiprocess,
        REGISTRY,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def observe(self, *args, **kwargs): pass
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    CollectorRegistry = object
    REGISTRY = None
    
    def generate_latest(registry=None):
        return b""
    
    CONTENT_TYPE_LATEST = "text/plain"


# Singleton instance
_metrics_registry: Optional['MetricsRegistry'] = None
_registry_lock = Lock()


class MetricsRegistry:
    """
    Central registry for all PredictBot metrics.
    
    This class provides a unified interface for recording metrics across
    all services in the stack.
    """
    
    def __init__(self, service_name: Optional[str] = None, registry: Optional[CollectorRegistry] = None):
        """
        Initialize the metrics registry.
        
        Args:
            service_name: Name of the service (defaults to PREDICTBOT_SERVICE_NAME env var)
            registry: Optional custom Prometheus registry
        """
        self.service_name = service_name or os.environ.get('PREDICTBOT_SERVICE_NAME', 'predictbot')
        self.registry = registry or (REGISTRY if PROMETHEUS_AVAILABLE else None)
        self._lock = Lock()
        
        # Initialize all metrics
        self._init_trading_metrics()
        self._init_ai_metrics()
        self._init_system_metrics()
        self._init_info_metrics()
    
    def _init_trading_metrics(self) -> None:
        """Initialize trading-related metrics."""
        # Trade counters
        self.trades_total = Counter(
            'predictbot_trades_total',
            'Total number of trades executed',
            ['platform', 'market', 'side', 'strategy'],
            registry=self.registry
        )
        
        # Trade latency histogram
        self.trade_latency = Histogram(
            'predictbot_trade_latency_seconds',
            'Trade execution latency in seconds',
            ['platform', 'order_type'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # P&L gauge
        self.pnl_current = Gauge(
            'predictbot_pnl_current_usd',
            'Current profit/loss in USD',
            ['platform', 'strategy'],
            registry=self.registry
        )
        
        # Daily P&L gauge
        self.pnl_daily = Gauge(
            'predictbot_pnl_daily_usd',
            'Daily profit/loss in USD',
            ['platform'],
            registry=self.registry
        )
        
        # Open positions gauge
        self.positions_open = Gauge(
            'predictbot_positions_open_total',
            'Number of currently open positions',
            ['platform', 'strategy'],
            registry=self.registry
        )
        
        # Position value gauge
        self.position_value = Gauge(
            'predictbot_position_value_usd',
            'Total value of open positions in USD',
            ['platform'],
            registry=self.registry
        )
        
        # Positions opened/closed counters
        self.positions_opened = Counter(
            'predictbot_positions_opened_total',
            'Total number of positions opened',
            ['platform', 'strategy'],
            registry=self.registry
        )
        
        self.positions_closed = Counter(
            'predictbot_positions_closed_total',
            'Total number of positions closed',
            ['platform', 'strategy', 'result'],
            registry=self.registry
        )
    
    def _init_ai_metrics(self) -> None:
        """Initialize AI/LLM-related metrics."""
        # AI decisions counter
        self.ai_decisions = Counter(
            'predictbot_ai_decisions_total',
            'Total number of AI trading decisions',
            ['model', 'action', 'market'],
            registry=self.registry
        )
        
        # AI confidence histogram
        self.ai_confidence = Histogram(
            'predictbot_ai_confidence',
            'AI decision confidence scores',
            ['model', 'action'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # Forecast accuracy gauge
        self.forecast_accuracy = Gauge(
            'predictbot_ai_forecast_accuracy',
            'Rolling forecast accuracy (0-1)',
            ['model', 'timeframe'],
            registry=self.registry
        )
        
        # Forecasts counter
        self.forecasts_total = Counter(
            'predictbot_forecasts_total',
            'Total number of forecasts generated',
            ['model', 'market_type'],
            registry=self.registry
        )
        
        # LLM API calls counter
        self.llm_calls = Counter(
            'predictbot_llm_calls_total',
            'Total number of LLM API calls',
            ['model', 'endpoint'],
            registry=self.registry
        )
        
        # LLM latency histogram
        self.llm_latency = Histogram(
            'predictbot_llm_latency_seconds',
            'LLM API call latency in seconds',
            ['model'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        # LLM tokens counter
        self.llm_tokens = Counter(
            'predictbot_llm_tokens_total',
            'Total LLM tokens used',
            ['model', 'type'],
            registry=self.registry
        )
    
    def _init_system_metrics(self) -> None:
        """Initialize system-related metrics."""
        # Error counter
        self.errors_total = Counter(
            'predictbot_errors_total',
            'Total number of errors',
            ['service', 'error_type'],
            registry=self.registry
        )
        
        # API errors counter
        self.api_errors = Counter(
            'predictbot_api_errors_total',
            'Total number of API errors',
            ['api_name', 'endpoint', 'error_code'],
            registry=self.registry
        )
        
        # Request counter
        self.requests_total = Counter(
            'predictbot_requests_total',
            'Total number of requests processed',
            ['service', 'endpoint', 'method', 'status'],
            registry=self.registry
        )
        
        # Request latency histogram
        self.request_latency = Histogram(
            'predictbot_request_latency_seconds',
            'Request processing latency in seconds',
            ['service', 'endpoint'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
            registry=self.registry
        )
        
        # Circuit breaker gauge
        self.circuit_breaker_active = Gauge(
            'predictbot_circuit_breaker_active',
            'Whether circuit breaker is currently active (1=active, 0=inactive)',
            ['reason'],
            registry=self.registry
        )
        
        # Circuit breaker triggers counter
        self.circuit_breaker_triggers = Counter(
            'predictbot_circuit_breaker_triggers_total',
            'Total number of circuit breaker triggers',
            ['reason'],
            registry=self.registry
        )
        
        # Loss limit triggers counter
        self.loss_limit_triggers = Counter(
            'predictbot_loss_limit_triggers_total',
            'Total number of loss limit triggers',
            ['limit_type'],
            registry=self.registry
        )
        
        # Health check gauge
        self.health_status = Gauge(
            'predictbot_health_status',
            'Service health status (1=healthy, 0=unhealthy)',
            ['service', 'component'],
            registry=self.registry
        )
        
        # Uptime gauge
        self.uptime_seconds = Gauge(
            'predictbot_uptime_seconds',
            'Service uptime in seconds',
            ['service'],
            registry=self.registry
        )
    
    def _init_info_metrics(self) -> None:
        """Initialize info metrics."""
        self.service_info = Info(
            'predictbot_service',
            'Service information',
            registry=self.registry
        )
    
    # =========================================================================
    # Trading Metric Methods
    # =========================================================================
    
    def record_trade(
        self,
        platform: str,
        market: str,
        side: str,
        amount: float,
        strategy: str = "default",
        latency_seconds: Optional[float] = None,
        order_type: str = "market"
    ) -> None:
        """
        Record a trade execution.
        
        Args:
            platform: Trading platform (e.g., "polymarket", "kalshi")
            market: Market identifier
            side: Trade side ("BUY" or "SELL")
            amount: Trade amount in USD
            strategy: Trading strategy name
            latency_seconds: Optional execution latency
            order_type: Order type ("market" or "limit")
        """
        self.trades_total.labels(
            platform=platform,
            market=market,
            side=side,
            strategy=strategy
        ).inc()
        
        if latency_seconds is not None:
            self.trade_latency.labels(
                platform=platform,
                order_type=order_type
            ).observe(latency_seconds)
    
    def update_pnl(
        self,
        pnl: float,
        platform: str = "total",
        strategy: str = "all"
    ) -> None:
        """Update current P&L."""
        self.pnl_current.labels(platform=platform, strategy=strategy).set(pnl)
    
    def update_daily_pnl(self, pnl: float, platform: str = "total") -> None:
        """Update daily P&L."""
        self.pnl_daily.labels(platform=platform).set(pnl)
    
    def update_positions(
        self,
        count: int,
        platform: str = "total",
        strategy: str = "all"
    ) -> None:
        """Update open positions count."""
        self.positions_open.labels(platform=platform, strategy=strategy).set(count)
    
    def record_position_opened(
        self,
        platform: str,
        strategy: str = "default"
    ) -> None:
        """Record a position being opened."""
        self.positions_opened.labels(platform=platform, strategy=strategy).inc()
    
    def record_position_closed(
        self,
        platform: str,
        strategy: str = "default",
        profitable: bool = True
    ) -> None:
        """Record a position being closed."""
        result = "profit" if profitable else "loss"
        self.positions_closed.labels(
            platform=platform,
            strategy=strategy,
            result=result
        ).inc()
    
    # =========================================================================
    # AI Metric Methods
    # =========================================================================
    
    def record_ai_decision(
        self,
        model: str,
        action: str,
        market: str,
        confidence: float
    ) -> None:
        """
        Record an AI trading decision.
        
        Args:
            model: AI model name (e.g., "gpt-4", "claude-3")
            action: Decision action ("BUY", "SELL", "HOLD")
            market: Market identifier
            confidence: Confidence score (0-1)
        """
        self.ai_decisions.labels(model=model, action=action, market=market).inc()
        self.ai_confidence.labels(model=model, action=action).observe(confidence)
    
    def update_forecast_accuracy(
        self,
        accuracy: float,
        model: str = "all",
        timeframe: str = "24h"
    ) -> None:
        """Update forecast accuracy metric."""
        self.forecast_accuracy.labels(model=model, timeframe=timeframe).set(accuracy)
    
    def record_forecast(self, model: str, market_type: str = "binary") -> None:
        """Record a forecast generation."""
        self.forecasts_total.labels(model=model, market_type=market_type).inc()
    
    def record_llm_call(
        self,
        model: str,
        endpoint: str = "chat",
        latency_seconds: Optional[float] = None,
        tokens_input: int = 0,
        tokens_output: int = 0
    ) -> None:
        """
        Record an LLM API call.
        
        Args:
            model: LLM model name
            endpoint: API endpoint
            latency_seconds: Call latency
            tokens_input: Input tokens used
            tokens_output: Output tokens generated
        """
        self.llm_calls.labels(model=model, endpoint=endpoint).inc()
        
        if latency_seconds is not None:
            self.llm_latency.labels(model=model).observe(latency_seconds)
        
        if tokens_input > 0:
            self.llm_tokens.labels(model=model, type="input").inc(tokens_input)
        
        if tokens_output > 0:
            self.llm_tokens.labels(model=model, type="output").inc(tokens_output)
    
    # =========================================================================
    # System Metric Methods
    # =========================================================================
    
    def record_error(self, error_type: str, service: Optional[str] = None) -> None:
        """Record an error occurrence."""
        service = service or self.service_name
        self.errors_total.labels(service=service, error_type=error_type).inc()
    
    def record_api_error(
        self,
        api_name: str,
        endpoint: str,
        error_code: int
    ) -> None:
        """Record an API error."""
        self.api_errors.labels(
            api_name=api_name,
            endpoint=endpoint,
            error_code=str(error_code)
        ).inc()
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        latency_seconds: float,
        service: Optional[str] = None
    ) -> None:
        """Record a request."""
        service = service or self.service_name
        self.requests_total.labels(
            service=service,
            endpoint=endpoint,
            method=method,
            status=str(status)
        ).inc()
        self.request_latency.labels(service=service, endpoint=endpoint).observe(latency_seconds)
    
    def set_circuit_breaker(self, active: bool, reason: str = "default") -> None:
        """Set circuit breaker status."""
        self.circuit_breaker_active.labels(reason=reason).set(1 if active else 0)
        if active:
            self.circuit_breaker_triggers.labels(reason=reason).inc()
    
    def record_loss_limit_trigger(self, limit_type: str = "daily") -> None:
        """Record a loss limit trigger."""
        self.loss_limit_triggers.labels(limit_type=limit_type).inc()
    
    def set_health_status(
        self,
        healthy: bool,
        component: str = "main",
        service: Optional[str] = None
    ) -> None:
        """Set health status for a component."""
        service = service or self.service_name
        self.health_status.labels(service=service, component=component).set(1 if healthy else 0)
    
    def update_uptime(self, seconds: float, service: Optional[str] = None) -> None:
        """Update service uptime."""
        service = service or self.service_name
        self.uptime_seconds.labels(service=service).set(seconds)
    
    def set_service_info(self, **info: str) -> None:
        """Set service information."""
        self.service_info.info(info)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    @contextmanager
    def time_operation(
        self,
        operation_name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Generator[None, None, None]:
        """
        Context manager to time an operation.
        
        Usage:
            with registry.time_operation("trade_execution", {"platform": "polymarket"}):
                execute_trade()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            # Record to request latency with operation as endpoint
            service = labels.get('service', self.service_name) if labels else self.service_name
            self.request_latency.labels(
                service=service,
                endpoint=operation_name
            ).observe(elapsed)
    
    def time_function(self, operation_name: str) -> Callable:
        """
        Decorator to time a function.
        
        Usage:
            @registry.time_function("trade_execution")
            def execute_trade():
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                with self.time_operation(operation_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format."""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry)
        return b""
    
    def get_content_type(self) -> str:
        """Get the content type for metrics response."""
        return CONTENT_TYPE_LATEST


def get_metrics_registry(
    service_name: Optional[str] = None,
    force_new: bool = False
) -> MetricsRegistry:
    """
    Get the singleton metrics registry instance.
    
    Args:
        service_name: Optional service name override
        force_new: If True, create a new registry even if one exists
    
    Returns:
        MetricsRegistry instance
    """
    global _metrics_registry
    
    with _registry_lock:
        if _metrics_registry is None or force_new:
            _metrics_registry = MetricsRegistry(service_name=service_name)
        return _metrics_registry


# =============================================================================
# Convenience Functions
# =============================================================================

def record_trade(
    platform: str,
    market: str,
    side: str,
    amount: float,
    **kwargs: Any
) -> None:
    """Convenience function to record a trade."""
    get_metrics_registry().record_trade(platform, market, side, amount, **kwargs)


def record_error(error_type: str, service: Optional[str] = None) -> None:
    """Convenience function to record an error."""
    get_metrics_registry().record_error(error_type, service)


def record_ai_decision(
    model: str,
    action: str,
    market: str,
    confidence: float
) -> None:
    """Convenience function to record an AI decision."""
    get_metrics_registry().record_ai_decision(model, action, market, confidence)


def get_metrics() -> bytes:
    """Convenience function to get metrics."""
    return get_metrics_registry().get_metrics()
