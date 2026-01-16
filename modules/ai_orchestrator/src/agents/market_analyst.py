"""
PredictBot AI Orchestrator - Market Analyst Agent
==================================================

This agent analyzes market structure, liquidity, and trends to identify
high-quality trading opportunities.

Responsibilities:
- Evaluate market liquidity and depth
- Detect price trends and patterns
- Score market quality for trading
- Filter opportunities based on criteria
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .base import BaseAgent, AgentError


# System prompt for market analysis
MARKET_ANALYST_SYSTEM_PROMPT = """You are an expert prediction market analyst specializing in market microstructure analysis.

Your role is to analyze prediction markets and evaluate their quality for trading. Consider:

1. LIQUIDITY ANALYSIS:
   - Order book depth
   - Bid-ask spread
   - 24h trading volume
   - Historical volume patterns

2. MARKET QUALITY:
   - Price stability
   - Number of active traders
   - Time to resolution
   - Information efficiency

3. TREND DETECTION:
   - Recent price movements
   - Volume spikes
   - News-driven changes
   - Mean reversion potential

4. RISK FACTORS:
   - Low liquidity risk
   - Resolution uncertainty
   - Platform-specific risks
   - Manipulation indicators

Provide your analysis in structured JSON format with clear reasoning."""


class MarketAnalystAgent(BaseAgent):
    """
    Market Analyst Agent - Analyzes market structure and quality.
    
    This agent is the first step in the trading pipeline. It receives
    raw market opportunities and evaluates them for trading suitability.
    
    Uses: Ollama for routine analysis, GPT-4 for complex markets
    """
    
    def __init__(self, llm_router: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="market_analyst",
            llm_router=llm_router,
            timeout=90.0,
            config=config
        )
        
        # Configuration
        self.min_liquidity_score = config.get("min_liquidity_score", 0.3) if config else 0.3
        self.min_volume_24h = config.get("min_volume_24h", 1000) if config else 1000
        self.max_markets_to_analyze = config.get("max_markets", 20) if config else 20
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market opportunities and update state with analysis results.
        
        Args:
            state: Current TradingState
            
        Returns:
            Updated TradingState with market_analysis and selected_markets
        """
        opportunities = state.get("opportunities", [])
        
        if not opportunities:
            self.logger.warning("No market opportunities to analyze")
            state["market_analysis"] = {"status": "no_opportunities"}
            state["selected_markets"] = []
            return state
        
        self.logger.info(f"Analyzing {len(opportunities)} market opportunities")
        
        # Pre-filter markets based on basic criteria
        filtered_markets = self._pre_filter_markets(opportunities)
        self.logger.info(f"Pre-filtered to {len(filtered_markets)} markets")
        
        # Limit number of markets for detailed analysis
        markets_to_analyze = filtered_markets[:self.max_markets_to_analyze]
        
        # Perform detailed analysis
        analysis_results = await self._analyze_markets(markets_to_analyze)
        
        # Score and rank markets
        scored_markets = self._score_markets(analysis_results)
        
        # Select top markets for further processing
        selected_markets = [
            m["market_id"] for m in scored_markets
            if m.get("quality_score", 0) >= 0.5
        ][:10]  # Top 10 markets
        
        # Update state
        state["market_analysis"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_opportunities": len(opportunities),
            "pre_filtered": len(filtered_markets),
            "analyzed": len(markets_to_analyze),
            "selected": len(selected_markets),
            "results": analysis_results,
            "scored_markets": scored_markets
        }
        state["selected_markets"] = selected_markets
        state["current_step"] = "market_analysis"
        
        self.log_decision(
            decision_type="market_selection",
            details={
                "total_markets": len(opportunities),
                "selected_count": len(selected_markets),
                "selected_markets": selected_markets[:5]  # Log first 5
            }
        )
        
        return state
    
    def _pre_filter_markets(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Pre-filter markets based on basic criteria.
        
        Args:
            opportunities: List of market opportunities
            
        Returns:
            Filtered list of markets
        """
        filtered = []
        
        for market in opportunities:
            # Check minimum volume
            if market.get("volume_24h", 0) < self.min_volume_24h:
                continue
            
            # Check liquidity score
            if market.get("liquidity_score", 0) < self.min_liquidity_score:
                continue
            
            # Check price is not at extremes (avoid 0.01 or 0.99 markets)
            price = market.get("current_price", 0.5)
            if price < 0.05 or price > 0.95:
                continue
            
            filtered.append(market)
        
        return filtered
    
    async def _analyze_markets(self, markets: List[Dict]) -> Dict[str, Any]:
        """
        Perform detailed LLM-based analysis on markets.
        
        Args:
            markets: List of markets to analyze
            
        Returns:
            Analysis results dictionary
        """
        if not markets:
            return {}
        
        # Prepare market data for analysis
        market_summaries = []
        for m in markets:
            summary = {
                "id": m.get("market_id"),
                "question": m.get("question", "")[:200],  # Truncate long questions
                "price": m.get("current_price"),
                "volume_24h": m.get("volume_24h"),
                "liquidity": m.get("liquidity_score"),
                "platform": m.get("platform"),
                "end_date": m.get("end_date")
            }
            market_summaries.append(summary)
        
        # Build analysis prompt
        prompt = f"""Analyze the following {len(market_summaries)} prediction markets for trading quality.

MARKETS:
{json.dumps(market_summaries, indent=2)}

For each market, provide:
1. liquidity_assessment: "high", "medium", or "low"
2. trend_direction: "bullish", "bearish", or "neutral"
3. volatility_estimate: 0.0 to 1.0
4. trading_opportunity: "strong", "moderate", "weak", or "avoid"
5. key_factors: list of important factors
6. recommended_strategy: brief strategy suggestion

Return your analysis as a JSON object with market IDs as keys."""

        try:
            # Use Ollama for routine analysis, GPT-4 for complex
            task_type = "analysis" if len(markets) <= 5 else "fast"
            
            response = await self.call_llm(
                prompt=prompt,
                task_type=task_type,
                system_prompt=MARKET_ANALYST_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=3000
            )
            
            return self.parse_json_response(response)
            
        except Exception as e:
            self.logger.error(f"Market analysis LLM call failed: {e}")
            # Return basic analysis on failure
            return {
                m.get("market_id"): {
                    "liquidity_assessment": "medium",
                    "trend_direction": "neutral",
                    "volatility_estimate": 0.5,
                    "trading_opportunity": "moderate",
                    "key_factors": ["analysis_failed"],
                    "recommended_strategy": "proceed_with_caution"
                }
                for m in markets
            }
    
    def _score_markets(self, analysis_results: Dict[str, Any]) -> List[Dict]:
        """
        Score markets based on analysis results.
        
        Args:
            analysis_results: LLM analysis results
            
        Returns:
            List of markets with quality scores, sorted by score
        """
        scored = []
        
        for market_id, analysis in analysis_results.items():
            if not isinstance(analysis, dict):
                continue
            
            # Calculate quality score
            score = 0.0
            
            # Liquidity component (0-0.3)
            liquidity = analysis.get("liquidity_assessment", "medium")
            if liquidity == "high":
                score += 0.3
            elif liquidity == "medium":
                score += 0.2
            else:
                score += 0.1
            
            # Opportunity component (0-0.4)
            opportunity = analysis.get("trading_opportunity", "moderate")
            if opportunity == "strong":
                score += 0.4
            elif opportunity == "moderate":
                score += 0.25
            elif opportunity == "weak":
                score += 0.1
            # "avoid" adds 0
            
            # Volatility component (0-0.3) - moderate volatility is best
            volatility = analysis.get("volatility_estimate", 0.5)
            if 0.2 <= volatility <= 0.6:
                score += 0.3
            elif 0.1 <= volatility <= 0.8:
                score += 0.2
            else:
                score += 0.1
            
            scored.append({
                "market_id": market_id,
                "quality_score": round(score, 3),
                "analysis": analysis
            })
        
        # Sort by quality score descending
        scored.sort(key=lambda x: x["quality_score"], reverse=True)
        
        return scored
