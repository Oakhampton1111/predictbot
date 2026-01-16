"""
Event Schemas for PredictBot Stack

Pydantic models for all event types in the system.
Provides validation, serialization, and documentation for events.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal
import uuid


# ============================================================================
# Base Event Schema
# ============================================================================

class BaseEventData(BaseModel):
    """Base class for all event data payloads."""
    
    class Config:
        extra = "allow"
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None,
            Decimal: lambda v: str(v) if v else None,
        }


class EventEnvelope(BaseModel):
    """Standard envelope for all events."""
    event_type: str = Field(..., description="Type of the event")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    source_service: str = Field(..., description="Service that generated the event")
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Correlation ID for tracing")
    priority: int = Field(default=3, ge=1, le=4, description="Event priority (1=critical, 4=low)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None,
        }


# ============================================================================
# Trading Event Schemas
# ============================================================================

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class TradeExecutedData(BaseEventData):
    """Data for trade.executed event."""
    trade_id: str = Field(..., description="Unique trade identifier")
    strategy_id: str = Field(..., description="Strategy that initiated the trade")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform (polymarket, kalshi, etc.)")
    side: OrderSide = Field(..., description="Trade side (buy/sell)")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    price: float = Field(..., gt=0, description="Execution price")
    total_value: float = Field(..., description="Total trade value")
    fees: float = Field(default=0, ge=0, description="Trading fees")
    slippage: Optional[float] = Field(default=None, description="Price slippage from expected")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time in milliseconds")


class TradeFailedData(BaseEventData):
    """Data for trade.failed event."""
    trade_id: str = Field(..., description="Attempted trade identifier")
    strategy_id: str = Field(..., description="Strategy that initiated the trade")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    side: OrderSide = Field(..., description="Attempted trade side")
    quantity: float = Field(..., description="Attempted quantity")
    price: Optional[float] = Field(default=None, description="Attempted price")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error description")
    retry_count: int = Field(default=0, description="Number of retry attempts")


class PositionOpenedData(BaseEventData):
    """Data for position.opened event."""
    position_id: str = Field(..., description="Unique position identifier")
    strategy_id: str = Field(..., description="Strategy that opened the position")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    side: OrderSide = Field(..., description="Position side")
    quantity: float = Field(..., gt=0, description="Position size")
    entry_price: float = Field(..., gt=0, description="Entry price")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit: Optional[float] = Field(default=None, description="Take profit price")


class PositionClosedData(BaseEventData):
    """Data for position.closed event."""
    position_id: str = Field(..., description="Position identifier")
    strategy_id: str = Field(..., description="Strategy that managed the position")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    side: OrderSide = Field(..., description="Position side")
    quantity: float = Field(..., description="Position size")
    entry_price: float = Field(..., description="Entry price")
    exit_price: float = Field(..., description="Exit price")
    pnl: float = Field(..., description="Profit/Loss amount")
    pnl_percent: float = Field(..., description="Profit/Loss percentage")
    hold_duration_seconds: int = Field(..., description="How long position was held")
    close_reason: str = Field(..., description="Reason for closing (take_profit, stop_loss, manual, etc.)")


class OrderPlacedData(BaseEventData):
    """Data for order.placed event."""
    order_id: str = Field(..., description="Unique order identifier")
    strategy_id: str = Field(..., description="Strategy that placed the order")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    order_type: OrderType = Field(..., description="Order type")
    side: OrderSide = Field(..., description="Order side")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(default=None, description="Limit price (for limit orders)")


class OrderCancelledData(BaseEventData):
    """Data for order.cancelled event."""
    order_id: str = Field(..., description="Order identifier")
    strategy_id: str = Field(..., description="Strategy that owned the order")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    cancel_reason: str = Field(..., description="Reason for cancellation")


class OrderFilledData(BaseEventData):
    """Data for order.filled event."""
    order_id: str = Field(..., description="Order identifier")
    strategy_id: str = Field(..., description="Strategy that placed the order")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    fill_price: float = Field(..., description="Fill price")
    fill_quantity: float = Field(..., description="Filled quantity")
    remaining_quantity: float = Field(default=0, description="Remaining unfilled quantity")
    is_complete: bool = Field(default=True, description="Whether order is fully filled")


# ============================================================================
# Strategy Event Schemas
# ============================================================================

class StrategyState(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class StrategyStartedData(BaseEventData):
    """Data for strategy.started event."""
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_name: str = Field(..., description="Strategy name")
    strategy_type: str = Field(..., description="Strategy type (arbitrage, market_making, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Strategy configuration")
    markets: List[str] = Field(default_factory=list, description="Markets being traded")
    initial_capital: Optional[float] = Field(default=None, description="Initial capital allocation")


class StrategyPausedData(BaseEventData):
    """Data for strategy.paused event."""
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_name: str = Field(..., description="Strategy name")
    pause_reason: str = Field(..., description="Reason for pausing")
    paused_by: str = Field(default="system", description="Who/what paused the strategy")
    open_positions: int = Field(default=0, description="Number of open positions")
    pending_orders: int = Field(default=0, description="Number of pending orders")


class StrategyStoppedData(BaseEventData):
    """Data for strategy.stopped event."""
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_name: str = Field(..., description="Strategy name")
    stop_reason: str = Field(..., description="Reason for stopping")
    stopped_by: str = Field(default="system", description="Who/what stopped the strategy")
    final_pnl: Optional[float] = Field(default=None, description="Final P&L")
    total_trades: int = Field(default=0, description="Total trades executed")
    runtime_seconds: int = Field(default=0, description="Total runtime in seconds")


class StrategyErrorData(BaseEventData):
    """Data for strategy.error event."""
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_name: str = Field(..., description="Strategy name")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    error_stack: Optional[str] = Field(default=None, description="Stack trace")
    is_recoverable: bool = Field(default=True, description="Whether error is recoverable")
    action_taken: str = Field(default="none", description="Action taken in response")


class StrategyConfigUpdatedData(BaseEventData):
    """Data for strategy.config.updated event."""
    strategy_id: str = Field(..., description="Strategy identifier")
    strategy_name: str = Field(..., description="Strategy name")
    updated_by: str = Field(..., description="Who updated the config")
    changes: Dict[str, Any] = Field(..., description="Configuration changes")
    previous_values: Dict[str, Any] = Field(default_factory=dict, description="Previous values")


# ============================================================================
# AI Event Schemas
# ============================================================================

class AICycleStartedData(BaseEventData):
    """Data for ai.cycle.started event."""
    cycle_id: str = Field(..., description="Unique cycle identifier")
    cycle_number: int = Field(..., description="Sequential cycle number")
    agents_active: List[str] = Field(..., description="List of active agents")
    markets_analyzed: int = Field(default=0, description="Number of markets to analyze")


class AICycleCompletedData(BaseEventData):
    """Data for ai.cycle.completed event."""
    cycle_id: str = Field(..., description="Cycle identifier")
    cycle_number: int = Field(..., description="Sequential cycle number")
    duration_seconds: float = Field(..., description="Cycle duration")
    forecasts_generated: int = Field(default=0, description="Number of forecasts generated")
    signals_generated: int = Field(default=0, description="Number of trading signals")
    errors_encountered: int = Field(default=0, description="Number of errors")
    agent_results: Dict[str, Any] = Field(default_factory=dict, description="Results from each agent")


class AIForecastGeneratedData(BaseEventData):
    """Data for ai.forecast.generated event."""
    forecast_id: str = Field(..., description="Unique forecast identifier")
    market_id: str = Field(..., description="Market being forecasted")
    platform: str = Field(..., description="Trading platform")
    prediction: float = Field(..., ge=0, le=1, description="Predicted probability")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level")
    current_price: float = Field(..., description="Current market price")
    expected_value: float = Field(..., description="Expected value of trade")
    model_version: str = Field(default="unknown", description="Model version used")
    features_used: List[str] = Field(default_factory=list, description="Features used in prediction")
    reasoning: Optional[str] = Field(default=None, description="Explanation of forecast")


class AISignalGeneratedData(BaseEventData):
    """Data for ai.signal.generated event."""
    signal_id: str = Field(..., description="Unique signal identifier")
    forecast_id: str = Field(..., description="Related forecast identifier")
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    signal_type: str = Field(..., description="Signal type (buy, sell, hold)")
    strength: float = Field(..., ge=0, le=1, description="Signal strength")
    recommended_size: float = Field(..., description="Recommended position size")
    entry_price: Optional[float] = Field(default=None, description="Recommended entry price")
    stop_loss: Optional[float] = Field(default=None, description="Recommended stop loss")
    take_profit: Optional[float] = Field(default=None, description="Recommended take profit")
    time_horizon: str = Field(default="short", description="Expected time horizon")


class AIModelUpdatedData(BaseEventData):
    """Data for ai.model.updated event."""
    model_id: str = Field(..., description="Model identifier")
    model_name: str = Field(..., description="Model name")
    previous_version: str = Field(..., description="Previous version")
    new_version: str = Field(..., description="New version")
    update_type: str = Field(..., description="Type of update (retrain, fine-tune, etc.)")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")


class AIConfidenceLowData(BaseEventData):
    """Data for ai.confidence.low event."""
    forecast_id: str = Field(..., description="Forecast identifier")
    market_id: str = Field(..., description="Market identifier")
    confidence: float = Field(..., description="Confidence level")
    threshold: float = Field(..., description="Minimum threshold")
    reason: str = Field(..., description="Reason for low confidence")


# ============================================================================
# Risk Event Schemas
# ============================================================================

class CircuitBreakerTriggeredData(BaseEventData):
    """Data for risk.circuit_breaker event."""
    trigger_id: str = Field(..., description="Unique trigger identifier")
    trigger_type: str = Field(..., description="Type of circuit breaker")
    trigger_reason: str = Field(..., description="Reason for triggering")
    affected_strategies: List[str] = Field(default_factory=list, description="Affected strategies")
    threshold_value: float = Field(..., description="Threshold that was breached")
    actual_value: float = Field(..., description="Actual value that triggered")
    cooldown_seconds: int = Field(default=300, description="Cooldown period")
    auto_resume: bool = Field(default=False, description="Whether auto-resume is enabled")


class DailyLossLimitReachedData(BaseEventData):
    """Data for risk.daily_loss_limit event."""
    date: str = Field(..., description="Date of the limit breach")
    daily_loss: float = Field(..., description="Current daily loss")
    daily_limit: float = Field(..., description="Daily loss limit")
    loss_percent: float = Field(..., description="Loss as percentage of capital")
    affected_strategies: List[str] = Field(default_factory=list, description="Affected strategies")
    action_taken: str = Field(..., description="Action taken (pause_all, reduce_size, etc.)")


class PositionLimitReachedData(BaseEventData):
    """Data for risk.position_limit event."""
    strategy_id: str = Field(..., description="Strategy identifier")
    current_positions: int = Field(..., description="Current number of positions")
    max_positions: int = Field(..., description="Maximum allowed positions")
    current_exposure: float = Field(..., description="Current exposure amount")
    max_exposure: float = Field(..., description="Maximum allowed exposure")


class ExposureWarningData(BaseEventData):
    """Data for risk.exposure_warning event."""
    warning_type: str = Field(..., description="Type of exposure warning")
    current_exposure: float = Field(..., description="Current exposure")
    warning_threshold: float = Field(..., description="Warning threshold")
    max_threshold: float = Field(..., description="Maximum threshold")
    affected_markets: List[str] = Field(default_factory=list, description="Markets with high exposure")
    recommendation: str = Field(..., description="Recommended action")


class VolatilitySpikeData(BaseEventData):
    """Data for risk.volatility_spike event."""
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    current_volatility: float = Field(..., description="Current volatility")
    normal_volatility: float = Field(..., description="Normal volatility level")
    spike_factor: float = Field(..., description="Volatility spike factor")
    affected_positions: List[str] = Field(default_factory=list, description="Affected positions")


# ============================================================================
# System Event Schemas
# ============================================================================

class ServiceStartedData(BaseEventData):
    """Data for system.service.started event."""
    service_name: str = Field(..., description="Service name")
    service_version: str = Field(..., description="Service version")
    instance_id: str = Field(..., description="Instance identifier")
    host: str = Field(..., description="Host name")
    port: Optional[int] = Field(default=None, description="Service port")
    config_hash: Optional[str] = Field(default=None, description="Configuration hash")


class ServiceStoppedData(BaseEventData):
    """Data for system.service.stopped event."""
    service_name: str = Field(..., description="Service name")
    instance_id: str = Field(..., description="Instance identifier")
    stop_reason: str = Field(..., description="Reason for stopping")
    uptime_seconds: int = Field(..., description="Total uptime")
    graceful: bool = Field(default=True, description="Whether shutdown was graceful")


class ServiceErrorData(BaseEventData):
    """Data for system.service.error event."""
    service_name: str = Field(..., description="Service name")
    instance_id: str = Field(..., description="Instance identifier")
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    error_stack: Optional[str] = Field(default=None, description="Stack trace")
    severity: str = Field(default="error", description="Severity level")
    is_fatal: bool = Field(default=False, description="Whether error is fatal")


class ServiceHealthCheckData(BaseEventData):
    """Data for system.service.health event."""
    service_name: str = Field(..., description="Service name")
    instance_id: str = Field(..., description="Instance identifier")
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Individual health checks")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Health metrics")
    uptime_seconds: int = Field(..., description="Current uptime")


class ConfigChangedData(BaseEventData):
    """Data for system.config.changed event."""
    config_type: str = Field(..., description="Type of configuration")
    changed_by: str = Field(..., description="Who changed the config")
    changes: Dict[str, Any] = Field(..., description="Configuration changes")
    previous_values: Dict[str, Any] = Field(default_factory=dict, description="Previous values")
    requires_restart: bool = Field(default=False, description="Whether restart is required")


class EmergencyStopData(BaseEventData):
    """Data for system.emergency.stop event."""
    triggered_by: str = Field(..., description="Who triggered the emergency stop")
    reason: str = Field(..., description="Reason for emergency stop")
    scope: str = Field(default="all", description="Scope of stop (all, strategy, platform)")
    affected_strategies: List[str] = Field(default_factory=list, description="Affected strategies")
    close_positions: bool = Field(default=False, description="Whether to close all positions")
    cancel_orders: bool = Field(default=True, description="Whether to cancel all orders")


# ============================================================================
# Alert Event Schemas
# ============================================================================

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertTriggeredData(BaseEventData):
    """Data for alert.triggered event."""
    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    source: str = Field(..., description="Source of the alert")
    related_entity_type: Optional[str] = Field(default=None, description="Related entity type")
    related_entity_id: Optional[str] = Field(default=None, description="Related entity ID")
    notification_channels: List[str] = Field(default_factory=list, description="Channels to notify")
    auto_resolve: bool = Field(default=False, description="Whether alert auto-resolves")
    resolve_timeout_seconds: Optional[int] = Field(default=None, description="Auto-resolve timeout")


class AlertAcknowledgedData(BaseEventData):
    """Data for alert.acknowledged event."""
    alert_id: str = Field(..., description="Alert identifier")
    acknowledged_by: str = Field(..., description="Who acknowledged the alert")
    acknowledgment_note: Optional[str] = Field(default=None, description="Acknowledgment note")


class AlertResolvedData(BaseEventData):
    """Data for alert.resolved event."""
    alert_id: str = Field(..., description="Alert identifier")
    resolved_by: str = Field(..., description="Who resolved the alert")
    resolution_type: str = Field(..., description="Resolution type (manual, auto, timeout)")
    resolution_note: Optional[str] = Field(default=None, description="Resolution note")
    duration_seconds: int = Field(..., description="Time from trigger to resolution")


# ============================================================================
# User Event Schemas
# ============================================================================

class UserLoginData(BaseEventData):
    """Data for user.login event."""
    user_id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    ip_address: str = Field(..., description="Login IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent string")
    login_method: str = Field(default="password", description="Login method")
    mfa_used: bool = Field(default=False, description="Whether MFA was used")


class UserLogoutData(BaseEventData):
    """Data for user.logout event."""
    user_id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    session_duration_seconds: int = Field(..., description="Session duration")
    logout_type: str = Field(default="manual", description="Logout type (manual, timeout, forced)")


class UserActionData(BaseEventData):
    """Data for user.action event."""
    user_id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(default=None, description="Resource identifier")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action details")
    ip_address: Optional[str] = Field(default=None, description="IP address")


# ============================================================================
# Market Event Schemas
# ============================================================================

class MarketDataUpdateData(BaseEventData):
    """Data for market.data.update event."""
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    current_price: float = Field(..., description="Current price")
    bid_price: Optional[float] = Field(default=None, description="Best bid price")
    ask_price: Optional[float] = Field(default=None, description="Best ask price")
    volume_24h: Optional[float] = Field(default=None, description="24-hour volume")
    price_change_24h: Optional[float] = Field(default=None, description="24-hour price change")


class MarketClosedData(BaseEventData):
    """Data for market.closed event."""
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    final_price: float = Field(..., description="Final settlement price")
    outcome: str = Field(..., description="Market outcome")
    total_volume: float = Field(..., description="Total trading volume")


class MarketOpenedData(BaseEventData):
    """Data for market.opened event."""
    market_id: str = Field(..., description="Market identifier")
    platform: str = Field(..., description="Trading platform")
    market_title: str = Field(..., description="Market title/question")
    opening_price: float = Field(..., description="Opening price")
    close_date: Optional[datetime] = Field(default=None, description="Expected close date")


# ============================================================================
# Event Schema Registry
# ============================================================================

EVENT_SCHEMA_MAP = {
    # Trading events
    "trade.executed": TradeExecutedData,
    "trade.failed": TradeFailedData,
    "position.opened": PositionOpenedData,
    "position.closed": PositionClosedData,
    "order.placed": OrderPlacedData,
    "order.cancelled": OrderCancelledData,
    "order.filled": OrderFilledData,
    
    # Strategy events
    "strategy.started": StrategyStartedData,
    "strategy.paused": StrategyPausedData,
    "strategy.stopped": StrategyStoppedData,
    "strategy.error": StrategyErrorData,
    "strategy.config.updated": StrategyConfigUpdatedData,
    
    # AI events
    "ai.cycle.started": AICycleStartedData,
    "ai.cycle.completed": AICycleCompletedData,
    "ai.forecast.generated": AIForecastGeneratedData,
    "ai.signal.generated": AISignalGeneratedData,
    "ai.model.updated": AIModelUpdatedData,
    "ai.confidence.low": AIConfidenceLowData,
    
    # Risk events
    "risk.circuit_breaker": CircuitBreakerTriggeredData,
    "risk.daily_loss_limit": DailyLossLimitReachedData,
    "risk.position_limit": PositionLimitReachedData,
    "risk.exposure_warning": ExposureWarningData,
    "risk.volatility_spike": VolatilitySpikeData,
    
    # System events
    "system.service.started": ServiceStartedData,
    "system.service.stopped": ServiceStoppedData,
    "system.service.error": ServiceErrorData,
    "system.service.health": ServiceHealthCheckData,
    "system.config.changed": ConfigChangedData,
    "system.emergency.stop": EmergencyStopData,
    
    # Alert events
    "alert.triggered": AlertTriggeredData,
    "alert.acknowledged": AlertAcknowledgedData,
    "alert.resolved": AlertResolvedData,
    
    # User events
    "user.login": UserLoginData,
    "user.logout": UserLogoutData,
    "user.action": UserActionData,
    
    # Market events
    "market.data.update": MarketDataUpdateData,
    "market.closed": MarketClosedData,
    "market.opened": MarketOpenedData,
}


def get_schema_for_event(event_type: str) -> type[BaseEventData]:
    """
    Get the Pydantic schema class for a given event type.
    
    Args:
        event_type: The event type string
        
    Returns:
        The corresponding Pydantic model class
        
    Raises:
        ValueError: If event type is not recognized
    """
    if event_type not in EVENT_SCHEMA_MAP:
        raise ValueError(f"Unknown event type: {event_type}")
    return EVENT_SCHEMA_MAP[event_type]


def validate_event_data(event_type: str, data: Dict[str, Any]) -> BaseEventData:
    """
    Validate event data against its schema.
    
    Args:
        event_type: The event type string
        data: The event data to validate
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If event type is not recognized
        ValidationError: If data doesn't match schema
    """
    schema_class = get_schema_for_event(event_type)
    return schema_class(**data)
