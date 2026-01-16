"""
PredictBot Stack - Logging Examples
====================================

This file demonstrates how to use the structured logging system across
different modules in the PredictBot stack.

Run this file directly to see example log output:
    python -m shared.logging_examples
"""

import asyncio
import os
import random
import time
from typing import Optional

# Set service name for examples
os.environ.setdefault('PREDICTBOT_SERVICE_NAME', 'example-service')
os.environ.setdefault('LOG_LEVEL', 'DEBUG')

from shared.logging_config import (
    get_logger,
    set_correlation_id,
    clear_correlation_id,
    with_correlation_id,
    log_critical_junction,
    CriticalJunctions,
    log_trade_execution,
    log_ai_decision,
    log_circuit_breaker,
    log_position_opened,
    log_position_closed,
    log_api_error,
    log_daily_loss_limit,
)


# =============================================================================
# Example 1: Basic Logging
# =============================================================================

def example_basic_logging():
    """Demonstrate basic logging with different levels."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 1: Basic Logging")
    print("=" * 60 + "\n")
    
    # Basic log messages
    logger.debug("Debug message - detailed information for debugging")
    logger.info("Info message - general operational information")
    logger.warning("Warning message - something unexpected happened")
    logger.error("Error message - an error occurred")
    logger.critical("Critical message - system is in critical state")


# =============================================================================
# Example 2: Logging with Extra Fields
# =============================================================================

def example_logging_with_extra():
    """Demonstrate logging with additional context fields."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 2: Logging with Extra Fields")
    print("=" * 60 + "\n")
    
    # Log with extra context
    logger.info(
        "Processing market data",
        extra={
            "market_id": "polymarket-btc-100k",
            "current_price": 0.65,
            "volume_24h": 150000,
            "source": "websocket"
        }
    )
    
    # Log with nested extra data
    logger.info(
        "Order book updated",
        extra={
            "market": "kalshi-fed-rate",
            "best_bid": {"price": 0.45, "size": 500},
            "best_ask": {"price": 0.47, "size": 300},
            "spread_bps": 200
        }
    )


# =============================================================================
# Example 3: Correlation ID for Request Tracing
# =============================================================================

def example_correlation_id():
    """Demonstrate correlation ID usage for request tracing."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 3: Correlation ID for Request Tracing")
    print("=" * 60 + "\n")
    
    # Simulate a request flow with correlation ID
    correlation_id = set_correlation_id()
    
    logger.info(f"Request started with correlation ID: {correlation_id}")
    logger.info("Fetching market data...")
    logger.info("Analyzing opportunity...")
    logger.info("Executing trade...")
    logger.info("Request completed")
    
    clear_correlation_id()
    
    # New request with different correlation ID
    set_correlation_id("custom-request-id-12345")
    logger.info("Another request with custom correlation ID")
    clear_correlation_id()


# =============================================================================
# Example 4: Using the Decorator
# =============================================================================

@with_correlation_id
def example_decorated_function():
    """Demonstrate the @with_correlation_id decorator."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 4: Using @with_correlation_id Decorator")
    print("=" * 60 + "\n")
    
    logger.info("Function started - correlation ID auto-generated")
    logger.info("Processing step 1...")
    logger.info("Processing step 2...")
    logger.info("Function completed")


# =============================================================================
# Example 5: Trade Execution Logging
# =============================================================================

def example_trade_execution():
    """Demonstrate trade execution logging."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 5: Trade Execution Logging")
    print("=" * 60 + "\n")
    
    set_correlation_id()
    
    # Log a trade execution
    log_trade_execution(
        logger,
        trade_id="trade-001",
        platform="polymarket",
        market="BTC-100K-2024",
        side="BUY",
        amount=100.0,
        price=0.65,
        order_type="LIMIT",
        fill_time_ms=45
    )
    
    # Log another trade
    log_trade_execution(
        logger,
        trade_id="trade-002",
        platform="kalshi",
        market="FED-RATE-DEC",
        side="SELL",
        amount=50.0,
        price=0.42,
        order_type="MARKET",
        slippage_bps=5
    )
    
    clear_correlation_id()


# =============================================================================
# Example 6: AI Decision Logging
# =============================================================================

def example_ai_decision():
    """Demonstrate AI decision logging."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 6: AI Decision Logging")
    print("=" * 60 + "\n")
    
    set_correlation_id()
    
    # Log an AI trading decision
    log_ai_decision(
        logger,
        decision_id="ai-dec-001",
        model="gpt-4-turbo",
        market="ELECTION-2024-WINNER",
        action="BUY",
        confidence=0.78,
        reasoning="Based on recent polling data and historical patterns, "
                  "the market appears underpriced relative to fundamentals.",
        tokens_used=1500,
        latency_ms=2300
    )
    
    # Log a decision to hold
    log_ai_decision(
        logger,
        decision_id="ai-dec-002",
        model="claude-3-opus",
        market="BTC-100K-2024",
        action="HOLD",
        confidence=0.45,
        reasoning="Insufficient edge detected. Market price aligns with model estimate.",
        tokens_used=800,
        latency_ms=1800
    )
    
    clear_correlation_id()


# =============================================================================
# Example 7: Position Management Logging
# =============================================================================

def example_position_management():
    """Demonstrate position open/close logging."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 7: Position Management Logging")
    print("=" * 60 + "\n")
    
    set_correlation_id()
    
    # Log position opened
    log_position_opened(
        logger,
        position_id="pos-001",
        platform="polymarket",
        market="ETH-MERGE-SUCCESS",
        side="LONG",
        size=500.0,
        entry_price=0.72,
        strategy="momentum"
    )
    
    # Simulate some time passing
    time.sleep(0.1)
    
    # Log position closed with profit
    log_position_closed(
        logger,
        position_id="pos-001",
        platform="polymarket",
        market="ETH-MERGE-SUCCESS",
        pnl=45.50,
        pnl_percent=0.126,
        hold_duration_seconds=3600,
        exit_reason="take_profit"
    )
    
    # Log position closed with loss
    log_position_closed(
        logger,
        position_id="pos-002",
        platform="kalshi",
        market="GDP-Q4-GROWTH",
        pnl=-25.00,
        pnl_percent=-0.05,
        hold_duration_seconds=7200,
        exit_reason="stop_loss"
    )
    
    clear_correlation_id()


# =============================================================================
# Example 8: Error Handling and API Errors
# =============================================================================

def example_error_handling():
    """Demonstrate error logging and API error handling."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 8: Error Handling and API Errors")
    print("=" * 60 + "\n")
    
    set_correlation_id()
    
    # Log an API error
    log_api_error(
        logger,
        api_name="polymarket",
        endpoint="/v1/orders",
        error_code=429,
        error_message="Rate limit exceeded",
        retry_after=60
    )
    
    # Log another API error
    log_api_error(
        logger,
        api_name="kalshi",
        endpoint="/v2/markets",
        error_code=503,
        error_message="Service temporarily unavailable",
        attempt=3,
        max_attempts=5
    )
    
    # Log an exception
    try:
        raise ValueError("Invalid market ID format")
    except ValueError as e:
        logger.exception("Failed to process market data", extra={"market_id": "invalid-123"})
    
    clear_correlation_id()


# =============================================================================
# Example 9: Circuit Breaker and Risk Events
# =============================================================================

def example_risk_events():
    """Demonstrate circuit breaker and risk management logging."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 9: Circuit Breaker and Risk Events")
    print("=" * 60 + "\n")
    
    set_correlation_id()
    
    # Log circuit breaker trigger
    log_circuit_breaker(
        logger,
        reason="Consecutive API failures exceeded threshold",
        trigger_count=5,
        cooldown_seconds=300,
        affected_services=["polymarket", "kalshi"]
    )
    
    # Log daily loss limit
    log_daily_loss_limit(
        logger,
        current_loss=95.50,
        limit=100.0,
        action_taken="halted_all_trading"
    )
    
    clear_correlation_id()


# =============================================================================
# Example 10: Health Status Updates
# =============================================================================

def example_health_status():
    """Demonstrate health status logging."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 10: Health Status Updates")
    print("=" * 60 + "\n")
    
    # Log service start
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.SERVICE_START,
        message="Orchestrator service started",
        extra={
            "version": "1.0.0",
            "environment": "production",
            "config_loaded": True
        }
    )
    
    # Log periodic health check
    logger.info(
        "Health check completed",
        extra={
            "status": "healthy",
            "uptime_seconds": 3600,
            "memory_mb": 256,
            "cpu_percent": 15.5,
            "active_positions": 3,
            "pending_orders": 2
        }
    )
    
    # Log health check failure
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.HEALTH_CHECK_FAILED,
        message="Health check failed for dependent service",
        level="WARNING",
        extra={
            "service": "redis",
            "error": "Connection refused",
            "retry_in_seconds": 30
        }
    )


# =============================================================================
# Example 11: Async Logging
# =============================================================================

@with_correlation_id
async def example_async_logging():
    """Demonstrate async logging with correlation ID."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("Example 11: Async Logging")
    print("=" * 60 + "\n")
    
    logger.info("Starting async operation")
    
    # Simulate async work
    await asyncio.sleep(0.1)
    logger.info("Async step 1 completed")
    
    await asyncio.sleep(0.1)
    logger.info("Async step 2 completed")
    
    logger.info("Async operation finished")


# =============================================================================
# Main Entry Point
# =============================================================================

def run_all_examples():
    """Run all logging examples."""
    print("\n" + "=" * 60)
    print("PredictBot Stack - Logging Examples")
    print("=" * 60)
    
    example_basic_logging()
    example_logging_with_extra()
    example_correlation_id()
    example_decorated_function()
    example_trade_execution()
    example_ai_decision()
    example_position_management()
    example_error_handling()
    example_risk_events()
    example_health_status()
    
    # Run async example
    asyncio.run(example_async_logging())
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_examples()
