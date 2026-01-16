"""
PredictBot AI Orchestrator - Forecaster Agent
==============================================

This agent generates probability forecasts for prediction markets
by synthesizing market data, news sentiment, and research.

Responsibilities:
- Generate probability estimates
- Provide confidence intervals
- Document reasoning and sources
- Identify key uncertainties
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import uuid

from .base import BaseAgent, AgentError


# System prompt for forecasting
FORECASTER_SYSTEM_PROMPT = """You are a superforecaster with expertise in prediction markets and probabilistic reasoning.

Your role is to generate accurate probability forecasts for prediction market questions.

FORECASTING METHODOLOGY:

1. BASE RATE ANALYSIS:
   - Historical frequency of similar events
   - Reference class forecasting
   - Regression to the mean

2. EVIDENCE INTEGRATION:
   - Current market price as wisdom of crowds
   - News and sentiment signals
   - Expert opinions and research
   - Quantitative indicators

3. BAYESIAN UPDATING:
   - Start with base rate as prior
   - Update based on new evidence
   - Weight evidence by reliability

4. CALIBRATION:
   - Avoid overconfidence
   - Consider both sides of the argument
   - Account for unknown unknowns

5. UNCERTAINTY QUANTIFICATION:
   - Confidence intervals
   - Key assumptions
   - Potential surprises

IMPORTANT PRINCIPLES:
- Be specific about your reasoning
- Cite sources and evidence
- Acknowledge uncertainty
- Consider contrarian views
- Avoid anchoring on current price

Output your forecast as structured JSON with clear reasoning."""


class ForecasterAgent(BaseAgent):
    """
    Forecaster Agent - Generates probability forecasts.
    
    This agent synthesizes all available information to produce
    probability estimates for prediction market outcomes.
    
    Uses: GPT-4 or Claude for high-stakes forecasts requiring deep reasoning
    """
    
    def __init__(self, llm_router: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="forecaster",
            llm_router=llm_router,
            timeout=180.0,  # Longer timeout for complex reasoning
            config=config
        )
        
        # Configuration
        self.min_confidence = config.get("min_confidence", 0.4) if config else 0.4
        self.edge_threshold = config.get("edge_threshold", 0.05) if config else 0.05
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate probability forecasts for selected markets.
        
        Args:
            state: Current TradingState
            
        Returns:
            Updated TradingState with forecasts
        """
        selected_markets = state.get("selected_markets", [])
        opportunities = state.get("opportunities", [])
        market_analysis = state.get("market_analysis", {})
        news_sentiment = state.get("news_sentiment", {})
        
        if not selected_markets:
            self.logger.warning("No markets selected for forecasting")
            state["forecasts"] = []
            return state
        
        # Get market details
        market_details = {
            m["market_id"]: m
            for m in opportunities
            if m.get("market_id") in selected_markets
        }
        
        self.logger.info(f"Generating forecasts for {len(selected_markets)} markets")
        
        # Generate forecasts
        forecasts = []
        for market_id in selected_markets:
            details = market_details.get(market_id, {})
            analysis = market_analysis.get("results", {}).get(market_id, {})
            sentiment = news_sentiment.get("aggregated", {}).get(market_id, {})
            
            forecast = await self._generate_forecast(
                market_id=market_id,
                details=details,
                analysis=analysis,
                sentiment=sentiment
            )
            
            if forecast:
                forecasts.append(forecast)
                
                # Log significant forecasts
                edge = abs(forecast["predicted_probability"] - details.get("current_price", 0.5))
                if edge >= self.edge_threshold:
                    self.log_decision(
                        decision_type="forecast",
                        details={
                            "market_id": market_id,
                            "predicted_probability": forecast["predicted_probability"],
                            "current_price": details.get("current_price"),
                            "edge": edge
                        },
                        confidence=forecast["confidence"]
                    )
        
        # Update state
        state["forecasts"] = forecasts
        state["current_step"] = "forecasting"
        
        return state
    
    async def _generate_forecast(
        self,
        market_id: str,
        details: Dict,
        analysis: Dict,
        sentiment: Dict
    ) -> Optional[Dict]:
        """
        Generate a forecast for a single market.
        
        Args:
            market_id: Market identifier
            details: Market details
            analysis: Market analysis results
            sentiment: News sentiment results
            
        Returns:
            Forecast dictionary or None if failed
        """
        prompt = self._build_forecast_prompt(details, analysis, sentiment)
        
        try:
            # Use high-quality model for forecasting
            response = await self.call_llm(
                prompt=prompt,
                task_type="reasoning",  # Routes to GPT-4 or Claude
                system_prompt=FORECASTER_SYSTEM_PROMPT,
                temperature=0.4,  # Lower temperature for more consistent forecasts
                max_tokens=2000
            )
            
            result = self.parse_json_response(response)
            
            # Validate and normalize forecast
            forecast = self._validate_forecast(market_id, result, details)
            return forecast
            
        except Exception as e:
            self.logger.error(f"Forecast generation failed for {market_id}: {e}")
            return None
    
    def _build_forecast_prompt(
        self,
        details: Dict,
        analysis: Dict,
        sentiment: Dict
    ) -> str:
        """Build the forecasting prompt with all available information."""
        
        current_price = details.get("current_price", 0.5)
        
        prompt = f"""Generate a probability forecast for the following prediction market:

MARKET QUESTION:
{details.get('question', 'Unknown question')}

MARKET DATA:
- Platform: {details.get('platform', 'Unknown')}
- Current Price (Market Probability): {current_price:.2%}
- 24h Volume: ${details.get('volume_24h', 0):,.0f}
- Liquidity Score: {details.get('liquidity_score', 0):.2f}
- Resolution Date: {details.get('end_date', 'Unknown')}

MARKET ANALYSIS:
- Liquidity Assessment: {analysis.get('liquidity_assessment', 'Unknown')}
- Trend Direction: {analysis.get('trend_direction', 'Unknown')}
- Volatility Estimate: {analysis.get('volatility_estimate', 0.5):.2f}
- Trading Opportunity: {analysis.get('trading_opportunity', 'Unknown')}

NEWS SENTIMENT:
- Sentiment Direction: {sentiment.get('direction', 'neutral')}
- Sentiment Score: {sentiment.get('sentiment_score', 0):.2f}
- Confidence: {sentiment.get('confidence', 0.5):.2f}
- Key Events: {', '.join(sentiment.get('key_events', ['None']))}

YOUR TASK:
1. Analyze all available information
2. Consider base rates and reference classes
3. Evaluate the current market price
4. Generate your probability forecast

Provide your forecast as JSON:
{{
    "predicted_probability": 0.0 to 1.0,
    "confidence": 0.0 to 1.0 (how confident you are in your forecast),
    "confidence_interval_low": 0.0 to 1.0,
    "confidence_interval_high": 0.0 to 1.0,
    "reasoning": "detailed explanation of your forecast",
    "key_factors": ["list of most important factors"],
    "sources": ["information sources used"],
    "assumptions": ["key assumptions made"],
    "risks": ["potential risks to this forecast"],
    "edge_vs_market": "explanation of why you differ from market price (if applicable)"
}}"""
        
        return prompt
    
    def _validate_forecast(
        self,
        market_id: str,
        result: Dict,
        details: Dict
    ) -> Dict:
        """
        Validate and normalize a forecast result.
        
        Args:
            market_id: Market identifier
            result: Raw LLM result
            details: Market details
            
        Returns:
            Validated forecast dictionary
        """
        # Extract and validate probability
        predicted_prob = result.get("predicted_probability", 0.5)
        predicted_prob = max(0.01, min(0.99, float(predicted_prob)))
        
        # Extract and validate confidence
        confidence = result.get("confidence", 0.5)
        confidence = max(0.0, min(1.0, float(confidence)))
        
        # Validate confidence interval
        ci_low = result.get("confidence_interval_low", predicted_prob - 0.1)
        ci_high = result.get("confidence_interval_high", predicted_prob + 0.1)
        ci_low = max(0.0, min(predicted_prob, float(ci_low)))
        ci_high = max(predicted_prob, min(1.0, float(ci_high)))
        
        # Calculate edge vs market
        current_price = details.get("current_price", 0.5)
        edge = predicted_prob - current_price
        
        return {
            "market_id": market_id,
            "predicted_probability": round(predicted_prob, 4),
            "confidence": round(confidence, 4),
            "confidence_interval": [round(ci_low, 4), round(ci_high, 4)],
            "reasoning": result.get("reasoning", ""),
            "key_factors": result.get("key_factors", []),
            "sources": result.get("sources", []),
            "assumptions": result.get("assumptions", []),
            "risks": result.get("risks", []),
            "edge_vs_market": round(edge, 4),
            "model_used": "gpt-4",  # Would be set by LLM router
            "timestamp": datetime.utcnow().isoformat(),
            "forecast_id": str(uuid.uuid4())
        }
