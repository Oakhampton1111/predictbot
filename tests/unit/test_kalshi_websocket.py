"""
Unit Tests - Kalshi WebSocket
=============================

Tests for the Kalshi WebSocket streaming client.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.kalshi_websocket import (
    KalshiWebSocketClient,
    KalshiOrderbook,
    KalshiTrade,
    KalshiMessageType,
    KalshiChannel,
    create_kalshi_websocket_client,
)


class TestKalshiMessageType:
    """Tests for KalshiMessageType enum."""
    
    def test_message_types(self):
        """Test all message types exist."""
        assert KalshiMessageType.SUBSCRIBE == "subscribe"
        assert KalshiMessageType.UNSUBSCRIBE == "unsubscribe"
        assert KalshiMessageType.ORDERBOOK_SNAPSHOT == "orderbook_snapshot"
        assert KalshiMessageType.ORDERBOOK_DELTA == "orderbook_delta"
        assert KalshiMessageType.TRADE == "trade"
        assert KalshiMessageType.TICKER == "ticker"
        assert KalshiMessageType.ERROR == "error"


class TestKalshiChannel:
    """Tests for KalshiChannel enum."""
    
    def test_channel_types(self):
        """Test all channel types exist."""
        assert KalshiChannel.ORDERBOOK == "orderbook"
        assert KalshiChannel.TRADES == "trades"
        assert KalshiChannel.TICKER == "ticker"
        assert KalshiChannel.MARKET_STATUS == "market_status"


class TestKalshiOrderbook:
    """Tests for KalshiOrderbook dataclass."""
    
    def test_create_orderbook(self):
        """Test creating an orderbook."""
        orderbook = KalshiOrderbook(
            market_ticker="PRES-2024",
            yes_bids=[{"price": 50, "quantity": 100}, {"price": 49, "quantity": 200}],
            yes_asks=[{"price": 52, "quantity": 150}, {"price": 53, "quantity": 250}],
            timestamp=datetime.utcnow(),
        )
        
        assert orderbook.market_ticker == "PRES-2024"
        assert len(orderbook.yes_bids) == 2
        assert len(orderbook.yes_asks) == 2
    
    def test_best_yes_bid(self):
        """Test getting best yes bid."""
        orderbook = KalshiOrderbook(
            market_ticker="PRES-2024",
            yes_bids=[{"price": 50, "quantity": 100}, {"price": 49, "quantity": 200}],
            yes_asks=[{"price": 52, "quantity": 150}],
        )
        
        assert orderbook.best_yes_bid == 0.50  # 50 cents = $0.50
    
    def test_best_yes_ask(self):
        """Test getting best yes ask."""
        orderbook = KalshiOrderbook(
            market_ticker="PRES-2024",
            yes_bids=[{"price": 50, "quantity": 100}],
            yes_asks=[{"price": 52, "quantity": 150}, {"price": 53, "quantity": 250}],
        )
        
        assert orderbook.best_yes_ask == 0.52  # 52 cents = $0.52
    
    def test_spread(self):
        """Test calculating spread."""
        orderbook = KalshiOrderbook(
            market_ticker="PRES-2024",
            yes_bids=[{"price": 50, "quantity": 100}],
            yes_asks=[{"price": 52, "quantity": 150}],
        )
        
        assert orderbook.spread == pytest.approx(0.02, rel=0.01)
    
    def test_empty_orderbook(self):
        """Test empty orderbook handling."""
        orderbook = KalshiOrderbook(
            market_ticker="PRES-2024",
            yes_bids=[],
            yes_asks=[],
        )
        
        assert orderbook.best_yes_bid is None
        assert orderbook.best_yes_ask is None
        assert orderbook.spread is None


class TestKalshiTrade:
    """Tests for KalshiTrade dataclass."""
    
    def test_create_trade(self):
        """Test creating a trade."""
        trade = KalshiTrade(
            market_ticker="PRES-2024",
            trade_id="trade-123",
            price=0.55,
            count=100,
            side="yes",
            taker_side="buy",
            timestamp=datetime.utcnow(),
        )
        
        assert trade.market_ticker == "PRES-2024"
        assert trade.trade_id == "trade-123"
        assert trade.price == 0.55
        assert trade.count == 100
        assert trade.side == "yes"


class TestKalshiWebSocketClient:
    """Tests for KalshiWebSocketClient class."""
    
    @pytest.fixture
    def ws_client(self):
        """Create a WebSocket client for testing."""
        client = KalshiWebSocketClient(
            api_key="test-api-key",
            api_secret="test-api-secret",
            demo_mode=True,
        )
        return client
    
    def test_init(self, ws_client):
        """Test client initialization."""
        assert ws_client.api_key == "test-api-key"
        assert ws_client.demo_mode is True
        assert ws_client.is_connected is False
    
    def test_ws_url_demo(self, ws_client):
        """Test demo WebSocket URL."""
        assert "demo" in ws_client.ws_url
    
    def test_ws_url_prod(self):
        """Test production WebSocket URL."""
        client = KalshiWebSocketClient(
            api_key="test",
            api_secret="test",
            demo_mode=False,
        )
        assert "demo" not in client.ws_url
    
    def test_generate_auth_signature(self, ws_client):
        """Test auth signature generation."""
        timestamp = 1234567890000
        signature = ws_client._generate_auth_signature(timestamp)
        
        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest
    
    def test_on_orderbook_decorator(self, ws_client):
        """Test orderbook handler decorator."""
        @ws_client.on_orderbook
        async def handler(orderbook):
            pass
        
        assert handler in ws_client._orderbook_handlers
    
    def test_on_trade_decorator(self, ws_client):
        """Test trade handler decorator."""
        @ws_client.on_trade
        async def handler(trade):
            pass
        
        assert handler in ws_client._trade_handlers
    
    def test_on_error_decorator(self, ws_client):
        """Test error handler decorator."""
        @ws_client.on_error
        async def handler(error):
            pass
        
        assert handler in ws_client._error_handlers
    
    def test_get_orderbook(self, ws_client):
        """Test getting cached orderbook."""
        # Add orderbook to cache
        ws_client._orderbooks["PRES-2024"] = KalshiOrderbook(
            market_ticker="PRES-2024",
            yes_bids=[{"price": 50, "quantity": 100}],
            yes_asks=[{"price": 52, "quantity": 150}],
        )
        
        orderbook = ws_client.get_orderbook("PRES-2024")
        
        assert orderbook is not None
        assert orderbook.market_ticker == "PRES-2024"
    
    def test_get_orderbook_not_found(self, ws_client):
        """Test getting non-existent orderbook."""
        orderbook = ws_client.get_orderbook("NONEXISTENT")
        assert orderbook is None
    
    def test_subscribed_markets(self, ws_client):
        """Test subscribed markets property."""
        ws_client._subscribed_channels[KalshiChannel.ORDERBOOK].add("PRES-2024")
        ws_client._subscribed_channels[KalshiChannel.TRADES].add("ECON-2024")
        
        markets = ws_client.subscribed_markets
        
        assert "PRES-2024" in markets
        assert "ECON-2024" in markets


class TestCreateKalshiWebSocketClient:
    """Tests for factory function."""
    
    def test_create_from_environment(self):
        """Test creating WebSocket client from environment."""
        with patch.dict(os.environ, {
            "KALSHI_API_KEY": "test-key",
            "KALSHI_API_SECRET": "test-secret",
            "DRY_RUN": "1",
        }):
            client = create_kalshi_websocket_client()
            
            assert client is not None
            assert isinstance(client, KalshiWebSocketClient)
            assert client.demo_mode is True
    
    def test_create_production_mode(self):
        """Test creating client in production mode."""
        with patch.dict(os.environ, {
            "KALSHI_API_KEY": "test-key",
            "KALSHI_API_SECRET": "test-secret",
            "DRY_RUN": "0",
        }):
            client = create_kalshi_websocket_client()
            
            assert client.demo_mode is False
    
    def test_create_with_override(self):
        """Test creating client with demo mode override."""
        client = create_kalshi_websocket_client(demo_mode=True)
        
        assert client.demo_mode is True
