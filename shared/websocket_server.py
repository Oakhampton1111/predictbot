"""
WebSocket Server for PredictBot Stack

Provides real-time updates to connected clients via WebSocket.
Integrates with the event bus for broadcasting events.
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Set, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of WebSocket messages."""
    # Client -> Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    AUTHENTICATE = "authenticate"
    
    # Server -> Client
    EVENT = "event"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    PONG = "pong"
    ERROR = "error"
    AUTHENTICATED = "authenticated"
    WELCOME = "welcome"


class SubscriptionChannel(str, Enum):
    """Available subscription channels."""
    ALL = "all"
    TRADES = "trades"
    POSITIONS = "positions"
    STRATEGIES = "strategies"
    AI = "ai"
    RISK = "risk"
    ALERTS = "alerts"
    SYSTEM = "system"
    MARKET_DATA = "market_data"


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client."""
    id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.utcnow)
    authenticated: bool = False
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def can_access_channel(self, channel: str) -> bool:
        """Check if client has permission to access a channel."""
        # Admin can access everything
        if self.user_role == "admin":
            return True
        
        # Unauthenticated users can only access public channels
        if not self.authenticated:
            return channel in ["system", "market_data"]
        
        # Authenticated users can access most channels
        restricted_channels = ["system"]
        if channel in restricted_channels:
            return self.user_role in ["admin", "operator"]
        
        return True


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Supports authentication, channel subscriptions, and
    integration with the event bus.
    """
    
    def __init__(
        self,
        require_auth: bool = True,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0
    ):
        """
        Initialize the WebSocket manager.
        
        Args:
            require_auth: Whether authentication is required
            ping_interval: Interval between ping messages in seconds
            ping_timeout: Timeout for ping responses in seconds
        """
        self.require_auth = require_auth
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        self.clients: Dict[str, WebSocketClient] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
        
        # Authentication callback
        self._auth_callback: Optional[Callable] = None
        
        # Event handlers
        self._message_handlers: Dict[str, Callable] = {}
        
        # Background tasks
        self._ping_task: Optional[asyncio.Task] = None
        self._running = False
    
    def set_auth_callback(self, callback: Callable):
        """Set the authentication callback function."""
        self._auth_callback = callback
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add a handler for a specific message type."""
        self._message_handlers[message_type] = handler
    
    async def connect(self, websocket: WebSocket) -> WebSocketClient:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            WebSocketClient instance
        """
        await websocket.accept()
        
        client_id = str(uuid.uuid4())
        client = WebSocketClient(
            id=client_id,
            websocket=websocket,
            authenticated=not self.require_auth
        )
        
        self.clients[client_id] = client
        
        # Send welcome message
        await self._send_message(client, {
            "type": MessageType.WELCOME.value,
            "client_id": client_id,
            "require_auth": self.require_auth,
            "available_channels": [c.value for c in SubscriptionChannel],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        logger.info(f"WebSocket client connected: {client_id}")
        return client
    
    def disconnect(self, client_id: str):
        """
        Handle client disconnection.
        
        Args:
            client_id: ID of the disconnecting client
        """
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        # Remove from all channel subscriptions
        for channel in client.subscriptions:
            if channel in self.channel_subscribers:
                self.channel_subscribers[channel].discard(client_id)
        
        del self.clients[client_id]
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def handle_message(self, client_id: str, data: str):
        """
        Handle an incoming message from a client.
        
        Args:
            client_id: ID of the sending client
            data: Raw message data
        """
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == MessageType.PING.value:
                await self._handle_ping(client)
            
            elif message_type == MessageType.AUTHENTICATE.value:
                await self._handle_authenticate(client, message)
            
            elif message_type == MessageType.SUBSCRIBE.value:
                await self._handle_subscribe(client, message)
            
            elif message_type == MessageType.UNSUBSCRIBE.value:
                await self._handle_unsubscribe(client, message)
            
            elif message_type in self._message_handlers:
                await self._message_handlers[message_type](client, message)
            
            else:
                await self._send_error(client, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(client, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(client, str(e))
    
    async def _handle_ping(self, client: WebSocketClient):
        """Handle ping message."""
        await self._send_message(client, {
            "type": MessageType.PONG.value,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    async def _handle_authenticate(self, client: WebSocketClient, message: Dict[str, Any]):
        """Handle authentication request."""
        token = message.get("token")
        
        if not token:
            await self._send_error(client, "Token required for authentication")
            return
        
        if self._auth_callback:
            try:
                auth_result = await self._auth_callback(token)
                if auth_result:
                    client.authenticated = True
                    client.user_id = auth_result.get("user_id")
                    client.user_role = auth_result.get("role")
                    
                    await self._send_message(client, {
                        "type": MessageType.AUTHENTICATED.value,
                        "user_id": client.user_id,
                        "role": client.user_role,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                    logger.info(f"Client {client.id} authenticated as {client.user_id}")
                else:
                    await self._send_error(client, "Authentication failed")
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                await self._send_error(client, "Authentication error")
        else:
            # No auth callback, accept any token
            client.authenticated = True
            await self._send_message(client, {
                "type": MessageType.AUTHENTICATED.value,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    async def _handle_subscribe(self, client: WebSocketClient, message: Dict[str, Any]):
        """Handle subscription request."""
        channels = message.get("channels", [])
        
        if isinstance(channels, str):
            channels = [channels]
        
        subscribed = []
        for channel in channels:
            # Check authentication for protected channels
            if self.require_auth and not client.authenticated:
                if channel not in ["system", "market_data"]:
                    continue
            
            # Check permission
            if not client.can_access_channel(channel):
                continue
            
            # Add subscription
            client.subscriptions.add(channel)
            
            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()
            self.channel_subscribers[channel].add(client.id)
            
            subscribed.append(channel)
        
        await self._send_message(client, {
            "type": MessageType.SUBSCRIBED.value,
            "channels": subscribed,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        logger.debug(f"Client {client.id} subscribed to: {subscribed}")
    
    async def _handle_unsubscribe(self, client: WebSocketClient, message: Dict[str, Any]):
        """Handle unsubscription request."""
        channels = message.get("channels", [])
        
        if isinstance(channels, str):
            channels = [channels]
        
        unsubscribed = []
        for channel in channels:
            if channel in client.subscriptions:
                client.subscriptions.discard(channel)
                
                if channel in self.channel_subscribers:
                    self.channel_subscribers[channel].discard(client.id)
                
                unsubscribed.append(channel)
        
        await self._send_message(client, {
            "type": MessageType.UNSUBSCRIBED.value,
            "channels": unsubscribed,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    async def broadcast(
        self,
        channel: str,
        event_type: str,
        data: Dict[str, Any],
        exclude_clients: Optional[Set[str]] = None
    ):
        """
        Broadcast a message to all subscribers of a channel.
        
        Args:
            channel: Channel to broadcast to
            event_type: Type of event
            data: Event data
            exclude_clients: Set of client IDs to exclude
        """
        if channel not in self.channel_subscribers:
            return
        
        message = {
            "type": MessageType.EVENT.value,
            "channel": channel,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        exclude = exclude_clients or set()
        
        # Also broadcast to "all" subscribers
        all_subscribers = self.channel_subscribers.get("all", set())
        channel_subscribers = self.channel_subscribers.get(channel, set())
        
        target_clients = (all_subscribers | channel_subscribers) - exclude
        
        for client_id in target_clients:
            if client_id in self.clients:
                client = self.clients[client_id]
                try:
                    await self._send_message(client, message)
                except Exception as e:
                    logger.warning(f"Failed to send to client {client_id}: {e}")
    
    async def broadcast_to_all(
        self,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Broadcast a message to all connected clients.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        message = {
            "type": MessageType.EVENT.value,
            "channel": "broadcast",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        for client in self.clients.values():
            try:
                await self._send_message(client, message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client {client.id}: {e}")
    
    async def send_to_user(
        self,
        user_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Send a message to all connections of a specific user.
        
        Args:
            user_id: User ID to send to
            event_type: Type of event
            data: Event data
        """
        message = {
            "type": MessageType.EVENT.value,
            "channel": "direct",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        for client in self.clients.values():
            if client.user_id == user_id:
                try:
                    await self._send_message(client, message)
                except Exception as e:
                    logger.warning(f"Failed to send to user {user_id}: {e}")
    
    async def _send_message(self, client: WebSocketClient, message: Dict[str, Any]):
        """Send a message to a client."""
        if client.websocket.client_state == WebSocketState.CONNECTED:
            await client.websocket.send_json(message)
    
    async def _send_error(self, client: WebSocketClient, error: str):
        """Send an error message to a client."""
        await self._send_message(client, {
            "type": MessageType.ERROR.value,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket server statistics."""
        channel_stats = {}
        for channel, subscribers in self.channel_subscribers.items():
            channel_stats[channel] = len(subscribers)
        
        return {
            "total_connections": len(self.clients),
            "authenticated_connections": sum(
                1 for c in self.clients.values() if c.authenticated
            ),
            "channel_subscribers": channel_stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def start_ping_loop(self):
        """Start the ping loop for keeping connections alive."""
        self._running = True
        self._ping_task = asyncio.create_task(self._ping_loop())
    
    async def stop_ping_loop(self):
        """Stop the ping loop."""
        self._running = False
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
    
    async def _ping_loop(self):
        """Background task to ping clients periodically."""
        while self._running:
            await asyncio.sleep(self.ping_interval)
            
            for client_id, client in list(self.clients.items()):
                try:
                    await self._send_message(client, {
                        "type": MessageType.PING.value,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
                except Exception as e:
                    logger.warning(f"Ping failed for client {client_id}: {e}")


class EventBusWebSocketBridge:
    """
    Bridge between the Event Bus and WebSocket server.
    
    Subscribes to event bus events and broadcasts them to
    WebSocket clients based on channel mappings.
    """
    
    # Mapping of event types to WebSocket channels
    EVENT_CHANNEL_MAP = {
        "trade.": SubscriptionChannel.TRADES.value,
        "position.": SubscriptionChannel.POSITIONS.value,
        "order.": SubscriptionChannel.TRADES.value,
        "strategy.": SubscriptionChannel.STRATEGIES.value,
        "ai.": SubscriptionChannel.AI.value,
        "risk.": SubscriptionChannel.RISK.value,
        "alert.": SubscriptionChannel.ALERTS.value,
        "system.": SubscriptionChannel.SYSTEM.value,
        "market.": SubscriptionChannel.MARKET_DATA.value,
    }
    
    def __init__(self, ws_manager: WebSocketManager):
        """
        Initialize the bridge.
        
        Args:
            ws_manager: WebSocket manager instance
        """
        self.ws_manager = ws_manager
        self.event_bus = None
    
    async def connect_event_bus(self, event_bus):
        """
        Connect to the event bus and subscribe to events.
        
        Args:
            event_bus: AsyncEventBus instance
        """
        self.event_bus = event_bus
        
        # Subscribe to all events using pattern
        await event_bus.subscribe_pattern("*", self._handle_event)
        
        logger.info("WebSocket bridge connected to event bus")
    
    async def _handle_event(self, event):
        """Handle an event from the event bus."""
        event_type = event.event_type
        
        # Determine channel based on event type
        channel = self._get_channel_for_event(event_type)
        
        # Broadcast to WebSocket clients
        await self.ws_manager.broadcast(
            channel=channel,
            event_type=event_type,
            data={
                "event_type": event_type,
                "data": event.data,
                "source": event.source_service,
                "correlation_id": event.correlation_id,
                "timestamp": event.timestamp
            }
        )
    
    def _get_channel_for_event(self, event_type: str) -> str:
        """Get the WebSocket channel for an event type."""
        for prefix, channel in self.EVENT_CHANNEL_MAP.items():
            if event_type.startswith(prefix):
                return channel
        return SubscriptionChannel.SYSTEM.value


# FastAPI WebSocket endpoint helper
async def websocket_endpoint(
    websocket: WebSocket,
    manager: WebSocketManager
):
    """
    FastAPI WebSocket endpoint handler.
    
    Usage:
        @app.websocket("/ws")
        async def websocket_route(websocket: WebSocket):
            await websocket_endpoint(websocket, ws_manager)
    """
    client = await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.handle_message(client.id, data)
    except WebSocketDisconnect:
        manager.disconnect(client.id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client.id)


# Factory function
def create_websocket_manager(
    require_auth: bool = True,
    ping_interval: float = 30.0
) -> WebSocketManager:
    """
    Create a WebSocket manager instance.
    
    Args:
        require_auth: Whether authentication is required
        ping_interval: Ping interval in seconds
        
    Returns:
        WebSocketManager instance
    """
    return WebSocketManager(
        require_auth=require_auth,
        ping_interval=ping_interval
    )
