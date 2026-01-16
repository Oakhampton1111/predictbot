"""
PredictBot Simulation - Data Models
====================================

Core data models for prediction market simulation including
market snapshots, order books, trades, and resolutions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class Platform(str, Enum):
    """Supported prediction market platforms."""
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"
    MANIFOLD = "manifold"


class OrderSide(str, Enum):
    """Order side for prediction markets."""
    BUY_YES = "BUY_YES"
    BUY_NO = "BUY_NO"
    SELL_YES = "SELL_YES"
    SELL_NO = "SELL_NO"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class MarketStatus(str, Enum):
    """Market status."""
    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ResolutionOutcome(str, Enum):
    """Market resolution outcomes."""
    YES = "YES"
    NO = "NO"
    CANCELLED = "CANCELLED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class MarketSnapshot:
    """
    Point-in-time snapshot of a prediction market.
    
    Used for historical data storage and backtesting.
    """
    market_id: str
    platform: Platform
    timestamp: datetime
    question: str
    yes_price: float
    no_price: float
    volume_24h: float = 0.0
    liquidity: float = 0.0
    resolution_date: Optional[datetime] = None
    status: MarketStatus = MarketStatus.ACTIVE
    resolved: bool = False
    resolution_outcome: Optional[ResolutionOutcome] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return abs(self.yes_price + self.no_price - 1.0)
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price for YES."""
        return self.yes_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "market_id": self.market_id,
            "platform": self.platform.value,
            "timestamp": self.timestamp.isoformat(),
            "question": self.question,
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "volume_24h": self.volume_24h,
            "liquidity": self.liquidity,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            "status": self.status.value,
            "resolved": self.resolved,
            "resolution_outcome": self.resolution_outcome.value if self.resolution_outcome else None,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketSnapshot":
        """Create from dictionary."""
        return cls(
            market_id=data["market_id"],
            platform=Platform(data["platform"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            question=data["question"],
            yes_price=data["yes_price"],
            no_price=data["no_price"],
            volume_24h=data.get("volume_24h", 0.0),
            liquidity=data.get("liquidity", 0.0),
            resolution_date=datetime.fromisoformat(data["resolution_date"]) if data.get("resolution_date") else None,
            status=MarketStatus(data.get("status", "active")),
            resolved=data.get("resolved", False),
            resolution_outcome=ResolutionOutcome(data["resolution_outcome"]) if data.get("resolution_outcome") else None,
            category=data.get("category"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class OrderBookLevel:
    """Single level in an order book."""
    price: float
    size: float
    order_count: int = 1


@dataclass
class OrderBookSnapshot:
    """
    Point-in-time snapshot of a market's order book.
    
    Stores bid/ask levels for realistic fill simulation.
    """
    market_id: str
    platform: Platform
    timestamp: datetime
    bids: List[OrderBookLevel] = field(default_factory=list)  # Sorted high to low
    asks: List[OrderBookLevel] = field(default_factory=list)  # Sorted low to high
    
    @property
    def best_bid(self) -> Optional[float]:
        """Get best bid price."""
        return self.bids[0].price if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        """Get best ask price."""
        return self.asks[0].price if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        """Calculate spread."""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None
    
    @property
    def mid_price(self) -> Optional[float]:
        """Calculate mid price."""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None
    
    def get_available_liquidity(self, side: OrderSide, max_price: Optional[float] = None) -> float:
        """
        Get available liquidity for a given side up to max_price.
        
        Args:
            side: Order side (BUY_YES means taking asks, etc.)
            max_price: Maximum price willing to pay
            
        Returns:
            Total available size
        """
        if side in [OrderSide.BUY_YES, OrderSide.BUY_NO]:
            levels = self.asks
            if max_price:
                levels = [l for l in levels if l.price <= max_price]
        else:
            levels = self.bids
            if max_price:
                levels = [l for l in levels if l.price >= max_price]
                
        return sum(level.size for level in levels)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_id": self.market_id,
            "platform": self.platform.value,
            "timestamp": self.timestamp.isoformat(),
            "bids": [(l.price, l.size, l.order_count) for l in self.bids],
            "asks": [(l.price, l.size, l.order_count) for l in self.asks]
        }


@dataclass
class TradeEvent:
    """
    Record of a trade that occurred in the market.
    
    Used for historical analysis and realistic simulation.
    """
    trade_id: str
    market_id: str
    platform: Platform
    timestamp: datetime
    side: OrderSide
    price: float
    size: float
    is_taker: bool = True
    fees: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def notional_value(self) -> float:
        """Calculate notional value of trade."""
        return self.price * self.size
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trade_id": self.trade_id,
            "market_id": self.market_id,
            "platform": self.platform.value,
            "timestamp": self.timestamp.isoformat(),
            "side": self.side.value,
            "price": self.price,
            "size": self.size,
            "is_taker": self.is_taker,
            "fees": self.fees,
            "metadata": self.metadata
        }


@dataclass
class MarketResolution:
    """
    Record of a market resolution event.
    
    Critical for calculating final P&L on positions.
    """
    market_id: str
    platform: Platform
    timestamp: datetime
    outcome: ResolutionOutcome
    question: str = ""
    resolution_source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_id": self.market_id,
            "platform": self.platform.value,
            "timestamp": self.timestamp.isoformat(),
            "outcome": self.outcome.value,
            "question": self.question,
            "resolution_source": self.resolution_source,
            "metadata": self.metadata
        }


@dataclass
class Order:
    """
    Order to be submitted to the simulated exchange.
    """
    order_id: str
    market_id: str
    platform: Platform
    side: OrderSide
    order_type: OrderType
    size: float
    limit_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate order parameters."""
        if self.size <= 0:
            return False
        if self.limit_price is not None and (self.limit_price < 0 or self.limit_price > 1):
            return False
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            return False
        return True


@dataclass
class SimulationEvent:
    """
    Base class for simulation events.
    
    Events are processed in timestamp order during backtesting.
    """
    timestamp: datetime
    event_type: str
    
    def __lt__(self, other: "SimulationEvent") -> bool:
        """Enable sorting by timestamp."""
        return self.timestamp < other.timestamp


@dataclass
class MarketUpdateEvent(SimulationEvent):
    """Market price update event."""
    market_id: str
    platform: Platform
    yes_price: float
    no_price: float
    volume: float = 0.0
    
    def __post_init__(self):
        self.event_type = "market_update"


@dataclass
class OrderBookUpdateEvent(SimulationEvent):
    """Order book update event."""
    market_id: str
    platform: Platform
    order_book: OrderBookSnapshot
    
    def __post_init__(self):
        self.event_type = "orderbook_update"


@dataclass
class ResolutionEvent(SimulationEvent):
    """Market resolution event."""
    resolution: MarketResolution
    
    def __post_init__(self):
        self.event_type = "resolution"


@dataclass
class NewsEvent(SimulationEvent):
    """News/external event for correlation analysis."""
    headline: str
    source: str
    sentiment: Optional[float] = None  # -1 to 1
    related_markets: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.event_type = "news"
