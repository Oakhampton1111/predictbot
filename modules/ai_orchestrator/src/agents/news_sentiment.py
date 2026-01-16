"""
PredictBot AI Orchestrator - News Sentiment Agent
==================================================

This agent processes news feeds and social media to extract sentiment
and predict event impacts on prediction markets.

Responsibilities:
- Aggregate news from multiple sources
- Analyze sentiment (bullish/bearish/neutral)
- Detect breaking news and events
- Predict impact on market prices
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .base import BaseAgent, AgentError


# System prompt for news sentiment analysis
NEWS_SENTIMENT_SYSTEM_PROMPT = """You are an expert news analyst specializing in prediction markets and event-driven trading.

Your role is to analyze news and social media content to determine sentiment and predict market impacts.

ANALYSIS FRAMEWORK:

1. SENTIMENT CLASSIFICATION:
   - Strongly Bullish: Clear positive news likely to increase YES price
   - Bullish: Moderately positive news
   - Neutral: No clear directional impact
   - Bearish: Moderately negative news
   - Strongly Bearish: Clear negative news likely to decrease YES price

2. EVENT IMPACT ASSESSMENT:
   - Immediate impact (within hours)
   - Short-term impact (1-3 days)
   - Long-term impact (weeks)

3. SOURCE CREDIBILITY:
   - Official sources (government, companies)
   - Major news outlets
   - Social media / rumors
   - Expert opinions

4. MARKET RELEVANCE:
   - Direct relevance to market question
   - Indirect/tangential relevance
   - No relevance

Always consider:
- Confirmation bias in sources
- Market efficiency (news may already be priced in)
- Potential for reversal or correction
- Time sensitivity of information

Provide structured JSON output with clear reasoning."""


class NewsSentimentAgent(BaseAgent):
    """
    News Sentiment Agent - Processes news and social sentiment.
    
    This agent analyzes news feeds and social media to extract
    sentiment signals that may impact prediction market prices.
    
    Uses: Groq for speed on high-volume news, GPT-4 for nuanced analysis
    """
    
    def __init__(self, llm_router: Any, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="news_sentiment",
            llm_router=llm_router,
            timeout=120.0,
            config=config
        )
        
        # Configuration
        self.max_news_items = config.get("max_news_items", 50) if config else 50
        self.sentiment_threshold = config.get("sentiment_threshold", 0.3) if config else 0.3
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze news sentiment for selected markets.
        
        Args:
            state: Current TradingState
            
        Returns:
            Updated TradingState with news_sentiment analysis
        """
        selected_markets = state.get("selected_markets", [])
        opportunities = state.get("opportunities", [])
        
        if not selected_markets:
            self.logger.warning("No markets selected for sentiment analysis")
            state["news_sentiment"] = {"status": "no_markets_selected"}
            return state
        
        # Get market details for selected markets
        market_details = {
            m["market_id"]: m
            for m in opportunities
            if m.get("market_id") in selected_markets
        }
        
        self.logger.info(f"Analyzing news sentiment for {len(selected_markets)} markets")
        
        # Fetch news for markets (simulated - would integrate with news APIs)
        news_data = await self._fetch_news_for_markets(market_details)
        
        # Analyze sentiment for each market
        sentiment_results = await self._analyze_sentiment(market_details, news_data)
        
        # Aggregate and score sentiment
        aggregated_sentiment = self._aggregate_sentiment(sentiment_results)
        
        # Update state
        state["news_sentiment"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "markets_analyzed": len(selected_markets),
            "news_items_processed": sum(len(n) for n in news_data.values()),
            "results": sentiment_results,
            "aggregated": aggregated_sentiment
        }
        state["current_step"] = "news_sentiment"
        
        # Log significant sentiment signals
        for market_id, sentiment in aggregated_sentiment.items():
            if abs(sentiment.get("sentiment_score", 0)) >= self.sentiment_threshold:
                self.log_decision(
                    decision_type="sentiment_signal",
                    details={
                        "market_id": market_id,
                        "sentiment_score": sentiment.get("sentiment_score"),
                        "direction": sentiment.get("direction"),
                        "confidence": sentiment.get("confidence")
                    },
                    confidence=sentiment.get("confidence")
                )
        
        return state
    
    async def _fetch_news_for_markets(
        self,
        market_details: Dict[str, Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Fetch relevant news for each market.
        
        In production, this would integrate with:
        - News APIs (NewsAPI, GDELT, etc.)
        - Social media APIs (Twitter/X, Reddit)
        - RSS feeds
        - Polyseer research service
        
        Args:
            market_details: Dictionary of market details
            
        Returns:
            Dictionary mapping market_id to list of news items
        """
        news_data = {}
        
        for market_id, details in market_details.items():
            # Placeholder - would fetch real news
            # For now, return empty list (real implementation would call APIs)
            news_data[market_id] = []
            
            # In production:
            # news_data[market_id] = await self._call_news_api(details["question"])
        
        return news_data
    
    async def _analyze_sentiment(
        self,
        market_details: Dict[str, Dict],
        news_data: Dict[str, List[Dict]]
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for markets using LLM.
        
        Args:
            market_details: Market information
            news_data: News items per market
            
        Returns:
            Sentiment analysis results
        """
        results = {}
        
        for market_id, details in market_details.items():
            news_items = news_data.get(market_id, [])
            
            # Build analysis prompt
            prompt = self._build_sentiment_prompt(details, news_items)
            
            try:
                # Use Groq for speed when processing many items
                task_type = "fast" if len(news_items) > 10 else "reasoning"
                
                response = await self.call_llm(
                    prompt=prompt,
                    task_type=task_type,
                    system_prompt=NEWS_SENTIMENT_SYSTEM_PROMPT,
                    temperature=0.3,
                    max_tokens=1500
                )
                
                results[market_id] = self.parse_json_response(response)
                
            except Exception as e:
                self.logger.error(f"Sentiment analysis failed for {market_id}: {e}")
                results[market_id] = self._default_sentiment()
        
        return results
    
    def _build_sentiment_prompt(
        self,
        market_details: Dict,
        news_items: List[Dict]
    ) -> str:
        """Build the sentiment analysis prompt."""
        
        market_info = f"""
MARKET INFORMATION:
- Question: {market_details.get('question', 'Unknown')}
- Current Price: {market_details.get('current_price', 0.5)}
- Platform: {market_details.get('platform', 'Unknown')}
- End Date: {market_details.get('end_date', 'Unknown')}
"""
        
        if news_items:
            news_text = "\n".join([
                f"- [{item.get('source', 'Unknown')}] {item.get('title', '')}: {item.get('summary', '')[:200]}"
                for item in news_items[:20]  # Limit to 20 items
            ])
            news_section = f"\nRECENT NEWS:\n{news_text}"
        else:
            news_section = "\nRECENT NEWS: No recent news available for this market."
        
        return f"""{market_info}
{news_section}

Analyze the sentiment and potential market impact. Provide your analysis as JSON with:
{{
    "sentiment_direction": "bullish" | "bearish" | "neutral",
    "sentiment_score": -1.0 to 1.0 (negative = bearish, positive = bullish),
    "confidence": 0.0 to 1.0,
    "key_events": ["list of relevant events"],
    "impact_timeline": "immediate" | "short_term" | "long_term",
    "price_impact_estimate": -0.2 to 0.2 (expected price change),
    "reasoning": "brief explanation"
}}"""
    
    def _default_sentiment(self) -> Dict[str, Any]:
        """Return default neutral sentiment when analysis fails."""
        return {
            "sentiment_direction": "neutral",
            "sentiment_score": 0.0,
            "confidence": 0.3,
            "key_events": [],
            "impact_timeline": "long_term",
            "price_impact_estimate": 0.0,
            "reasoning": "Unable to determine sentiment - defaulting to neutral"
        }
    
    def _aggregate_sentiment(
        self,
        sentiment_results: Dict[str, Any]
    ) -> Dict[str, Dict]:
        """
        Aggregate and normalize sentiment results.
        
        Args:
            sentiment_results: Raw sentiment analysis results
            
        Returns:
            Aggregated sentiment per market
        """
        aggregated = {}
        
        for market_id, result in sentiment_results.items():
            if not isinstance(result, dict):
                aggregated[market_id] = self._default_sentiment()
                continue
            
            # Normalize and validate scores
            sentiment_score = max(-1.0, min(1.0, result.get("sentiment_score", 0.0)))
            confidence = max(0.0, min(1.0, result.get("confidence", 0.5)))
            
            # Determine direction based on score
            if sentiment_score > 0.2:
                direction = "bullish"
            elif sentiment_score < -0.2:
                direction = "bearish"
            else:
                direction = "neutral"
            
            aggregated[market_id] = {
                "sentiment_score": sentiment_score,
                "direction": direction,
                "confidence": confidence,
                "impact_estimate": result.get("price_impact_estimate", 0.0),
                "timeline": result.get("impact_timeline", "long_term"),
                "key_events": result.get("key_events", []),
                "reasoning": result.get("reasoning", "")
            }
        
        return aggregated
