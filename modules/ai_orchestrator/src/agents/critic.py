"""
PredictBot AI Orchestrator - Critic Agent
==========================================

This agent validates forecasts by challenging assumptions,
identifying biases, and providing counter-arguments.

Responsibilities:
- Challenge forecast assumptions
- Identify potential biases
- Provide counter-arguments
- Suggest forecast revisions
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .base import BaseAgent, AgentError


# System prompt for critique
CRITIC_SYSTEM_PROMPT = """You are a critical analyst specializing in challenging forecasts and identifying biases.

Your role is to rigorously evaluate probability forecasts and identify potential weaknesses.

CRITIQUE FRAMEWORK:

1. ASSUMPTION ANALYSIS:
   - Identify implicit assumptions
   - Challenge key premises
   - Test logical consistency

2. BIAS DETECTION:
   - Anchoring bias (over-reliance on current price)
   - Confirmation bias (selective evidence)
   - Overconfidence bias
   - Recency bias
   - Availability bias

3. COUNTER-ARGUMENTS:
   - Steel-man opposing views
   - Identify overlooked factors
   - Consider alternative scenarios

4. EVIDENCE EVALUATION:
   - Source reliability
   - Sample size issues
   - Correlation vs causation
   - Missing data

5. CALIBRATION CHECK:
   - Is confidence level appropriate?
   - Are uncertainty bounds reasonable?
   - Historical accuracy of similar forecasts

IMPORTANT:
- Be constructively critical, not dismissive
- Provide specific, actionable feedback
- Suggest concrete improvements
- Consider both over and under-estimation

Output your critique as structured JSON."""


class CriticAgent(BaseAgent):
    """
    Critic Agent - Validates and challenges forecasts.
    
    This agent provides an adversarial review of forecasts to
    improve accuracy and identify potential issues.
    
    Uses: Different model than Forecaster to avoid confirmation bias
    """
    
    def __init__(self, llm_router: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="critic",
            llm_router=llm_router,
            timeout=120.0,
            config=config
        )
        
        # Configuration
        self.min_validation_score = config.get("min_validation_score", 0.5) if config else 0.5
        self.revision_threshold = config.get("revision_threshold", 0.3) if config else 0.3
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critique forecasts and provide validation feedback.
        
        Args:
            state: Current TradingState
            
        Returns:
            Updated TradingState with critic_feedback
        """
        forecasts = state.get("forecasts", [])
        opportunities = state.get("opportunities", [])
        
        if not forecasts:
            self.logger.warning("No forecasts to critique")
            state["critic_feedback"] = {}
            return state
        
        # Get market details for context
        market_details = {
            m["market_id"]: m
            for m in opportunities
        }
        
        self.logger.info(f"Critiquing {len(forecasts)} forecasts")
        
        # Critique each forecast
        feedback = {}
        for forecast in forecasts:
            market_id = forecast.get("market_id")
            details = market_details.get(market_id, {})
            
            critique = await self._critique_forecast(forecast, details)
            feedback[market_id] = critique
            
            # Log significant critiques
            if critique.get("recommendation") == "reject":
                self.log_decision(
                    decision_type="forecast_rejection",
                    details={
                        "market_id": market_id,
                        "validation_score": critique.get("validation_score"),
                        "biases_detected": critique.get("biases_detected")
                    }
                )
        
        # Update forecasts based on critique
        revised_forecasts = self._apply_revisions(forecasts, feedback)
        
        # Update state
        state["critic_feedback"] = feedback
        state["forecasts"] = revised_forecasts
        state["current_step"] = "critique"
        
        return state
    
    async def _critique_forecast(
        self,
        forecast: Dict,
        details: Dict
    ) -> Dict:
        """
        Generate critique for a single forecast.
        
        Args:
            forecast: Forecast to critique
            details: Market details
            
        Returns:
            Critique feedback dictionary
        """
        prompt = self._build_critique_prompt(forecast, details)
        
        try:
            # Use a different model than the forecaster to avoid bias
            # If forecaster used GPT-4, critic uses Claude (or vice versa)
            response = await self.call_llm(
                prompt=prompt,
                task_type="critique",  # Routes to alternative model
                system_prompt=CRITIC_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=2000
            )
            
            result = self.parse_json_response(response)
            return self._validate_critique(result, forecast)
            
        except Exception as e:
            self.logger.error(f"Critique failed for {forecast.get('market_id')}: {e}")
            return self._default_critique()
    
    def _build_critique_prompt(self, forecast: Dict, details: Dict) -> str:
        """Build the critique prompt."""
        
        return f"""Critically evaluate the following probability forecast:

MARKET QUESTION:
{details.get('question', 'Unknown')}

CURRENT MARKET PRICE: {details.get('current_price', 0.5):.2%}

FORECAST:
- Predicted Probability: {forecast.get('predicted_probability', 0.5):.2%}
- Confidence: {forecast.get('confidence', 0.5):.2%}
- Confidence Interval: {forecast.get('confidence_interval', [0.4, 0.6])}
- Edge vs Market: {forecast.get('edge_vs_market', 0):.2%}

FORECASTER'S REASONING:
{forecast.get('reasoning', 'No reasoning provided')}

KEY FACTORS CITED:
{json.dumps(forecast.get('key_factors', []), indent=2)}

ASSUMPTIONS MADE:
{json.dumps(forecast.get('assumptions', []), indent=2)}

YOUR TASK:
1. Identify weaknesses in the reasoning
2. Detect potential biases
3. Provide counter-arguments
4. Evaluate if the confidence level is appropriate
5. Suggest revisions if needed

Provide your critique as JSON:
{{
    "validation_score": 0.0 to 1.0 (overall quality of forecast),
    "reasoning_quality": 0.0 to 1.0,
    "evidence_quality": 0.0 to 1.0,
    "calibration_quality": 0.0 to 1.0,
    "biases_detected": ["list of biases found"],
    "counter_arguments": ["list of counter-arguments"],
    "overlooked_factors": ["factors not considered"],
    "assumption_issues": ["problems with assumptions"],
    "recommendation": "accept" | "revise" | "reject",
    "suggested_probability": null or 0.0 to 1.0 (if revision recommended),
    "suggested_confidence": null or 0.0 to 1.0,
    "critique_summary": "brief summary of main issues"
}}"""
    
    def _validate_critique(self, result: Dict, forecast: Dict) -> Dict:
        """Validate and normalize critique result."""
        
        # Extract and validate scores
        validation_score = max(0.0, min(1.0, result.get("validation_score", 0.5)))
        reasoning_quality = max(0.0, min(1.0, result.get("reasoning_quality", 0.5)))
        evidence_quality = max(0.0, min(1.0, result.get("evidence_quality", 0.5)))
        calibration_quality = max(0.0, min(1.0, result.get("calibration_quality", 0.5)))
        
        # Validate recommendation
        recommendation = result.get("recommendation", "accept")
        if recommendation not in ["accept", "revise", "reject"]:
            recommendation = "accept" if validation_score >= 0.5 else "revise"
        
        # Validate suggested probability
        suggested_prob = result.get("suggested_probability")
        if suggested_prob is not None:
            suggested_prob = max(0.01, min(0.99, float(suggested_prob)))
        
        return {
            "forecast_id": forecast.get("forecast_id"),
            "validation_score": round(validation_score, 4),
            "reasoning_quality": round(reasoning_quality, 4),
            "evidence_quality": round(evidence_quality, 4),
            "calibration_quality": round(calibration_quality, 4),
            "biases_detected": result.get("biases_detected", []),
            "counter_arguments": result.get("counter_arguments", []),
            "overlooked_factors": result.get("overlooked_factors", []),
            "assumption_issues": result.get("assumption_issues", []),
            "recommendation": recommendation,
            "suggested_probability": suggested_prob,
            "suggested_confidence": result.get("suggested_confidence"),
            "critique_summary": result.get("critique_summary", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _default_critique(self) -> Dict:
        """Return default critique when analysis fails."""
        return {
            "validation_score": 0.5,
            "reasoning_quality": 0.5,
            "evidence_quality": 0.5,
            "calibration_quality": 0.5,
            "biases_detected": [],
            "counter_arguments": [],
            "overlooked_factors": [],
            "assumption_issues": [],
            "recommendation": "accept",
            "suggested_probability": None,
            "suggested_confidence": None,
            "critique_summary": "Unable to generate critique - defaulting to accept",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _apply_revisions(
        self,
        forecasts: List[Dict],
        feedback: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Apply critic revisions to forecasts.
        
        Args:
            forecasts: Original forecasts
            feedback: Critic feedback per market
            
        Returns:
            Revised forecasts
        """
        revised = []
        
        for forecast in forecasts:
            market_id = forecast.get("market_id")
            critique = feedback.get(market_id, {})
            
            # Skip rejected forecasts
            if critique.get("recommendation") == "reject":
                self.logger.info(f"Forecast for {market_id} rejected by critic")
                continue
            
            # Apply revisions if recommended
            if critique.get("recommendation") == "revise":
                revised_forecast = forecast.copy()
                
                # Apply suggested probability if provided
                if critique.get("suggested_probability") is not None:
                    original_prob = forecast.get("predicted_probability", 0.5)
                    suggested_prob = critique["suggested_probability"]
                    
                    # Blend original and suggested (weighted average)
                    revised_prob = 0.6 * original_prob + 0.4 * suggested_prob
                    revised_forecast["predicted_probability"] = round(revised_prob, 4)
                    revised_forecast["revised"] = True
                    revised_forecast["original_probability"] = original_prob
                
                # Apply suggested confidence if provided
                if critique.get("suggested_confidence") is not None:
                    revised_forecast["confidence"] = critique["suggested_confidence"]
                
                # Add critique notes
                revised_forecast["critique_notes"] = critique.get("critique_summary", "")
                
                revised.append(revised_forecast)
            else:
                # Accept forecast as-is
                forecast["critique_notes"] = "Accepted by critic"
                revised.append(forecast)
        
        return revised
