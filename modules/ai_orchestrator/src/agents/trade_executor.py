"""
PredictBot AI Orchestrator - Trade Executor Agent
==================================================

This agent determines final trade execution parameters including
timing, order type, and price limits.

Responsibilities:
- Generate trade signals from forecasts
- Determine execution timing
- Set price limits and order types
- Prioritize trades by expected value
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from .base import BaseAgent, AgentError
from ..state import TradeAction, Urgency


class TradeExecutorAgent(BaseAgent):
    """
    Trade Executor Agent - Determines execution parameters.
    
    This agent converts validated forecasts and risk assessments
    into actionable trade signals with specific execution parameters.
    
    Uses: Ollama for speed (time-sensitive decisions)
    """
    
    def __init__(self, llm_router: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="trade_executor",
            llm_router=llm_router,
            timeout=45.0,  # Fast execution decisions
            config=config
        )
        
        # Configuration
        self.min_confidence = config.get("min_confidence", 0.5) if config else 0.5
        self.min_edge = config.get("min_edge", 0.03) if config else 0.03
        self.max_slippage = config.get("max_slippage", 0.02) if config else 0.02
        self.max_trades_per_cycle = config.get("max_trades_per_cycle", 5) if config else 5
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trade signals from forecasts and risk assessments.
        
        Args:
            state: Current TradingState
            
        Returns:
            Updated TradingState with trade_signals
        """
        forecasts = state.get("forecasts", [])
        risk_assessment = state.get("risk_assessment", {})
        opportunities = state.get("opportunities", [])
        portfolio = state.get("portfolio", {})
        
        if not forecasts:
            self.logger.warning("No forecasts to generate trade signals from")
            state["trade_signals"] = []
            return state
        
        # Get market details
        market_details = {
            m["market_id"]: m
            for m in opportunities
        }
        
        individual_risk = risk_assessment.get("individual", {})
        
        self.logger.info(f"Generating trade signals from {len(forecasts)} forecasts")
        
        # Generate trade signals
        trade_signals = []
        for forecast in forecasts:
            market_id = forecast.get("market_id")
            details = market_details.get(market_id, {})
            risk = individual_risk.get(market_id, {})
            
            # Skip if not tradeable
            if not risk.get("tradeable", False):
                self.logger.debug(f"Skipping {market_id} - not tradeable")
                continue
            
            # Generate signal
            signal = self._generate_signal(
                forecast=forecast,
                details=details,
                risk=risk,
                portfolio=portfolio
            )
            
            if signal:
                trade_signals.append(signal)
        
        # Sort by expected value and limit
        trade_signals.sort(key=lambda x: x.get("expected_value", 0), reverse=True)
        trade_signals = trade_signals[:self.max_trades_per_cycle]
        
        # Log trade signals
        for signal in trade_signals:
            self.log_decision(
                decision_type="trade_signal",
                details={
                    "market_id": signal.get("market_id"),
                    "action": signal.get("action"),
                    "size": signal.get("size"),
                    "expected_value": signal.get("expected_value")
                },
                confidence=signal.get("confidence")
            )
        
        # Update state
        state["trade_signals"] = trade_signals
        state["current_step"] = "trade_execution"
        
        return state
    
    def _generate_signal(
        self,
        forecast: Dict,
        details: Dict,
        risk: Dict,
        portfolio: Dict
    ) -> Optional[Dict]:
        """
        Generate a trade signal for a single forecast.
        
        Args:
            forecast: Forecast data
            details: Market details
            risk: Risk assessment
            portfolio: Current portfolio
            
        Returns:
            Trade signal dictionary or None
        """
        market_id = forecast.get("market_id")
        predicted_prob = forecast.get("predicted_probability", 0.5)
        confidence = forecast.get("confidence", 0.5)
        current_price = details.get("current_price", 0.5)
        platform = details.get("platform", "unknown")
        
        # Check minimum confidence
        if confidence < self.min_confidence:
            self.logger.debug(f"Skipping {market_id} - confidence too low ({confidence:.2%})")
            return None
        
        # Calculate edge
        edge = predicted_prob - current_price
        abs_edge = abs(edge)
        
        # Check minimum edge
        if abs_edge < self.min_edge:
            self.logger.debug(f"Skipping {market_id} - edge too small ({abs_edge:.2%})")
            return None
        
        # Determine action
        if edge > 0:
            action = TradeAction.BUY_YES.value
            direction = "YES"
        else:
            action = TradeAction.BUY_NO.value
            direction = "NO"
        
        # Get position size from risk assessment
        size = risk.get("max_position_size", 0)
        if size <= 0:
            self.logger.debug(f"Skipping {market_id} - zero position size")
            return None
        
        # Calculate max price (with slippage allowance)
        if action == TradeAction.BUY_YES.value:
            max_price = min(predicted_prob, current_price + self.max_slippage)
        else:
            max_price = max(1 - predicted_prob, current_price - self.max_slippage)
        
        # Determine urgency
        urgency = self._determine_urgency(forecast, details, risk)
        
        # Calculate expected value
        expected_value = self._calculate_expected_value(
            predicted_prob=predicted_prob,
            current_price=current_price,
            size=size,
            action=action
        )
        
        # Build reasoning
        reasoning = self._build_reasoning(
            forecast=forecast,
            details=details,
            risk=risk,
            action=action,
            direction=direction
        )
        
        return {
            "signal_id": str(uuid.uuid4()),
            "market_id": market_id,
            "platform": platform,
            "action": action,
            "size": round(size, 2),
            "max_price": round(max_price, 4),
            "urgency": urgency,
            "reasoning": reasoning,
            "confidence": round(confidence, 4),
            "risk_score": round(risk.get("risk_score", 0.5), 4),
            "expected_value": round(expected_value, 2),
            "edge": round(edge, 4),
            "predicted_probability": round(predicted_prob, 4),
            "current_price": round(current_price, 4),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _determine_urgency(
        self,
        forecast: Dict,
        details: Dict,
        risk: Dict
    ) -> str:
        """
        Determine trade urgency based on market conditions.
        
        Args:
            forecast: Forecast data
            details: Market details
            risk: Risk assessment
            
        Returns:
            Urgency level string
        """
        # High urgency if:
        # - Large edge that might disappear
        # - Near resolution
        # - High volatility (price moving fast)
        
        edge = abs(forecast.get("edge_vs_market", 0))
        time_decay_risk = risk.get("time_decay_risk", 0.5)
        volatility_risk = risk.get("volatility_risk", 0.5)
        
        urgency_score = (
            0.4 * min(1.0, edge * 5) +  # Large edge = urgent
            0.3 * time_decay_risk +      # Near resolution = urgent
            0.3 * volatility_risk        # High volatility = urgent
        )
        
        if urgency_score > 0.7:
            return Urgency.IMMEDIATE.value
        elif urgency_score > 0.4:
            return Urgency.NORMAL.value
        else:
            return Urgency.PATIENT.value
    
    def _calculate_expected_value(
        self,
        predicted_prob: float,
        current_price: float,
        size: float,
        action: str
    ) -> float:
        """
        Calculate expected value of the trade.
        
        Args:
            predicted_prob: Our probability estimate
            current_price: Current market price
            size: Position size
            action: Trade action
            
        Returns:
            Expected value in dollars
        """
        if action == TradeAction.BUY_YES.value:
            # Buying YES at current_price
            # Win: get $1, paid current_price -> profit = 1 - current_price
            # Lose: get $0, paid current_price -> loss = current_price
            ev = predicted_prob * (1 - current_price) - (1 - predicted_prob) * current_price
        else:
            # Buying NO at (1 - current_price)
            # Win: get $1, paid (1 - current_price) -> profit = current_price
            # Lose: get $0, paid (1 - current_price) -> loss = 1 - current_price
            ev = (1 - predicted_prob) * current_price - predicted_prob * (1 - current_price)
        
        return ev * size
    
    def _build_reasoning(
        self,
        forecast: Dict,
        details: Dict,
        risk: Dict,
        action: str,
        direction: str
    ) -> str:
        """
        Build human-readable reasoning for the trade signal.
        
        Args:
            forecast: Forecast data
            details: Market details
            risk: Risk assessment
            action: Trade action
            direction: YES or NO
            
        Returns:
            Reasoning string
        """
        predicted_prob = forecast.get("predicted_probability", 0.5)
        current_price = details.get("current_price", 0.5)
        edge = abs(predicted_prob - current_price)
        confidence = forecast.get("confidence", 0.5)
        risk_score = risk.get("risk_score", 0.5)
        
        reasoning_parts = [
            f"Forecast: {predicted_prob:.1%} vs Market: {current_price:.1%} ({edge:.1%} edge)",
            f"Confidence: {confidence:.1%}",
            f"Risk Score: {risk_score:.2f}",
            f"Action: Buy {direction}"
        ]
        
        # Add forecast reasoning if available
        if forecast.get("reasoning"):
            reasoning_parts.append(f"Basis: {forecast['reasoning'][:200]}...")
        
        # Add warnings if any
        warnings = risk.get("warnings", [])
        if warnings:
            reasoning_parts.append(f"Warnings: {'; '.join(warnings[:2])}")
        
        return " | ".join(reasoning_parts)
