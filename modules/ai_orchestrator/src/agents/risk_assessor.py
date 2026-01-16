"""
PredictBot AI Orchestrator - Risk Assessor Agent
=================================================

This agent evaluates trade risk and determines optimal position sizing
using Kelly criterion and other risk management techniques.

Responsibilities:
- Calculate risk scores for trades
- Determine optimal position sizes (Kelly criterion)
- Assess portfolio correlation risk
- Identify risk warnings
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import math

from .base import BaseAgent, AgentError


class RiskAssessorAgent(BaseAgent):
    """
    Risk Assessor Agent - Evaluates trade risk and position sizing.
    
    This agent calculates risk metrics and determines optimal bet sizes
    using the Kelly criterion and portfolio risk considerations.
    
    Uses: Ollama for fast calculations (mostly mathematical)
    """
    
    def __init__(self, llm_router: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="risk_assessor",
            llm_router=llm_router,
            timeout=60.0,
            config=config
        )
        
        # Risk configuration
        self.max_position_pct = config.get("max_position_pct", 0.1) if config else 0.1  # 10% max per position
        self.max_daily_risk = config.get("max_daily_risk", 0.05) if config else 0.05  # 5% max daily risk
        self.kelly_fraction = config.get("kelly_fraction", 0.25) if config else 0.25  # Use 1/4 Kelly
        self.min_edge = config.get("min_edge", 0.03) if config else 0.03  # 3% minimum edge
        self.max_correlation = config.get("max_correlation", 0.7) if config else 0.7
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for forecasted markets and determine position sizes.
        
        Args:
            state: Current TradingState
            
        Returns:
            Updated TradingState with risk_assessment
        """
        forecasts = state.get("forecasts", [])
        opportunities = state.get("opportunities", [])
        portfolio = state.get("portfolio", {})
        critic_feedback = state.get("critic_feedback", {})
        
        if not forecasts:
            self.logger.warning("No forecasts to assess risk for")
            state["risk_assessment"] = {}
            return state
        
        # Get market details
        market_details = {
            m["market_id"]: m
            for m in opportunities
        }
        
        self.logger.info(f"Assessing risk for {len(forecasts)} forecasts")
        
        # Calculate risk for each forecast
        risk_assessments = {}
        for forecast in forecasts:
            market_id = forecast.get("market_id")
            details = market_details.get(market_id, {})
            critique = critic_feedback.get(market_id, {})
            
            assessment = self._assess_risk(
                forecast=forecast,
                details=details,
                critique=critique,
                portfolio=portfolio
            )
            
            risk_assessments[market_id] = assessment
            
            # Log high-risk assessments
            if assessment.get("risk_score", 0) > 0.7:
                self.log_decision(
                    decision_type="high_risk_warning",
                    details={
                        "market_id": market_id,
                        "risk_score": assessment.get("risk_score"),
                        "warnings": assessment.get("warnings")
                    }
                )
        
        # Check portfolio-level risk
        portfolio_risk = self._assess_portfolio_risk(risk_assessments, portfolio)
        
        # Update state
        state["risk_assessment"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "individual": risk_assessments,
            "portfolio": portfolio_risk
        }
        state["current_step"] = "risk_assessment"
        
        return state
    
    def _assess_risk(
        self,
        forecast: Dict,
        details: Dict,
        critique: Dict,
        portfolio: Dict
    ) -> Dict:
        """
        Assess risk for a single forecast.
        
        Args:
            forecast: Forecast data
            details: Market details
            critique: Critic feedback
            portfolio: Current portfolio state
            
        Returns:
            Risk assessment dictionary
        """
        warnings = []
        
        # Extract key values
        predicted_prob = forecast.get("predicted_probability", 0.5)
        confidence = forecast.get("confidence", 0.5)
        current_price = details.get("current_price", 0.5)
        liquidity_score = details.get("liquidity_score", 0.5)
        volume_24h = details.get("volume_24h", 0)
        validation_score = critique.get("validation_score", 0.5)
        
        # Calculate edge
        edge = predicted_prob - current_price
        abs_edge = abs(edge)
        
        # Check minimum edge
        if abs_edge < self.min_edge:
            warnings.append(f"Edge ({abs_edge:.2%}) below minimum threshold ({self.min_edge:.2%})")
        
        # Calculate Kelly fraction
        kelly = self._calculate_kelly(predicted_prob, current_price, confidence)
        
        # Apply fractional Kelly
        adjusted_kelly = kelly * self.kelly_fraction
        
        # Calculate risk components
        liquidity_risk = 1.0 - liquidity_score
        volatility_risk = self._estimate_volatility_risk(details)
        time_decay_risk = self._calculate_time_decay_risk(details)
        correlation_risk = self._estimate_correlation_risk(forecast, portfolio)
        
        # Aggregate risk score (0-1, higher = riskier)
        risk_score = (
            0.25 * liquidity_risk +
            0.25 * volatility_risk +
            0.20 * time_decay_risk +
            0.15 * correlation_risk +
            0.15 * (1.0 - validation_score)
        )
        
        # Add warnings based on risk factors
        if liquidity_risk > 0.6:
            warnings.append("Low liquidity - may have difficulty exiting position")
        if volatility_risk > 0.7:
            warnings.append("High volatility - price may move significantly")
        if time_decay_risk > 0.8:
            warnings.append("Near resolution - limited time for price correction")
        if correlation_risk > 0.5:
            warnings.append("High correlation with existing positions")
        if validation_score < 0.4:
            warnings.append("Forecast received low validation score from critic")
        
        # Calculate maximum position size
        available_capital = sum(portfolio.get("available_capital", {}).values()) or 10000
        max_position = min(
            available_capital * self.max_position_pct,
            available_capital * adjusted_kelly,
            volume_24h * 0.1  # Don't exceed 10% of daily volume
        )
        
        # Reduce position size based on risk
        risk_adjusted_position = max_position * (1.0 - risk_score * 0.5)
        
        return {
            "market_id": forecast.get("market_id"),
            "risk_score": round(risk_score, 4),
            "kelly_fraction": round(kelly, 4),
            "adjusted_kelly": round(adjusted_kelly, 4),
            "max_position_size": round(max(0, risk_adjusted_position), 2),
            "edge": round(edge, 4),
            "abs_edge": round(abs_edge, 4),
            "liquidity_risk": round(liquidity_risk, 4),
            "volatility_risk": round(volatility_risk, 4),
            "time_decay_risk": round(time_decay_risk, 4),
            "correlation_risk": round(correlation_risk, 4),
            "warnings": warnings,
            "tradeable": abs_edge >= self.min_edge and risk_score < 0.8
        }
    
    def _calculate_kelly(
        self,
        predicted_prob: float,
        market_price: float,
        confidence: float
    ) -> float:
        """
        Calculate Kelly criterion bet fraction.
        
        Kelly formula: f* = (bp - q) / b
        where:
        - b = odds received on the bet (payout ratio)
        - p = probability of winning
        - q = probability of losing (1 - p)
        
        Args:
            predicted_prob: Our probability estimate
            market_price: Current market price
            confidence: Confidence in our estimate
            
        Returns:
            Kelly fraction (can be negative for short)
        """
        # Adjust probability by confidence
        # Blend toward 0.5 based on uncertainty
        adjusted_prob = confidence * predicted_prob + (1 - confidence) * 0.5
        
        # Determine if we're betting YES or NO
        if adjusted_prob > market_price:
            # Bet YES
            p = adjusted_prob
            b = (1 - market_price) / market_price  # Payout ratio for YES
        else:
            # Bet NO
            p = 1 - adjusted_prob
            b = market_price / (1 - market_price)  # Payout ratio for NO
        
        q = 1 - p
        
        # Kelly formula
        if b <= 0:
            return 0.0
        
        kelly = (b * p - q) / b
        
        # Clamp to reasonable range
        return max(0.0, min(1.0, kelly))
    
    def _estimate_volatility_risk(self, details: Dict) -> float:
        """
        Estimate volatility risk based on market characteristics.
        
        Args:
            details: Market details
            
        Returns:
            Volatility risk score (0-1)
        """
        # Use liquidity as proxy for volatility (low liquidity = high volatility)
        liquidity = details.get("liquidity_score", 0.5)
        
        # Price near extremes tends to be more volatile
        price = details.get("current_price", 0.5)
        price_extremity = 2 * abs(price - 0.5)  # 0 at 0.5, 1 at 0 or 1
        
        # Combine factors
        volatility_risk = 0.6 * (1 - liquidity) + 0.4 * price_extremity
        
        return min(1.0, volatility_risk)
    
    def _calculate_time_decay_risk(self, details: Dict) -> float:
        """
        Calculate time decay risk based on resolution date.
        
        Args:
            details: Market details
            
        Returns:
            Time decay risk score (0-1)
        """
        end_date_str = details.get("end_date")
        if not end_date_str:
            return 0.5  # Unknown, assume moderate risk
        
        try:
            from dateutil.parser import parse
            end_date = parse(end_date_str)
            now = datetime.utcnow()
            
            if end_date.tzinfo:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            
            days_remaining = (end_date - now).days
            
            if days_remaining <= 0:
                return 1.0  # Already expired
            elif days_remaining <= 1:
                return 0.9
            elif days_remaining <= 3:
                return 0.7
            elif days_remaining <= 7:
                return 0.5
            elif days_remaining <= 30:
                return 0.3
            else:
                return 0.1
                
        except Exception:
            return 0.5  # Parse error, assume moderate risk
    
    def _estimate_correlation_risk(
        self,
        forecast: Dict,
        portfolio: Dict
    ) -> float:
        """
        Estimate correlation risk with existing positions.
        
        Args:
            forecast: Current forecast
            portfolio: Current portfolio state
            
        Returns:
            Correlation risk score (0-1)
        """
        positions = portfolio.get("positions", {})
        
        if not positions:
            return 0.0  # No existing positions
        
        # Simple heuristic: more positions = higher correlation risk
        # In production, would calculate actual correlations
        num_positions = len(positions)
        
        if num_positions >= 10:
            return 0.7
        elif num_positions >= 5:
            return 0.5
        elif num_positions >= 3:
            return 0.3
        else:
            return 0.1
    
    def _assess_portfolio_risk(
        self,
        risk_assessments: Dict[str, Dict],
        portfolio: Dict
    ) -> Dict:
        """
        Assess overall portfolio risk.
        
        Args:
            risk_assessments: Individual risk assessments
            portfolio: Current portfolio state
            
        Returns:
            Portfolio risk assessment
        """
        if not risk_assessments:
            return {
                "total_risk_score": 0.0,
                "concentration_risk": 0.0,
                "total_exposure": 0.0,
                "warnings": []
            }
        
        warnings = []
        
        # Calculate aggregate metrics
        risk_scores = [a.get("risk_score", 0) for a in risk_assessments.values()]
        avg_risk = sum(risk_scores) / len(risk_scores)
        max_risk = max(risk_scores)
        
        # Calculate total proposed exposure
        total_exposure = sum(
            a.get("max_position_size", 0)
            for a in risk_assessments.values()
            if a.get("tradeable", False)
        )
        
        # Check concentration
        available_capital = sum(portfolio.get("available_capital", {}).values()) or 10000
        concentration = total_exposure / available_capital if available_capital > 0 else 0
        
        if concentration > 0.5:
            warnings.append(f"High concentration risk: {concentration:.1%} of capital in proposed trades")
        
        if max_risk > 0.8:
            warnings.append("At least one trade has very high risk score")
        
        if avg_risk > 0.6:
            warnings.append("Average risk across trades is elevated")
        
        return {
            "total_risk_score": round(avg_risk, 4),
            "max_individual_risk": round(max_risk, 4),
            "concentration_risk": round(concentration, 4),
            "total_exposure": round(total_exposure, 2),
            "tradeable_count": sum(1 for a in risk_assessments.values() if a.get("tradeable", False)),
            "warnings": warnings
        }
