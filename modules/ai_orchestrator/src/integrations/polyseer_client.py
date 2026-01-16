"""
PredictBot AI Orchestrator - Polyseer Client
=============================================

Client for the Polyseer research assistant that provides
information retrieval and research capabilities.
"""

import os
from typing import Any, Dict, List, Optional
import httpx
import asyncio


class PolyseerClient:
    """
    Client for the Polyseer research assistant.
    
    Polyseer provides:
    - Information retrieval from various sources
    - Research summaries for prediction markets
    - Historical data and analysis
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 60.0
    ):
        """
        Initialize the Polyseer client.
        
        Args:
            base_url: Polyseer server URL (defaults to POLYSEER_URL env var)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.environ.get(
            "POLYSEER_URL",
            "http://localhost:3001"
        )
        self.timeout = timeout
    
    async def search(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for information related to a query.
        
        Args:
            query: Search query
            sources: List of sources to search (news, academic, social, etc.)
            max_results: Maximum number of results
            
        Returns:
            Search results dictionary
        """
        payload = {
            "query": query,
            "max_results": max_results
        }
        if sources:
            payload["sources"] = sources
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/search",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def research_market(
        self,
        question: str,
        context: Optional[str] = None,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Conduct research on a prediction market question.
        
        Args:
            question: The market question to research
            context: Additional context about the market
            depth: Research depth (quick, standard, deep)
            
        Returns:
            Research results with sources and analysis
        """
        payload = {
            "question": question,
            "depth": depth
        }
        if context:
            payload["context"] = context
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/research",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def get_news(
        self,
        topic: str,
        time_range: str = "24h",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent news on a topic.
        
        Args:
            topic: Topic to search for
            time_range: Time range (1h, 24h, 7d, 30d)
            limit: Maximum number of articles
            
        Returns:
            List of news articles
        """
        params = {
            "topic": topic,
            "time_range": time_range,
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/news",
                params=params
            )
            response.raise_for_status()
            return response.json().get("articles", [])
    
    async def get_social_sentiment(
        self,
        topic: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get social media sentiment for a topic.
        
        Args:
            topic: Topic to analyze
            platforms: Platforms to include (twitter, reddit, etc.)
            
        Returns:
            Sentiment analysis results
        """
        payload = {"topic": topic}
        if platforms:
            payload["platforms"] = platforms
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/sentiment",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def get_historical_data(
        self,
        market_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical data for a market.
        
        Args:
            market_id: Market identifier
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Historical price and volume data
        """
        params = {"market_id": market_id}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/historical",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if Polyseer server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
