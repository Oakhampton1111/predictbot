"""
PredictBot AI Orchestrator - Trading State Schema
==================================================

This module defines the state schema used by the LangGraph workflow.
The TradingState is passed between agents and contains all information
needed for the trading decision pipeline.
"""

from typing import TypedDict, List, Optional, Literal, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class Platform(str, Enum):
    """Supported prediction market platforms."""
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"
    MANIFOLD = "manifold"
    PREDICTIT = "predictit"


class TradeAction(str, Enum):
    """Possible trade actions."""
    BUY_YES = "buy_yes"
    BUY_NO = "buy_no"
    SELL_YES = "sell_yes"
    SELL_NO = "sell_no"
    HOLD = "hold"


class Urgency(str, Enum):
    """Trade urgency levels."""
    IMMEDIATE = "immediate"
    NORMAL = "normal"
    PATIENT = "patient"


class WorkflowStep(str, Enum):
    """Workflow steps in the trading cycle."""
    INITIALIZED = "initialized"
    MARKET_ANALYSIS = "market_analysis"
    NEWS_SENTIMENT = "news_sentiment"
    FORECASTING = "forecasting"
    CRITIQUE = "critique"
    RISK_ASSESSMENT = "risk_assessment"
    TRADE_EXECUTION = "trade_execution"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# TypedDict Schemas (for LangGraph state)
# =============================================================================

class MarketOpportunity(TypedDict):
    """Represents a potential trading opportunity in a prediction market."""
    market_id: str
    platform: str  # Platform enum value
    question: str
    current_price: float
    volume_24h: float
    liquidity_score: float
    end_date: Optional[str]
    category: Optional[str]
    metadata: Optional[Dict[str, Any]]


class Forecast(TypedDict):
    """AI-generated probability forecast for a market."""
    market_id: str
    predicted_probability: float
    confidence: float
    reasoning: str
    sources: List[str]
    model_used: str
    timestamp: str


class CritiqueFeedback(TypedDict):
    """Feedback from the critic agent on a forecast."""
    forecast_id: str
    validation_score: float
    counter_arguments: List[str]
    bias_detected: List[str]
    recommendation: str  # "accept", "revise", "reject"
    revised_probability: Optional[float]


class RiskAssessment(TypedDict):
    """Risk assessment for a potential trade."""
    market_id: str
    risk_score: float  # 0-1, higher = riskier
    kelly_fraction: float  # Optimal bet size as fraction of bankroll
    max_position_size: float
    volatility_estimate: float
    correlation_risk: float
    liquidity_risk: float
    time_decay_risk: float
    warnings: List[str]


class TradeSignal(TypedDict):
    """Final trade signal ready for execution."""
    market_id: str
    platform: str
    action: str  # TradeAction enum value
    size: float
    max_price: float
    urgency: str  # Urgency enum value
    reasoning: str
    confidence: float
    risk_score: float
    expected_value: float


class ExecutedTrade(TypedDict):
    """Record of an executed trade."""
    trade_id: str
    market_id: str
    platform: str
    action: str
    size: float
    price: float
    timestamp: str
    status: str  # "success", "partial", "failed"
    error_message: Optional[str]


class PortfolioState(TypedDict):
    """Current portfolio state across all platforms."""
    positions: Dict[str, Dict[str, Any]]  # market_id -> position details
    available_capital: Dict[str, float]  # platform -> available capital
    total_value: float
    daily_pnl: float
    unrealized_pnl: float
    margin_used: float


class TradingState(TypedDict):
    """
    Main state object passed through the LangGraph workflow.
    
    This contains all information needed for the trading decision pipeline,
    from market data through analysis to final trade execution.
    """
    # Workflow metadata
    cycle_id: str
    started_at: str
    current_step: str  # WorkflowStep enum value
    
    # Market data
    opportunities: List[MarketOpportunity]
    selected_markets: List[str]  # market_ids selected for analysis
    
    # Analysis results
    market_analysis: Dict[str, Any]
    news_sentiment: Dict[str, Any]
    forecasts: List[Forecast]
    critic_feedback: Dict[str, CritiqueFeedback]  # market_id -> feedback
    risk_assessment: Dict[str, RiskAssessment]  # market_id -> assessment
    
    # Trade decisions
    trade_signals: List[TradeSignal]
    executed_trades: List[ExecutedTrade]
    
    # Portfolio state
    portfolio: PortfolioState
    
    # Error handling
    errors: List[str]
    retry_count: int
    max_retries: int


# =============================================================================
# Pydantic Models (for API validation)
# =============================================================================

class MarketOpportunityModel(BaseModel):
    """Pydantic model for MarketOpportunity."""
    market_id: str
    platform: Platform
    question: str
    current_price: float = Field(ge=0, le=1)
    volume_24h: float = Field(ge=0)
    liquidity_score: float = Field(ge=0, le=1)
    end_date: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ForecastModel(BaseModel):
    """Pydantic model for Forecast."""
    market_id: str
    predicted_probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    sources: List[str] = []
    model_used: str
    timestamp: str


class TradeSignalModel(BaseModel):
    """Pydantic model for TradeSignal."""
    market_id: str
    platform: Platform
    action: TradeAction
    size: float = Field(ge=0)
    max_price: float = Field(ge=0, le=1)
    urgency: Urgency = Urgency.NORMAL
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    expected_value: float


class CycleStatusModel(BaseModel):
    """Status of a trading cycle."""
    cycle_id: str
    status: WorkflowStep
    started_at: str
    current_step: str
    markets_analyzed: int
    forecasts_generated: int
    trades_executed: int
    errors: List[str]


# =============================================================================
# Factory Functions
# =============================================================================

def create_initial_state(cycle_id: str) -> TradingState:
    """
    Create an initial TradingState for a new trading cycle.
    
    Args:
        cycle_id: Unique identifier for this trading cycle
        
    Returns:
        Initialized TradingState
    """
    return TradingState(
        cycle_id=cycle_id,
        started_at=datetime.utcnow().isoformat(),
        current_step=WorkflowStep.INITIALIZED.value,
        opportunities=[],
        selected_markets=[],
        market_analysis={},
        news_sentiment={},
        forecasts=[],
        critic_feedback={},
        risk_assessment={},
        trade_signals=[],
        executed_trades=[],
        portfolio=PortfolioState(
            positions={},
            available_capital={},
            total_value=0.0,
            daily_pnl=0.0,
            unrealized_pnl=0.0,
            margin_used=0.0
        ),
        errors=[],
        retry_count=0,
        max_retries=3
    )


def state_to_dict(state: TradingState) -> Dict[str, Any]:
    """Convert TradingState to a serializable dictionary."""
    return dict(state)


def dict_to_state(data: Dict[str, Any]) -> TradingState:
    """Convert a dictionary back to TradingState."""
    return TradingState(**data)
