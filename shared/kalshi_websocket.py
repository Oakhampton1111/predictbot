"""
PredictBot - Kalshi WebSocket Client
====================================

Real-time WebSocket client for Kalshi market data streaming.

Features:
- Real-time orderbook updates
- Trade stream
- Market status updates
- Automatic reconnection with exponential backoff
- Event publishing to Redis for other services

Kalshi WebSocket API Documentation:
https://trading-api.readme.io/reference/websocket-api
"""

import os
import json
import asyncio
import hashlib
import hmac
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp

try:
    from .logging_config import get_logger
    from .metrics import get_metrics_registry
    from .event_bus import EventBus
except ImportError:
    import logging
    def get_logger(name: str, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_metrics_registry():
        return None
    
    EventBus = None


class KalshiMessageType(str, Enum):
    """Kalshi WebSocket message types."""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ORDERBOOK_SNAPSHOT = "orderbook_snapshot"
    ORDERBOOK_DELTA = "orderbook_delta"
    TRADE = "trade"
    TICKER = "ticker"
    MARKET_STATUS = "market_status"
    ERROR = "error"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"


class KalshiChannel(str, Enum):
    """Kalshi WebSocket subscription channels."""
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    TICKER = "ticker"
    MARKET_STATUS = "market_status"


@dataclass
class KalshiOrderbook:
    """Kalshi orderbook state."""
    market_ticker: str
    yes_bids: List[Dict[str, Any]] = field(default_factory=list)  # [{price, quantity}]
    yes_asks: List[Dict[str, Any]] = field(default_factory=list)
    no_bids: List[Dict[str, Any]] = field(default_factory=list)
    no_asks: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    
    @property
    def best_yes_bid(self) -> Optional[float]:
        """Get best yes bid price."""
        if self.yes_bids:
            return max(b["price"] for b in self.yes_bids) / 100  # Convert cents to dollars
        return None
    
    @property
    def best_yes_ask(self) -> Optional[float]:
        """Get best yes ask price."""
        if self.yes_asks:
            return min(a["price"] for a in self.yes_asks) / 100
        return None
    
    @property
    def spread(self) -> Optional[float]:
        """Get bid-ask spread."""
        if self.best_yes_bid and self.best_yes_ask:
            return self.best_yes_ask - self.best_yes_bid
        return None


@dataclass
class KalshiTrade:
    """Kalshi trade event."""
    market_ticker: str
    trade_id: str
    price: float  # In dollars (0-1)
    count: int
    side: str  # "yes" or "no"
    taker_side: str  # "buy" or "sell"
    timestamp: datetime


class KalshiWebSocketClient:
    """
    Kalshi WebSocket client for real-time market data.
    
    Usage:
        client = KalshiWebSocketClient(api_key, api_secret)
        
        @client.on_orderbook
        async def handle_orderbook(orderbook: KalshiOrderbook):
            print(f"Orderbook update: {orderbook.market_ticker}")
        
        @client.on_trade
        async def handle_trade(trade: KalshiTrade):
            print(f"Trade: {trade.market_ticker} @ {trade.price}")
        
        await client.connect()
        await client.subscribe_orderbook(["MARKET-TICKER-1", "MARKET-TICKER-2"])
        await client.run_forever()
    """
    
    # Kalshi WebSocket endpoints
    WS_URL_PROD = "wss://trading-api.kalshi.com/trade-api/ws/v2"
    WS_URL_DEMO = "wss://demo-api.kalshi.co/trade-api/ws/v2"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        demo_mode: bool = False,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 10,
        reconnect_delay: float = 1.0,
        event_bus: Optional[Any] = None,
    ):
        """
        Initialize Kalshi WebSocket client.
        
        Args:
            api_key: Kalshi API key
            api_secret: Kalshi API secret
            demo_mode: Use demo API endpoint
            auto_reconnect: Automatically reconnect on disconnect
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_delay: Initial delay between reconnection attempts
            event_bus: Optional EventBus for publishing events
        """
        self.logger = get_logger("kalshi.websocket")
        self.metrics = get_metrics_registry()
        
        self.api_key = api_key or os.environ.get("KALSHI_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("KALSHI_API_SECRET", "")
        self.demo_mode = demo_mode
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.event_bus = event_bus
        
        self.ws_url = self.WS_URL_DEMO if demo_mode else self.WS_URL_PROD
        
        # Connection state
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._reconnect_count = 0
        self._running = False
        
        # Subscriptions
        self._subscribed_markets: Set[str] = set()
        self._subscribed_channels: Dict[str, Set[str]] = {
            KalshiChannel.ORDERBOOK: set(),
            KalshiChannel.TRADES: set(),
            KalshiChannel.TICKER: set(),
        }
        
        # Orderbook state
        self._orderbooks: Dict[str, KalshiOrderbook] = {}
        
        # Event handlers
        self._orderbook_handlers: List[Callable] = []
        self._trade_handlers: List[Callable] = []
        self._ticker_handlers: List[Callable] = []
        self._error_handlers: List[Callable] = []
        
        self.logger.info(f"Kalshi WebSocket client initialized (demo={demo_mode})")
    
    def _generate_auth_signature(self, timestamp: int) -> str:
        """Generate HMAC signature for authentication."""
        message = f"{timestamp}GET/trade-api/ws/v2"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def connect(self) -> bool:
        """
        Connect to Kalshi WebSocket.
        
        Returns:
            True if connected successfully
        """
        if self._connected:
            self.logger.warning("Already connected")
            return True
        
        try:
            self._session = aiohttp.ClientSession()
            
            # Generate authentication headers
            timestamp = int(time.time() * 1000)
            signature = self._generate_auth_signature(timestamp)
            
            headers = {
                "KALSHI-ACCESS-KEY": self.api_key,
                "KALSHI-ACCESS-SIGNATURE": signature,
                "KALSHI-ACCESS-TIMESTAMP": str(timestamp),
            }
            
            self._ws = await self._session.ws_connect(
                self.ws_url,
                headers=headers,
                heartbeat=30,
            )
            
            self._connected = True
            self._reconnect_count = 0
            
            self.logger.info(f"Connected to Kalshi WebSocket: {self.ws_url}")
            
            # Resubscribe to previous subscriptions
            await self._resubscribe()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Kalshi WebSocket: {e}")
            await self._cleanup()
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Kalshi WebSocket."""
        self._running = False
        await self._cleanup()
        self.logger.info("Disconnected from Kalshi WebSocket")
    
    async def _cleanup(self) -> None:
        """Clean up connection resources."""
        self._connected = False
        
        if self._ws and not self._ws.closed:
            await self._ws.close()
        self._ws = None
        
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
    
    async def _reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff."""
        if not self.auto_reconnect:
            return False
        
        while self._reconnect_count < self.max_reconnect_attempts:
            self._reconnect_count += 1
            delay = self.reconnect_delay * (2 ** (self._reconnect_count - 1))
            
            self.logger.info(
                f"Reconnecting in {delay}s (attempt {self._reconnect_count}/{self.max_reconnect_attempts})"
            )
            
            await asyncio.sleep(delay)
            
            if await self.connect():
                return True
        
        self.logger.error("Max reconnection attempts reached")
        return False
    
    async def _resubscribe(self) -> None:
        """Resubscribe to all previous subscriptions after reconnect."""
        for channel, markets in self._subscribed_channels.items():
            if markets:
                await self._send_subscribe(channel, list(markets))
    
    async def _send(self, message: Dict[str, Any]) -> None:
        """Send a message to the WebSocket."""
        if not self._ws or self._ws.closed:
            raise RuntimeError("WebSocket not connected")
        
        await self._ws.send_json(message)
        self.logger.debug(f"Sent: {message}")
    
    async def _send_subscribe(self, channel: str, markets: List[str]) -> None:
        """Send subscription message."""
        message = {
            "id": int(time.time() * 1000),
            "cmd": KalshiMessageType.SUBSCRIBE,
            "params": {
                "channels": [channel],
                "market_tickers": markets,
            }
        }
        await self._send(message)
    
    async def _send_unsubscribe(self, channel: str, markets: List[str]) -> None:
        """Send unsubscription message."""
        message = {
            "id": int(time.time() * 1000),
            "cmd": KalshiMessageType.UNSUBSCRIBE,
            "params": {
                "channels": [channel],
                "market_tickers": markets,
            }
        }
        await self._send(message)
    
    # Subscription methods
    
    async def subscribe_orderbook(self, markets: List[str]) -> None:
        """
        Subscribe to orderbook updates for markets.
        
        Args:
            markets: List of market tickers
        """
        new_markets = [m for m in markets if m not in self._subscribed_channels[KalshiChannel.ORDERBOOK]]
        if new_markets:
            await self._send_subscribe(KalshiChannel.ORDERBOOK, new_markets)
            self._subscribed_channels[KalshiChannel.ORDERBOOK].update(new_markets)
            self.logger.info(f"Subscribed to orderbook: {new_markets}")
    
    async def subscribe_trades(self, markets: List[str]) -> None:
        """Subscribe to trade stream for markets."""
        new_markets = [m for m in markets if m not in self._subscribed_channels[KalshiChannel.TRADES]]
        if new_markets:
            await self._send_subscribe(KalshiChannel.TRADES, new_markets)
            self._subscribed_channels[KalshiChannel.TRADES].update(new_markets)
            self.logger.info(f"Subscribed to trades: {new_markets}")
    
    async def subscribe_ticker(self, markets: List[str]) -> None:
        """Subscribe to ticker updates for markets."""
        new_markets = [m for m in markets if m not in self._subscribed_channels[KalshiChannel.TICKER]]
        if new_markets:
            await self._send_subscribe(KalshiChannel.TICKER, new_markets)
            self._subscribed_channels[KalshiChannel.TICKER].update(new_markets)
            self.logger.info(f"Subscribed to ticker: {new_markets}")
    
    async def unsubscribe_orderbook(self, markets: List[str]) -> None:
        """Unsubscribe from orderbook updates."""
        existing = [m for m in markets if m in self._subscribed_channels[KalshiChannel.ORDERBOOK]]
        if existing:
            await self._send_unsubscribe(KalshiChannel.ORDERBOOK, existing)
            self._subscribed_channels[KalshiChannel.ORDERBOOK].difference_update(existing)
    
    # Event handler decorators
    
    def on_orderbook(self, handler: Callable) -> Callable:
        """Decorator to register orderbook update handler."""
        self._orderbook_handlers.append(handler)
        return handler
    
    def on_trade(self, handler: Callable) -> Callable:
        """Decorator to register trade handler."""
        self._trade_handlers.append(handler)
        return handler
    
    def on_ticker(self, handler: Callable) -> Callable:
        """Decorator to register ticker handler."""
        self._ticker_handlers.append(handler)
        return handler
    
    def on_error(self, handler: Callable) -> Callable:
        """Decorator to register error handler."""
        self._error_handlers.append(handler)
        return handler
    
    # Message processing
    
    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process incoming WebSocket message."""
        msg_type = data.get("type")
        
        if msg_type == KalshiMessageType.ORDERBOOK_SNAPSHOT:
            await self._handle_orderbook_snapshot(data)
        elif msg_type == KalshiMessageType.ORDERBOOK_DELTA:
            await self._handle_orderbook_delta(data)
        elif msg_type == KalshiMessageType.TRADE:
            await self._handle_trade(data)
        elif msg_type == KalshiMessageType.TICKER:
            await self._handle_ticker(data)
        elif msg_type == KalshiMessageType.ERROR:
            await self._handle_error(data)
        elif msg_type == KalshiMessageType.SUBSCRIBED:
            self.logger.debug(f"Subscription confirmed: {data}")
        elif msg_type == KalshiMessageType.UNSUBSCRIBED:
            self.logger.debug(f"Unsubscription confirmed: {data}")
        else:
            self.logger.debug(f"Unknown message type: {msg_type}")
    
    async def _handle_orderbook_snapshot(self, data: Dict[str, Any]) -> None:
        """Handle orderbook snapshot message."""
        msg = data.get("msg", {})
        market_ticker = msg.get("market_ticker")
        
        if not market_ticker:
            return
        
        orderbook = KalshiOrderbook(
            market_ticker=market_ticker,
            yes_bids=msg.get("yes", {}).get("bids", []),
            yes_asks=msg.get("yes", {}).get("asks", []),
            no_bids=msg.get("no", {}).get("bids", []),
            no_asks=msg.get("no", {}).get("asks", []),
            timestamp=datetime.utcnow(),
        )
        
        self._orderbooks[market_ticker] = orderbook
        
        # Call handlers
        for handler in self._orderbook_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(orderbook)
                else:
                    handler(orderbook)
            except Exception as e:
                self.logger.error(f"Orderbook handler error: {e}")
        
        # Publish to event bus
        if self.event_bus:
            await self.event_bus.publish("kalshi.orderbook", {
                "market_ticker": market_ticker,
                "best_yes_bid": orderbook.best_yes_bid,
                "best_yes_ask": orderbook.best_yes_ask,
                "spread": orderbook.spread,
                "timestamp": orderbook.timestamp.isoformat(),
            })
    
    async def _handle_orderbook_delta(self, data: Dict[str, Any]) -> None:
        """Handle orderbook delta (incremental update) message."""
        msg = data.get("msg", {})
        market_ticker = msg.get("market_ticker")
        
        if not market_ticker or market_ticker not in self._orderbooks:
            return
        
        orderbook = self._orderbooks[market_ticker]
        
        # Apply delta updates
        # This is a simplified implementation - full implementation would
        # need to handle price level updates properly
        if "yes" in msg:
            if "bids" in msg["yes"]:
                orderbook.yes_bids = msg["yes"]["bids"]
            if "asks" in msg["yes"]:
                orderbook.yes_asks = msg["yes"]["asks"]
        
        if "no" in msg:
            if "bids" in msg["no"]:
                orderbook.no_bids = msg["no"]["bids"]
            if "asks" in msg["no"]:
                orderbook.no_asks = msg["no"]["asks"]
        
        orderbook.timestamp = datetime.utcnow()
        
        # Call handlers
        for handler in self._orderbook_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(orderbook)
                else:
                    handler(orderbook)
            except Exception as e:
                self.logger.error(f"Orderbook handler error: {e}")
    
    async def _handle_trade(self, data: Dict[str, Any]) -> None:
        """Handle trade message."""
        msg = data.get("msg", {})
        
        trade = KalshiTrade(
            market_ticker=msg.get("market_ticker", ""),
            trade_id=msg.get("trade_id", ""),
            price=msg.get("yes_price", 0) / 100,  # Convert cents to dollars
            count=msg.get("count", 0),
            side="yes" if msg.get("yes_price") else "no",
            taker_side=msg.get("taker_side", ""),
            timestamp=datetime.utcnow(),
        )
        
        # Call handlers
        for handler in self._trade_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(trade)
                else:
                    handler(trade)
            except Exception as e:
                self.logger.error(f"Trade handler error: {e}")
        
        # Publish to event bus
        if self.event_bus:
            await self.event_bus.publish("kalshi.trade", {
                "market_ticker": trade.market_ticker,
                "trade_id": trade.trade_id,
                "price": trade.price,
                "count": trade.count,
                "side": trade.side,
                "taker_side": trade.taker_side,
                "timestamp": trade.timestamp.isoformat(),
            })
        
        # Record metrics
        if self.metrics:
            self.metrics.record_trade(
                platform="kalshi",
                market=trade.market_ticker,
                side=trade.side,
                price=trade.price,
                size=trade.count,
            )
    
    async def _handle_ticker(self, data: Dict[str, Any]) -> None:
        """Handle ticker message."""
        msg = data.get("msg", {})
        
        # Call handlers
        for handler in self._ticker_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(msg)
                else:
                    handler(msg)
            except Exception as e:
                self.logger.error(f"Ticker handler error: {e}")
    
    async def _handle_error(self, data: Dict[str, Any]) -> None:
        """Handle error message."""
        error_msg = data.get("msg", {}).get("error", "Unknown error")
        self.logger.error(f"Kalshi WebSocket error: {error_msg}")
        
        # Call handlers
        for handler in self._error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_msg)
                else:
                    handler(error_msg)
            except Exception as e:
                self.logger.error(f"Error handler error: {e}")
    
    # Main loop
    
    async def run_forever(self) -> None:
        """
        Run the WebSocket client forever, handling reconnections.
        
        This method blocks until disconnect() is called or max reconnection
        attempts are exceeded.
        """
        self._running = True
        
        while self._running:
            if not self._connected:
                if not await self.connect():
                    if not await self._reconnect():
                        break
                    continue
            
            try:
                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            await self._process_message(data)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse message: {e}")
                    
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self.logger.error(f"WebSocket error: {self._ws.exception()}")
                        break
                    
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        self.logger.warning("WebSocket closed by server")
                        break
                
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
            
            # Connection lost
            self._connected = False
            
            if self._running and self.auto_reconnect:
                if not await self._reconnect():
                    break
            else:
                break
        
        await self._cleanup()
    
    # Utility methods
    
    def get_orderbook(self, market_ticker: str) -> Optional[KalshiOrderbook]:
        """Get cached orderbook for a market."""
        return self._orderbooks.get(market_ticker)
    
    def get_all_orderbooks(self) -> Dict[str, KalshiOrderbook]:
        """Get all cached orderbooks."""
        return self._orderbooks.copy()
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected
    
    @property
    def subscribed_markets(self) -> Set[str]:
        """Get all subscribed markets across all channels."""
        all_markets = set()
        for markets in self._subscribed_channels.values():
            all_markets.update(markets)
        return all_markets


# Convenience function to create client from environment
def create_kalshi_websocket_client(
    event_bus: Optional[Any] = None,
    demo_mode: Optional[bool] = None,
) -> KalshiWebSocketClient:
    """
    Create a Kalshi WebSocket client from environment variables.
    
    Args:
        event_bus: Optional EventBus for publishing events
        demo_mode: Override demo mode (default: from DRY_RUN env var)
        
    Returns:
        Configured KalshiWebSocketClient
    """
    if demo_mode is None:
        demo_mode = os.environ.get("DRY_RUN", "1") == "1"
    
    return KalshiWebSocketClient(
        api_key=os.environ.get("KALSHI_API_KEY"),
        api_secret=os.environ.get("KALSHI_API_SECRET"),
        demo_mode=demo_mode,
        event_bus=event_bus,
    )
