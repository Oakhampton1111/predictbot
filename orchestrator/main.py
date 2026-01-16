#!/usr/bin/env python3
"""
PredictBot Stack - Orchestrator Main Entry Point

This is the central orchestrator that manages the trading bot stack,
including health monitoring, risk management, and service coordination.
"""

import os
import sys
import json
import threading
import time
import socket
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from flask import Flask, jsonify, request, Response
from config_loader import load_config, SecureConfig

# Set service name for logging/metrics
os.environ.setdefault('PREDICTBOT_SERVICE_NAME', 'orchestrator')

# Import shared utilities (with fallback for standalone operation)
try:
    sys.path.insert(0, '/app')
    from shared.logging_config import (
        get_logger,
        log_critical_junction,
        CriticalJunctions,
        log_circuit_breaker,
        log_daily_loss_limit,
        set_correlation_id,
    )
    from shared.metrics import get_metrics_registry, MetricsRegistry
    SHARED_AVAILABLE = True
except ImportError:
    SHARED_AVAILABLE = False
    import logging
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    def get_logger(name):
        return logging.getLogger(name)
    
    def log_critical_junction(*args, **kwargs):
        pass
    
    def log_circuit_breaker(*args, **kwargs):
        pass
    
    def log_daily_loss_limit(*args, **kwargs):
        pass
    
    def set_correlation_id(*args, **kwargs):
        return "no-correlation"
    
    class CriticalJunctions:
        SERVICE_START = "service_start"
        SERVICE_STOP = "service_stop"
        CIRCUIT_BREAKER_TRIGGER = "circuit_breaker_trigger"
        DAILY_LOSS_LIMIT = "daily_loss_limit"
    
    def get_metrics_registry():
        return None

# Get logger
logger = get_logger('orchestrator')

# Get metrics registry
metrics = get_metrics_registry() if SHARED_AVAILABLE else None

# Track service start time for uptime calculation
SERVICE_START_TIME = time.time()

# Flask app for health checks and API
app = Flask(__name__)


@dataclass
class ServiceStatus:
    """Status of a trading service."""
    name: str
    healthy: bool = False
    last_check: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class TradingMetrics:
    """Trading performance metrics."""
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    total_trades: int = 0
    daily_trades: int = 0
    open_positions: int = 0
    last_reset: datetime = field(default_factory=datetime.utcnow)


class RiskManager:
    """Manages risk controls and circuit breakers."""
    
    def __init__(self, config: SecureConfig):
        self.config = config
        self.trading_metrics = TradingMetrics()
        self.circuit_breaker_triggered = False
        self.circuit_breaker_reason: Optional[str] = None
        self.consecutive_failures = 0
        self.last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()
    
    def record_trade(self, pnl: float, success: bool = True, platform: str = "unknown"):
        """Record a trade result."""
        with self._lock:
            self.trading_metrics.total_pnl += pnl
            self.trading_metrics.daily_pnl += pnl
            self.trading_metrics.total_trades += 1
            self.trading_metrics.daily_trades += 1
            
            # Update Prometheus metrics
            if metrics:
                metrics.update_pnl(self.trading_metrics.total_pnl)
                metrics.update_daily_pnl(self.trading_metrics.daily_pnl)
            
            if success:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                self.last_failure_time = datetime.utcnow()
                
                # Record error metric
                if metrics:
                    metrics.record_error("trade_failure")
                
                # Check circuit breaker
                if self.consecutive_failures >= self.config.circuit_breaker_threshold:
                    self._trigger_circuit_breaker("consecutive_failures")
            
            # Check daily loss limit
            if self.trading_metrics.daily_pnl <= -self.config.max_daily_loss:
                self._trigger_daily_loss_limit()
    
    def _trigger_circuit_breaker(self, reason: str = "unknown"):
        """Trigger the circuit breaker."""
        # Log using structured logging
        log_circuit_breaker(
            logger,
            reason=f"Circuit breaker triggered after {self.consecutive_failures} consecutive failures",
            trigger_count=self.consecutive_failures,
            cooldown_seconds=self.config.circuit_breaker_cooldown
        )
        
        self.circuit_breaker_triggered = True
        self.circuit_breaker_reason = reason
        
        # Update metrics
        if metrics:
            metrics.set_circuit_breaker(True, reason)
    
    def _trigger_daily_loss_limit(self):
        """Trigger daily loss limit shutdown."""
        # Log using structured logging
        log_daily_loss_limit(
            logger,
            current_loss=abs(self.trading_metrics.daily_pnl),
            limit=self.config.max_daily_loss
        )
        
        self.circuit_breaker_triggered = True
        self.circuit_breaker_reason = "daily_loss_limit"
        
        # Update metrics
        if metrics:
            metrics.record_loss_limit_trigger("daily")
            metrics.set_circuit_breaker(True, "daily_loss_limit")
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows trading."""
        if not self.circuit_breaker_triggered:
            return True
        
        # Check if cooldown has passed
        if self.last_failure_time:
            cooldown_end = self.last_failure_time + timedelta(
                seconds=self.config.circuit_breaker_cooldown
            )
            if datetime.utcnow() > cooldown_end:
                logger.info("Circuit breaker cooldown complete, resetting")
                self.circuit_breaker_triggered = False
                self.circuit_breaker_reason = None
                self.consecutive_failures = 0
                
                # Update metrics
                if metrics:
                    metrics.set_circuit_breaker(False)
                
                return True
        
        return False
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at midnight)."""
        with self._lock:
            self.trading_metrics.daily_pnl = 0.0
            self.trading_metrics.daily_trades = 0
            self.trading_metrics.last_reset = datetime.utcnow()
            
            # Update Prometheus metrics
            if metrics:
                metrics.update_daily_pnl(0.0)
            
            logger.info("Daily metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current risk status."""
        return {
            "circuit_breaker_triggered": self.circuit_breaker_triggered,
            "circuit_breaker_reason": self.circuit_breaker_reason,
            "consecutive_failures": self.consecutive_failures,
            "trading_allowed": self.check_circuit_breaker(),
            "metrics": {
                "total_pnl": self.trading_metrics.total_pnl,
                "daily_pnl": self.trading_metrics.daily_pnl,
                "total_trades": self.trading_metrics.total_trades,
                "daily_trades": self.trading_metrics.daily_trades,
                "open_positions": self.trading_metrics.open_positions
            },
            "limits": {
                "max_daily_loss": self.config.max_daily_loss,
                "max_total_position": self.config.max_total_position,
                "circuit_breaker_threshold": self.config.circuit_breaker_threshold
            }
        }


class Orchestrator:
    """Main orchestrator for the trading bot stack."""
    
    def __init__(self):
        self.config: Optional[SecureConfig] = None
        self.risk_manager: Optional[RiskManager] = None
        self.services: Dict[str, ServiceStatus] = {}
        self.running = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def initialize(self):
        """Initialize the orchestrator."""
        logger.info("Initializing PredictBot Orchestrator...")
        
        # Load configuration
        self.config = load_config(
            env_path=os.getenv('ENV_FILE', '.env'),
            config_path=os.getenv('CONFIG_FILE', '/app/config/config.yml')
        )
        
        # Initialize risk manager
        self.risk_manager = RiskManager(self.config)
        
        # Initialize service tracking
        self._init_services()
        
        logger.info("Orchestrator initialized successfully")
        logger.info(f"Dry run mode: {self.config.dry_run}")
        
        # Log configuration summary
        status = self.config.get_status_summary()
        logger.info(f"Enabled features: {status['features']}")
    
    def _init_services(self):
        """Initialize service status tracking."""
        service_names = [
            'polymarket-arb',
            'polymarket-mm',
            'polymarket-spike',
            'kalshi-ai',
            'manifold-mm',
            'mcp-server',
            'polyseer'
        ]
        
        for name in service_names:
            self.services[name] = ServiceStatus(name=name)
    
    def start(self):
        """Start the orchestrator."""
        self.running = True
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
        
        logger.info("Orchestrator started")
    
    def stop(self):
        """Stop the orchestrator."""
        self.running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Orchestrator stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        last_daily_reset = datetime.utcnow().date()
        
        while self.running:
            try:
                # Check for daily reset
                today = datetime.utcnow().date()
                if today > last_daily_reset:
                    self.risk_manager.reset_daily_metrics()
                    last_daily_reset = today
                
                # Health check services (placeholder - would use Docker SDK)
                self._check_services()
                
                # Log status periodically
                if datetime.utcnow().second == 0:  # Once per minute
                    self._log_status()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(10)  # Check every 10 seconds
    
    def _check_services(self):
        """Check health of all services."""
        # In production, this would use Docker SDK to check container health
        # For now, we just update timestamps
        for service in self.services.values():
            service.last_check = datetime.utcnow()
    
    def _log_status(self):
        """Log current status."""
        risk_status = self.risk_manager.get_status()
        logger.debug(f"Risk status: {json.dumps(risk_status)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "status": "running" if self.running else "stopped",
            "dry_run": self.config.dry_run if self.config else True,
            "timestamp": datetime.utcnow().isoformat(),
            "risk": self.risk_manager.get_status() if self.risk_manager else {},
            "services": {
                name: {
                    "healthy": svc.healthy,
                    "last_check": svc.last_check.isoformat() if svc.last_check else None,
                    "error_count": svc.error_count
                }
                for name, svc in self.services.items()
            }
        }


# Global orchestrator instance
orchestrator = Orchestrator()


# Flask routes
@app.route('/health')
def health():
    """
    Basic health check endpoint.
    
    Returns a simple healthy/unhealthy status for load balancers
    and container orchestration health checks.
    """
    # Update health metric
    if metrics:
        metrics.set_health_status(True, "main")
        metrics.update_uptime(time.time() - SERVICE_START_TIME)
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/health/detailed')
def health_detailed():
    """
    Detailed health check endpoint.
    
    Returns comprehensive health status of all components including:
    - Service status (running/stopped)
    - Risk manager status
    - Circuit breaker status
    - All dependent services health
    - Resource usage estimates
    """
    uptime_seconds = time.time() - SERVICE_START_TIME
    
    # Check dependent services
    service_health = {}
    for name, svc in orchestrator.services.items():
        service_health[name] = {
            "healthy": svc.healthy,
            "last_check": svc.last_check.isoformat() if svc.last_check else None,
            "error_count": svc.error_count,
            "last_error": svc.last_error
        }
    
    # Build detailed health response
    health_data = {
        "status": "healthy" if orchestrator.running else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "version": os.getenv("VERSION", "1.0.0"),
        "components": {
            "orchestrator": {
                "status": "running" if orchestrator.running else "stopped",
                "healthy": orchestrator.running
            },
            "risk_manager": {
                "status": "active" if orchestrator.risk_manager else "not_initialized",
                "healthy": orchestrator.risk_manager is not None,
                "circuit_breaker_active": orchestrator.risk_manager.circuit_breaker_triggered if orchestrator.risk_manager else False,
                "trading_allowed": orchestrator.risk_manager.check_circuit_breaker() if orchestrator.risk_manager else False
            },
            "config": {
                "status": "loaded" if orchestrator.config else "not_loaded",
                "healthy": orchestrator.config is not None,
                "dry_run": orchestrator.config.dry_run if orchestrator.config else True
            }
        },
        "services": service_health,
        "metrics": {
            "total_pnl": orchestrator.risk_manager.trading_metrics.total_pnl if orchestrator.risk_manager else 0,
            "daily_pnl": orchestrator.risk_manager.trading_metrics.daily_pnl if orchestrator.risk_manager else 0,
            "total_trades": orchestrator.risk_manager.trading_metrics.total_trades if orchestrator.risk_manager else 0,
            "open_positions": orchestrator.risk_manager.trading_metrics.open_positions if orchestrator.risk_manager else 0
        }
    }
    
    # Determine overall health status
    is_healthy = (
        orchestrator.running and
        orchestrator.config is not None and
        orchestrator.risk_manager is not None
    )
    
    # Update metrics
    if metrics:
        metrics.set_health_status(is_healthy, "main")
        metrics.update_uptime(uptime_seconds)
        metrics.update_positions(
            orchestrator.risk_manager.trading_metrics.open_positions if orchestrator.risk_manager else 0
        )
    
    status_code = 200 if is_healthy else 503
    return jsonify(health_data), status_code


@app.route('/metrics')
def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns all metrics in Prometheus text format for scraping.
    """
    if metrics:
        # Update uptime before returning metrics
        metrics.update_uptime(time.time() - SERVICE_START_TIME)
        
        # Get metrics in Prometheus format
        metrics_data = metrics.get_metrics()
        return Response(
            metrics_data,
            mimetype=metrics.get_content_type()
        )
    
    # Return empty metrics if not available
    return Response(
        b"# Metrics not available - prometheus_client not installed\n",
        mimetype="text/plain"
    )


@app.route('/status')
def status():
    """Get full system status."""
    return jsonify(orchestrator.get_status())


@app.route('/risk')
def risk_status():
    """Get risk management status."""
    if orchestrator.risk_manager:
        return jsonify(orchestrator.risk_manager.get_status())
    return jsonify({"error": "Risk manager not initialized"}), 500


@app.route('/config')
def config_status():
    """Get configuration status (with masked secrets)."""
    if orchestrator.config:
        return jsonify(orchestrator.config.get_status_summary())
    return jsonify({"error": "Configuration not loaded"}), 500


@app.route('/circuit-breaker/reset', methods=['POST'])
def reset_circuit_breaker():
    """Manually reset the circuit breaker."""
    if orchestrator.risk_manager:
        orchestrator.risk_manager.circuit_breaker_triggered = False
        orchestrator.risk_manager.circuit_breaker_reason = None
        orchestrator.risk_manager.consecutive_failures = 0
        
        # Update metrics
        if metrics:
            metrics.set_circuit_breaker(False)
        
        logger.info("Circuit breaker manually reset")
        return jsonify({"status": "reset"})
    return jsonify({"error": "Risk manager not initialized"}), 500


@app.route('/trading/stop', methods=['POST'])
def stop_trading():
    """Emergency stop all trading."""
    if orchestrator.risk_manager:
        orchestrator.risk_manager.circuit_breaker_triggered = True
        orchestrator.risk_manager.circuit_breaker_reason = "manual_stop"
        
        # Update metrics
        if metrics:
            metrics.set_circuit_breaker(True, "manual_stop")
        
        logger.warning("Emergency trading stop triggered via API")
        return jsonify({"status": "stopped"})
    return jsonify({"error": "Risk manager not initialized"}), 500


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("PredictBot Stack - Orchestrator")
    logger.info("=" * 60)
    
    try:
        # Initialize orchestrator
        orchestrator.initialize()
        
        # Start orchestrator
        orchestrator.start()
        
        # Log service start as critical junction
        log_critical_junction(
            logger,
            junction_name=CriticalJunctions.SERVICE_START,
            message="Orchestrator service started successfully",
            extra={
                "version": os.getenv("VERSION", "1.0.0"),
                "dry_run": orchestrator.config.dry_run if orchestrator.config else True,
                "port": int(os.getenv('PORT', 8080))
            }
        )
        
        # Set service info in metrics
        if metrics:
            metrics.set_service_info(
                version=os.getenv("VERSION", "1.0.0"),
                service="orchestrator",
                environment=os.getenv("ENVIRONMENT", "development")
            )
        
        # Run Flask app
        port = int(os.getenv('PORT', 8080))
        logger.info(f"Starting health check server on port {port}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if metrics:
            metrics.record_error("fatal_error")
        raise
    finally:
        # Log service stop
        log_critical_junction(
            logger,
            junction_name=CriticalJunctions.SERVICE_STOP,
            message="Orchestrator service stopping",
            extra={
                "uptime_seconds": time.time() - SERVICE_START_TIME
            }
        )
        orchestrator.stop()
        logger.info("Orchestrator shutdown complete")


if __name__ == '__main__':
    main()
