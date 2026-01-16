"""
PredictBot Simulation - Market Maker Strategy Adapter
======================================================

Adapter for market making strategy.
Provides liquidity by placing orders on both sides of the market.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Deque, Tuple

from .base import BaseStrategyAdapter, StrategySignal, SignalType
from ..models import Platform, MarketUpdateEvent, MarketSnapshot, OrderBookSnapshot
from ..portfolio import VirtualPortfolio


logger = logging.getLogger(__name__)


@dataclass
class Quote:
    """A two-sided quote."""
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float
    timestamp: datetime


class MarketMakerAdapter(BaseStrategyAdapter):
    """
    Market making strategy.
    
    Provides liquidity by maintaining quotes on both sides of the market.
    Profits from the bid-ask spread while managing inventory risk.
    
    Based on manifold_mm and polymarket_mm module logic.
    """
    
    def __init__(
        self,
        target_spread: float = 0.02,  # 2% spread
        min_spread: float = 0.01,  # Minimum spread
        max_spread: float = 0.10,  # Maximum spread
        quote_size: float = 100.0,
        max_inventory: float = 500.0,
        inventory_skew: float = 0.5,  # How much to skew quotes based on inventory
        refresh_interval_seconds: int = 60,
        min_edge: float = 0.005,  # Minimum edge over fair value
        platforms: Optional[List[Platform]] = None,
    ):
        """
        Initialize market maker.
        
        Args:
            target_spread: Target bid-ask spread
            min_spread: Minimum spread to maintain
            max_spread: Maximum spread
            quote_size: Size of each quote
            max_inventory: Maximum inventory per side
            inventory_skew: How much to adjust quotes based on inventory
            refresh_interval_seconds: How often to refresh quotes
            min_edge: Minimum edge required
            platforms: Platforms to trade on
        """
        super().__init__(
            name="MarketMakerStrategy",
            platforms=platforms,
            position_size=quote_size,
        )
        
        self.target_spread = target_spread
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.quote_size = quote_size
        self.max_inventory = max_inventory
        self.inventory_skew = inventory_skew
        self.refresh_interval_seconds = refresh_interval_seconds
        self.min_edge = min_edge
        
        # Track active quotes
        self._active_quotes: Dict[str, Quote] = {}
        
        # Track last quote time
        self._last_quote_time: Dict[str, datetime] = {}
        
        # Track fair value estimates
        self._fair_values: Dict[str, float] = {}
        
        # Price history for fair value estimation
        self._price_history: Dict[str, Deque[float]] = {}
    
    def _estimate_fair_value(self, market_id: str, current_price: float) -> float:
        """
        Estimate fair value for a market.
        
        Uses exponential moving average of recent prices.
        """
        if market_id not in self._price_history:
            self._price_history[market_id] = deque(maxlen=20)
        
        history = self._price_history[market_id]
        history.append(current_price)
        
        if len(history) < 3:
            return current_price
        
        # Simple EMA
        alpha = 0.3
        ema = history[0]
        for price in list(history)[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        self._fair_values[market_id] = ema
        return ema
    
    def _calculate_inventory_adjustment(
        self,
        portfolio: VirtualPortfolio,
        market_id: str,
    ) -> float:
        """
        Calculate price adjustment based on inventory.
        
        Returns adjustment to add to bid/ask prices.
        Positive = we're long, want to sell more (lower bid, raise ask)
        Negative = we're short, want to buy more (raise bid, lower ask)
        """
        position = portfolio.get_position(market_id)
        if not position:
            return 0.0
        
        # Net position (positive = long YES, negative = long NO)
        net_position = position.yes_shares - position.no_shares
        
        # Normalize by max inventory
        inventory_ratio = net_position / self.max_inventory if self.max_inventory > 0 else 0
        
        # Clamp to [-1, 1]
        inventory_ratio = max(-1, min(1, inventory_ratio))
        
        # Calculate adjustment
        adjustment = inventory_ratio * self.inventory_skew * self.target_spread
        
        return adjustment
    
    def _calculate_quotes(
        self,
        market_id: str,
        fair_value: float,
        inventory_adjustment: float,
        timestamp: datetime,
    ) -> Quote:
        """Calculate bid and ask quotes."""
        half_spread = self.target_spread / 2
        
        # Base quotes around fair value
        bid_price = fair_value - half_spread
        ask_price = fair_value + half_spread
        
        # Apply inventory adjustment
        bid_price -= inventory_adjustment
        ask_price -= inventory_adjustment
        
        # Ensure minimum spread
        if ask_price - bid_price < self.min_spread:
            mid = (bid_price + ask_price) / 2
            bid_price = mid - self.min_spread / 2
            ask_price = mid + self.min_spread / 2
        
        # Clamp to valid price range
        bid_price = max(0.01, min(0.98, bid_price))
        ask_price = max(0.02, min(0.99, ask_price))
        
        # Ensure ask > bid
        if ask_price <= bid_price:
            ask_price = bid_price + self.min_spread
        
        return Quote(
            bid_price=bid_price,
            bid_size=self.quote_size,
            ask_price=ask_price,
            ask_size=self.quote_size,
            timestamp=timestamp,
        )
    
    def _should_refresh_quotes(self, market_id: str, timestamp: datetime) -> bool:
        """Check if quotes should be refreshed."""
        last_time = self._last_quote_time.get(market_id)
        if not last_time:
            return True
        
        elapsed = (timestamp - last_time).total_seconds()
        return elapsed >= self.refresh_interval_seconds
    
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio,
    ) -> List[StrategySignal]:
        """Process market update and generate market making signals."""
        signals = []
        market_id = event.market_id
        
        # Update market state
        snapshot = MarketSnapshot(
            market_id=market_id,
            platform=event.platform,
            timestamp=event.timestamp,
            question="",
            yes_price=event.yes_price,
            no_price=event.no_price,
            volume_24h=event.volume,
        )
        self.update_market_state(snapshot)
        
        # Check if we should refresh quotes
        if not self._should_refresh_quotes(market_id, event.timestamp):
            return signals
        
        # Estimate fair value
        fair_value = self._estimate_fair_value(market_id, event.yes_price)
        
        # Calculate inventory adjustment
        inventory_adj = self._calculate_inventory_adjustment(portfolio, market_id)
        
        # Calculate new quotes
        quote = self._calculate_quotes(
            market_id,
            fair_value,
            inventory_adj,
            event.timestamp,
        )
        
        # Check if we have edge
        current_mid = (event.yes_price + (1 - event.no_price)) / 2
        edge = abs(fair_value - current_mid)
        
        if edge < self.min_edge:
            logger.debug(f"Insufficient edge for {market_id}: {edge:.4f}")
            return signals
        
        # Store quote
        self._active_quotes[market_id] = quote
        self._last_quote_time[market_id] = event.timestamp
        
        # Check inventory limits
        position = portfolio.get_position(market_id)
        current_yes = position.yes_shares if position else 0
        current_no = position.no_shares if position else 0
        
        # Generate bid signal (buy YES) if not at max inventory
        if current_yes < self.max_inventory:
            bid_signal = StrategySignal(
                signal_type=SignalType.BUY_YES,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=0.5,  # MM signals are passive
                target_price=quote.bid_price,
                size=min(quote.bid_size, self.max_inventory - current_yes),
                reason=f"MM bid: fair={fair_value:.3f}, inv_adj={inventory_adj:.4f}",
                metadata={
                    "quote_type": "bid",
                    "fair_value": fair_value,
                    "inventory_adjustment": inventory_adj,
                }
            )
            signals.append(bid_signal)
            self._record_signal(bid_signal)
        
        # Generate ask signal (sell YES / buy NO) if not at max inventory
        if current_no < self.max_inventory:
            ask_signal = StrategySignal(
                signal_type=SignalType.BUY_NO,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=0.5,
                target_price=1 - quote.ask_price,  # NO price
                size=min(quote.ask_size, self.max_inventory - current_no),
                reason=f"MM ask: fair={fair_value:.3f}, inv_adj={inventory_adj:.4f}",
                metadata={
                    "quote_type": "ask",
                    "fair_value": fair_value,
                    "inventory_adjustment": inventory_adj,
                }
            )
            signals.append(ask_signal)
            self._record_signal(ask_signal)
        
        return signals
    
    def on_orderbook_update(
        self,
        market_id: str,
        orderbook: OrderBookSnapshot,
        portfolio: VirtualPortfolio,
    ) -> List[StrategySignal]:
        """
        Process order book update.
        
        Market makers can use order book data to improve quotes.
        """
        self._orderbook_state[market_id] = orderbook
        
        # Could adjust quotes based on order book depth
        # For now, just store the data
        
        return []
    
    def get_statistics(self) -> Dict:
        """Get market maker statistics."""
        stats = super().get_statistics()
        
        stats.update({
            "active_quotes": len(self._active_quotes),
            "markets_quoted": list(self._active_quotes.keys()),
            "target_spread": self.target_spread,
            "max_inventory": self.max_inventory,
        })
        
        if self._fair_values:
            stats["fair_values"] = dict(self._fair_values)
        
        return stats
