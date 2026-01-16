"""
PredictBot Simulation - Simulated Exchange
===========================================

Simulates order execution for prediction markets with realistic
fill models, latency, and fee structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import random
import math
import uuid

from .models import (
    Platform,
    OrderSide,
    OrderType,
    Order,
    OrderBookSnapshot,
    MarketSnapshot
)


class FillStatus(str, Enum):
    """Order fill status."""
    FILLED = "filled"
    PARTIAL = "partial"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class FillResult:
    """Result of an order fill attempt."""
    status: FillStatus
    filled_size: float = 0.0
    fill_price: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    latency_ms: float = 0.0
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def filled(self) -> bool:
        """Check if order was at least partially filled."""
        return self.status in [FillStatus.FILLED, FillStatus.PARTIAL]
    
    @property
    def total_cost(self) -> float:
        """Total cost including fees."""
        return self.filled_size * self.fill_price + self.fees


class FillModel:
    """
    Base fill model for simulating order execution.
    
    Determines how orders are filled based on market conditions.
    """
    
    def __init__(
        self,
        prob_fill_on_limit: float = 0.8,
        prob_slippage: float = 0.3,
        max_slippage_bps: int = 50,
        random_seed: Optional[int] = None
    ):
        """
        Initialize fill model.
        
        Args:
            prob_fill_on_limit: Probability limit order fills at limit price
            prob_slippage: Probability of slippage on market orders
            max_slippage_bps: Maximum slippage in basis points
            random_seed: Random seed for reproducibility
        """
        self.prob_fill_on_limit = prob_fill_on_limit
        self.prob_slippage = prob_slippage
        self.max_slippage_bps = max_slippage_bps
        self.rng = random.Random(random_seed)
        
    def attempt_fill(
        self,
        order: Order,
        market_price: float,
        available_liquidity: float,
        order_book: Optional[OrderBookSnapshot] = None
    ) -> FillResult:
        """
        Attempt to fill an order.
        
        Args:
            order: Order to fill
            market_price: Current market price
            available_liquidity: Available liquidity at current price
            order_book: Optional order book for more realistic fills
            
        Returns:
            FillResult with fill details
        """
        # Validate order
        if not order.validate():
            return FillResult(
                status=FillStatus.REJECTED,
                reason="invalid_order"
            )
            
        # Check liquidity
        if available_liquidity <= 0:
            return FillResult(
                status=FillStatus.REJECTED,
                reason="no_liquidity"
            )
            
        # Determine fill size
        fill_size = min(order.size, available_liquidity)
        
        # Calculate fill price with potential slippage
        fill_price = self._calculate_fill_price(
            order=order,
            market_price=market_price,
            fill_size=fill_size,
            available_liquidity=available_liquidity
        )
        
        # Check limit price
        if order.order_type == OrderType.LIMIT and order.limit_price is not None:
            if order.side in [OrderSide.BUY_YES, OrderSide.BUY_NO]:
                if fill_price > order.limit_price:
                    # Price moved above limit
                    if self.rng.random() > self.prob_fill_on_limit:
                        return FillResult(
                            status=FillStatus.REJECTED,
                            reason="price_above_limit"
                        )
                    fill_price = order.limit_price
            else:
                if fill_price < order.limit_price:
                    if self.rng.random() > self.prob_fill_on_limit:
                        return FillResult(
                            status=FillStatus.REJECTED,
                            reason="price_below_limit"
                        )
                    fill_price = order.limit_price
                    
        # Calculate slippage
        slippage = abs(fill_price - market_price)
        
        # Determine fill status
        if fill_size >= order.size:
            status = FillStatus.FILLED
        elif fill_size > 0:
            status = FillStatus.PARTIAL
        else:
            status = FillStatus.REJECTED
            
        return FillResult(
            status=status,
            filled_size=fill_size,
            fill_price=fill_price,
            slippage=slippage
        )
    
    def _calculate_fill_price(
        self,
        order: Order,
        market_price: float,
        fill_size: float,
        available_liquidity: float
    ) -> float:
        """Calculate fill price with slippage."""
        # Base price is market price
        price = market_price
        
        # Apply slippage based on order size relative to liquidity
        if self.rng.random() < self.prob_slippage:
            # Size impact - larger orders have more slippage
            size_ratio = fill_size / max(available_liquidity, 1)
            slippage_factor = min(size_ratio * 2, 1.0)  # Cap at 100% of max slippage
            
            max_slip = self.max_slippage_bps / 10000
            slippage = self.rng.uniform(0, max_slip * slippage_factor)
            
            # Direction depends on order side
            if order.side in [OrderSide.BUY_YES, OrderSide.BUY_NO]:
                price = min(price + slippage, 0.99)  # Cap at 0.99
            else:
                price = max(price - slippage, 0.01)  # Floor at 0.01
                
        return round(price, 4)


class RealisticFillModel(FillModel):
    """
    More realistic fill model that considers order book depth.
    
    Uses order book to simulate fills across multiple price levels.
    """
    
    def __init__(
        self,
        prob_fill_on_limit: float = 0.7,
        prob_slippage: float = 0.5,
        max_slippage_bps: int = 100,
        price_impact_factor: float = 0.1,
        random_seed: Optional[int] = None
    ):
        super().__init__(
            prob_fill_on_limit=prob_fill_on_limit,
            prob_slippage=prob_slippage,
            max_slippage_bps=max_slippage_bps,
            random_seed=random_seed
        )
        self.price_impact_factor = price_impact_factor
        
    def attempt_fill(
        self,
        order: Order,
        market_price: float,
        available_liquidity: float,
        order_book: Optional[OrderBookSnapshot] = None
    ) -> FillResult:
        """
        Attempt to fill using order book if available.
        """
        if order_book is None:
            return super().attempt_fill(
                order, market_price, available_liquidity, order_book
            )
            
        # Use order book for more realistic fills
        return self._fill_from_order_book(order, order_book)
    
    def _fill_from_order_book(
        self,
        order: Order,
        order_book: OrderBookSnapshot
    ) -> FillResult:
        """Fill order by walking through order book levels."""
        # Determine which side of the book to use
        if order.side in [OrderSide.BUY_YES, OrderSide.BUY_NO]:
            levels = order_book.asks
        else:
            levels = order_book.bids
            
        if not levels:
            return FillResult(
                status=FillStatus.REJECTED,
                reason="empty_order_book"
            )
            
        remaining_size = order.size
        total_cost = 0.0
        filled_size = 0.0
        
        for level in levels:
            # Check limit price
            if order.limit_price is not None:
                if order.side in [OrderSide.BUY_YES, OrderSide.BUY_NO]:
                    if level.price > order.limit_price:
                        break
                else:
                    if level.price < order.limit_price:
                        break
                        
            # Fill at this level
            fill_at_level = min(remaining_size, level.size)
            total_cost += fill_at_level * level.price
            filled_size += fill_at_level
            remaining_size -= fill_at_level
            
            if remaining_size <= 0:
                break
                
        if filled_size == 0:
            return FillResult(
                status=FillStatus.REJECTED,
                reason="no_fills_at_limit"
            )
            
        # Calculate average fill price
        avg_price = total_cost / filled_size
        
        # Calculate slippage from best price
        best_price = levels[0].price
        slippage = abs(avg_price - best_price)
        
        status = FillStatus.FILLED if filled_size >= order.size else FillStatus.PARTIAL
        
        return FillResult(
            status=status,
            filled_size=filled_size,
            fill_price=avg_price,
            slippage=slippage
        )


class LatencyModel:
    """
    Models network and execution latency.
    """
    
    def __init__(
        self,
        mean_ms: float = 50.0,
        std_ms: float = 20.0,
        min_ms: float = 10.0,
        max_ms: float = 500.0,
        random_seed: Optional[int] = None
    ):
        """
        Initialize latency model.
        
        Args:
            mean_ms: Mean latency in milliseconds
            std_ms: Standard deviation of latency
            min_ms: Minimum latency
            max_ms: Maximum latency
            random_seed: Random seed for reproducibility
        """
        self.mean_ms = mean_ms
        self.std_ms = std_ms
        self.min_ms = min_ms
        self.max_ms = max_ms
        self.rng = random.Random(random_seed)
        
    def get_latency(self) -> float:
        """Get simulated latency in milliseconds."""
        latency = self.rng.gauss(self.mean_ms, self.std_ms)
        return max(self.min_ms, min(self.max_ms, latency))


class FeeModel:
    """
    Platform-specific fee structures.
    """
    
    # Fee structures by platform
    FEE_STRUCTURES = {
        Platform.POLYMARKET: {
            "maker_fee": 0.0,
            "taker_fee": 0.02,  # 2%
            "withdrawal_fee": 0.0,
        },
        Platform.KALSHI: {
            "maker_fee": 0.0,
            "taker_fee": 0.07,  # 7 cents per contract
            "fee_cap": 0.07,   # Capped at 7 cents
            "per_contract": True,
        },
        Platform.MANIFOLD: {
            "maker_fee": 0.0,
            "taker_fee": 0.0,  # Play money
            "withdrawal_fee": 0.0,
        }
    }
    
    def __init__(self, custom_fees: Optional[Dict[Platform, Dict]] = None):
        """
        Initialize fee model.
        
        Args:
            custom_fees: Optional custom fee structures
        """
        self.fees = dict(self.FEE_STRUCTURES)
        if custom_fees:
            self.fees.update(custom_fees)
            
    def calculate_fees(
        self,
        platform: Platform,
        size: float,
        price: float,
        is_maker: bool = False
    ) -> float:
        """
        Calculate trading fees.
        
        Args:
            platform: Trading platform
            size: Order size
            price: Execution price
            is_maker: Whether order is maker (adds liquidity)
            
        Returns:
            Fee amount
        """
        fee_struct = self.fees.get(platform, {})
        
        if is_maker:
            fee_rate = fee_struct.get("maker_fee", 0)
        else:
            fee_rate = fee_struct.get("taker_fee", 0)
            
        if fee_struct.get("per_contract", False):
            # Per-contract fee (like Kalshi)
            fee = size * fee_rate
            fee_cap = fee_struct.get("fee_cap")
            if fee_cap:
                fee = min(fee, size * fee_cap)
        else:
            # Percentage fee
            fee = size * price * fee_rate
            
        return round(fee, 4)


class SimulatedExchange:
    """
    Simulates a prediction market exchange.
    
    Handles order submission, execution, and market state.
    """
    
    def __init__(
        self,
        fill_model: Optional[FillModel] = None,
        latency_model: Optional[LatencyModel] = None,
        fee_model: Optional[FeeModel] = None,
        random_seed: Optional[int] = None
    ):
        """
        Initialize simulated exchange.
        
        Args:
            fill_model: Model for order fills
            latency_model: Model for latency simulation
            fee_model: Model for fee calculation
            random_seed: Random seed for reproducibility
        """
        self.fill_model = fill_model or FillModel(random_seed=random_seed)
        self.latency_model = latency_model or LatencyModel(random_seed=random_seed)
        self.fee_model = fee_model or FeeModel()
        
        # Market state
        self.markets: Dict[str, MarketSnapshot] = {}
        self.order_books: Dict[str, OrderBookSnapshot] = {}
        self.pending_orders: List[Order] = []
        self.executed_orders: List[tuple] = []  # (order, fill_result)
        
    def update_market(self, snapshot: MarketSnapshot):
        """Update market state with new snapshot."""
        self.markets[snapshot.market_id] = snapshot
        
    def update_order_book(self, order_book: OrderBookSnapshot):
        """Update order book for a market."""
        self.order_books[order_book.market_id] = order_book
        
    def get_market_price(self, market_id: str, side: OrderSide) -> Optional[float]:
        """
        Get current market price for a side.
        
        Args:
            market_id: Market identifier
            side: Order side
            
        Returns:
            Current price or None if market not found
        """
        market = self.markets.get(market_id)
        if not market:
            return None
            
        if side in [OrderSide.BUY_YES, OrderSide.SELL_YES]:
            return market.yes_price
        else:
            return market.no_price
            
    def get_available_liquidity(
        self,
        market_id: str,
        side: OrderSide
    ) -> float:
        """
        Get available liquidity for a market/side.
        
        Args:
            market_id: Market identifier
            side: Order side
            
        Returns:
            Available liquidity
        """
        # Check order book first
        order_book = self.order_books.get(market_id)
        if order_book:
            return order_book.get_available_liquidity(side)
            
        # Fall back to market liquidity estimate
        market = self.markets.get(market_id)
        if market:
            return market.liquidity
            
        return 0.0
        
    def submit_order(self, order: Order) -> FillResult:
        """
        Submit an order for execution.
        
        Args:
            order: Order to submit
            
        Returns:
            FillResult with execution details
        """
        # Get market price
        market_price = self.get_market_price(order.market_id, order.side)
        if market_price is None:
            return FillResult(
                status=FillStatus.REJECTED,
                reason="market_not_found"
            )
            
        # Get available liquidity
        liquidity = self.get_available_liquidity(order.market_id, order.side)
        
        # Get order book if available
        order_book = self.order_books.get(order.market_id)
        
        # Attempt fill
        result = self.fill_model.attempt_fill(
            order=order,
            market_price=market_price,
            available_liquidity=liquidity,
            order_book=order_book
        )
        
        # Add latency
        result.latency_ms = self.latency_model.get_latency()
        
        # Calculate fees if filled
        if result.filled:
            result.fees = self.fee_model.calculate_fees(
                platform=order.platform,
                size=result.filled_size,
                price=result.fill_price,
                is_maker=order.order_type == OrderType.LIMIT
            )
            
        # Record execution
        self.executed_orders.append((order, result))
        
        return result
        
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        for i, order in enumerate(self.pending_orders):
            if order.order_id == order_id:
                self.pending_orders.pop(i)
                return True
        return False
        
    def get_execution_history(self) -> List[tuple]:
        """Get history of executed orders."""
        return list(self.executed_orders)
        
    def reset(self):
        """Reset exchange state."""
        self.markets.clear()
        self.order_books.clear()
        self.pending_orders.clear()
        self.executed_orders.clear()
