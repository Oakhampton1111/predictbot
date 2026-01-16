"""
PredictBot AI Orchestrator - MCP Client
========================================

Client for the Model Context Protocol (MCP) server that provides
market data and trading operations.
"""

import os
from typing import Any, Dict, List, Optional
import httpx
import asyncio


class MCPClient:
    """
    Client for the MCP (Model Context Protocol) server.
    
    The MCP server provides:
    - Market data from prediction market platforms
    - Trading operations (place orders, cancel orders)
    - Portfolio information
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the MCP client.
        
        Args:
            base_url: MCP server URL (defaults to MCP_SERVER_URL env var)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.environ.get(
            "MCP_SERVER_URL",
            "http://localhost:3000"
        )
        self.timeout = timeout
    
    async def get_markets(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get available markets from the MCP server.
        
        Args:
            platform: Filter by platform (polymarket, kalshi, etc.)
            category: Filter by category
            limit: Maximum number of markets to return
            
        Returns:
            List of market dictionaries
        """
        params = {"limit": limit}
        if platform:
            params["platform"] = platform
        if category:
            params["category"] = category
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/markets",
                params=params
            )
            response.raise_for_status()
            return response.json().get("markets", [])
    
    async def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific market.
        
        Args:
            market_id: Market identifier
            
        Returns:
            Market details dictionary or None
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/markets/{market_id}"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def get_orderbook(
        self,
        market_id: str,
        depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get orderbook for a market.
        
        Args:
            market_id: Market identifier
            depth: Number of price levels to return
            
        Returns:
            Orderbook with bids and asks
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/markets/{market_id}/orderbook",
                params={"depth": depth}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_portfolio(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current portfolio state.
        
        Args:
            platform: Filter by platform
            
        Returns:
            Portfolio state dictionary
        """
        params = {}
        if platform:
            params["platform"] = platform
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/portfolio",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def place_order(
        self,
        market_id: str,
        platform: str,
        side: str,
        size: float,
        price: float,
        order_type: str = "limit"
    ) -> Dict[str, Any]:
        """
        Place an order through the MCP server.
        
        Args:
            market_id: Market identifier
            platform: Trading platform
            side: Order side (buy_yes, buy_no, sell_yes, sell_no)
            size: Order size
            price: Order price
            order_type: Order type (limit, market)
            
        Returns:
            Order result dictionary
        """
        payload = {
            "market_id": market_id,
            "platform": platform,
            "side": side,
            "size": size,
            "price": price,
            "order_type": order_type
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/orders",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Cancellation result
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.base_url}/api/orders/{order_id}"
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if MCP server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
