"""
PredictBot AI Orchestrator - FastAPI Entry Point
=================================================

This module provides the FastAPI application for the AI orchestrator,
exposing endpoints for trading cycle control, monitoring, and WebSocket
real-time updates.

Endpoints:
- GET  /health          - Health check
- GET  /metrics         - Prometheus metrics
- POST /api/cycle/start - Start a trading cycle
- GET  /api/cycle/{id}  - Get cycle status
- GET  /api/forecasts   - Get recent forecasts
- GET  /api/signals     - Get trade signals
- WS   /ws              - WebSocket for real-time updates
"""

import os
import sys
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import json
import uuid

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from shared.logging_config import get_logger, log_critical_junction, CriticalJunctions
    from shared.metrics import get_metrics_registry
except ImportError:
    import logging
    def get_logger(name: str, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def log_critical_junction(*args, **kwargs):
        pass
    
    class CriticalJunctions:
        SERVICE_START = "service_start"
        SERVICE_STOP = "service_stop"
    
    def get_metrics_registry():
        return None

from .graph import TradingWorkflow, create_workflow
from .state import (
    TradingState,
    MarketOpportunityModel,
    TradeSignalModel,
    CycleStatusModel,
    WorkflowStep,
)


# Initialize logger
logger = get_logger("ai_orchestrator.main")

# Global workflow instance
workflow: Optional[TradingWorkflow] = None

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Recent cycles cache
recent_cycles: Dict[str, TradingState] = {}


# =============================================================================
# Pydantic Models for API
# =============================================================================

class StartCycleRequest(BaseModel):
    """Request to start a trading cycle."""
    opportunities: List[Dict[str, Any]] = Field(
        ...,
        description="List of market opportunities to analyze"
    )
    portfolio: Optional[Dict[str, Any]] = Field(
        None,
        description="Current portfolio state"
    )
    cycle_id: Optional[str] = Field(
        None,
        description="Optional cycle identifier"
    )


class StartCycleResponse(BaseModel):
    """Response from starting a trading cycle."""
    cycle_id: str
    status: str
    message: str


class CycleStatusResponse(BaseModel):
    """Response with cycle status."""
    cycle_id: str
    status: str
    current_step: str
    started_at: str
    markets_analyzed: int
    forecasts_generated: int
    trade_signals: int
    errors: List[str]


class ForecastResponse(BaseModel):
    """Response with forecast data."""
    market_id: str
    predicted_probability: float
    confidence: float
    reasoning: str
    timestamp: str


class TradeSignalResponse(BaseModel):
    """Response with trade signal data."""
    signal_id: str
    market_id: str
    platform: str
    action: str
    size: float
    max_price: float
    urgency: str
    confidence: float
    expected_value: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: str
    components: Dict[str, bool]


class StatsResponse(BaseModel):
    """Statistics response."""
    agents: Dict[str, Any]
    llm: Dict[str, Any]
    cycles: Dict[str, Any]


# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global workflow
    
    # Startup
    logger.info("Starting AI Orchestrator service")
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.SERVICE_START,
        message="AI Orchestrator starting"
    )
    
    # Initialize workflow
    workflow = create_workflow()
    
    # Set service info in metrics
    metrics = get_metrics_registry()
    if metrics:
        metrics.set_service_info(
            name="ai_orchestrator",
            version="0.1.0"
        )
        metrics.set_health_status(True, "main")
    
    logger.info("AI Orchestrator service started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Orchestrator service")
    log_critical_junction(
        logger,
        junction_name=CriticalJunctions.SERVICE_STOP,
        message="AI Orchestrator stopping"
    )
    
    # Close WebSocket connections
    for connection in active_connections:
        try:
            await connection.close()
        except Exception:
            pass
    
    logger.info("AI Orchestrator service stopped")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="PredictBot AI Orchestrator",
    description="LangGraph-based multi-agent system for prediction market trading",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Metrics Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    components = {
        "workflow": workflow is not None,
        "llm_router": workflow.llm_router is not None if workflow else False,
    }
    
    # Check Ollama health
    if workflow and workflow.llm_router:
        ollama_adapter = workflow.llm_router._adapters.get("ollama")
        if ollama_adapter:
            try:
                components["ollama"] = await ollama_adapter.check_health()
            except Exception:
                components["ollama"] = False
    
    all_healthy = all(components.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        service="ai_orchestrator",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        components=components
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    registry = get_metrics_registry()
    if registry:
        return Response(
            content=registry.get_metrics(),
            media_type=registry.get_content_type()
        )
    return Response(content=b"", media_type="text/plain")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get service statistics."""
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    return StatsResponse(
        agents=workflow.get_agent_stats(),
        llm=workflow.get_llm_stats(),
        cycles={
            "recent_count": len(recent_cycles),
            "active": sum(
                1 for c in recent_cycles.values()
                if c.get("current_step") not in [
                    WorkflowStep.COMPLETED.value,
                    WorkflowStep.FAILED.value
                ]
            )
        }
    )


# =============================================================================
# Trading Cycle Endpoints
# =============================================================================

@app.post("/api/cycle/start", response_model=StartCycleResponse)
async def start_cycle(
    request: StartCycleRequest,
    background_tasks: BackgroundTasks
):
    """Start a new trading cycle."""
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    cycle_id = request.cycle_id or str(uuid.uuid4())
    
    # Check if cycle already exists
    if cycle_id in recent_cycles:
        raise HTTPException(
            status_code=400,
            detail=f"Cycle {cycle_id} already exists"
        )
    
    logger.info(f"Starting trading cycle {cycle_id}")
    
    # Run cycle in background
    background_tasks.add_task(
        run_cycle_background,
        cycle_id,
        request.opportunities,
        request.portfolio
    )
    
    return StartCycleResponse(
        cycle_id=cycle_id,
        status="started",
        message=f"Trading cycle {cycle_id} started with {len(request.opportunities)} opportunities"
    )


async def run_cycle_background(
    cycle_id: str,
    opportunities: List[Dict],
    portfolio: Optional[Dict]
):
    """Run a trading cycle in the background."""
    try:
        result = await workflow.run_cycle(
            opportunities=opportunities,
            portfolio=portfolio,
            cycle_id=cycle_id
        )
        
        # Cache result
        recent_cycles[cycle_id] = result
        
        # Broadcast to WebSocket clients
        await broadcast_update({
            "type": "cycle_complete",
            "cycle_id": cycle_id,
            "status": result.get("current_step"),
            "trade_signals": len(result.get("trade_signals", []))
        })
        
    except Exception as e:
        logger.exception(f"Cycle {cycle_id} failed: {e}")
        recent_cycles[cycle_id] = {
            "cycle_id": cycle_id,
            "current_step": WorkflowStep.FAILED.value,
            "errors": [str(e)]
        }


@app.get("/api/cycle/{cycle_id}", response_model=CycleStatusResponse)
async def get_cycle_status(cycle_id: str):
    """Get the status of a trading cycle."""
    # Check cache first
    if cycle_id in recent_cycles:
        state = recent_cycles[cycle_id]
    elif workflow:
        # Try to get from Redis
        state = await workflow.get_cycle_state(cycle_id)
        if state:
            recent_cycles[cycle_id] = state
    else:
        state = None
    
    if not state:
        raise HTTPException(status_code=404, detail=f"Cycle {cycle_id} not found")
    
    return CycleStatusResponse(
        cycle_id=cycle_id,
        status=state.get("current_step", "unknown"),
        current_step=state.get("current_step", "unknown"),
        started_at=state.get("started_at", ""),
        markets_analyzed=len(state.get("selected_markets", [])),
        forecasts_generated=len(state.get("forecasts", [])),
        trade_signals=len(state.get("trade_signals", [])),
        errors=state.get("errors", [])
    )


@app.get("/api/forecasts")
async def get_forecasts(cycle_id: Optional[str] = None, limit: int = 20):
    """Get recent forecasts."""
    forecasts = []
    
    if cycle_id:
        # Get forecasts for specific cycle
        state = recent_cycles.get(cycle_id)
        if state:
            forecasts = state.get("forecasts", [])
    else:
        # Get forecasts from all recent cycles
        for state in recent_cycles.values():
            forecasts.extend(state.get("forecasts", []))
    
    # Sort by timestamp and limit
    forecasts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    forecasts = forecasts[:limit]
    
    return {"forecasts": forecasts, "count": len(forecasts)}


@app.get("/api/signals")
async def get_signals(cycle_id: Optional[str] = None, limit: int = 20):
    """Get trade signals."""
    signals = []
    
    if cycle_id:
        # Get signals for specific cycle
        state = recent_cycles.get(cycle_id)
        if state:
            signals = state.get("trade_signals", [])
    else:
        # Get signals from all recent cycles
        for state in recent_cycles.values():
            signals.extend(state.get("trade_signals", []))
    
    # Sort by expected value and limit
    signals.sort(key=lambda x: x.get("expected_value", 0), reverse=True)
    signals = signals[:limit]
    
    return {"signals": signals, "count": len(signals)}


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            
            # Handle subscription requests
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    await websocket.send_json({
                        "type": "subscribed",
                        "message": "Subscribed to updates"
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(active_connections)}")


async def broadcast_update(message: Dict[str, Any]):
    """Broadcast an update to all connected WebSocket clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", "8081"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.environ.get("DEBUG", "false").lower() == "true"
    )
