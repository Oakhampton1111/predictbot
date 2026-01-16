"""
PredictBot Simulation - Arbitrage Strategy Adapter
===================================================

Adapter for cross-platform arbitrage strategy.
Detects price discrepancies between platforms for the same event.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

from .base import BaseStrategyAdapter, StrategySignal, SignalType
from ..models import Platform, MarketUpdateEvent, MarketSnapshot
from ..portfolio import VirtualPortfolio


logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity between platforms."""
    market_id_a: str
    market_id_b: str
    platform_a: Platform
    platform_b: Platform
    price_a: float
    price_b: float
    spread: float
    expected_profit: float
    timestamp: datetime


class ArbitrageAdapter(BaseStrategyAdapter):
    """
    Cross-platform arbitrage strategy.
    
    Looks for price discrepancies between platforms for similar markets.
    When the same event is priced differently on two platforms, it
    buys on the cheaper platform and sells on the more expensive one.
    
    Based on polymarket_arb module logic.
    """
    
    def __init__(
        self,
        min_spread: float = 0.02,  # Minimum 2% spread to trade
        max_spread: float = 0.20,  # Maximum spread (avoid suspicious)
        min_liquidity: float = 1000.0,
        max_position_per_market: float = 500.0,
        correlation_threshold: float = 0.8,  # How similar markets must be
        platforms: Optional[List[Platform]] = None,
    ):
        """
        Initialize arbitrage adapter.
        
        Args:
            min_spread: Minimum spread to trigger trade
            max_spread: Maximum spread (avoid suspicious opportunities)
            min_liquidity: Minimum liquidity required
            max_position_per_market: Maximum position size per market
            correlation_threshold: Similarity threshold for market matching
            platforms: Platforms to trade on
        """
        super().__init__(
            name="ArbitrageStrategy",
            platforms=platforms or [Platform.POLYMARKET, Platform.KALSHI],
            position_size=max_position_per_market,
        )
        
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.min_liquidity = min_liquidity
        self.max_position_per_market = max_position_per_market
        self.correlation_threshold = correlation_threshold
        
        # Track correlated markets across platforms
        # Key: normalized question, Value: {platform: market_id}
        self._correlated_markets: Dict[str, Dict[Platform, str]] = {}
        
        # Track recent opportunities
        self._opportunities: List[ArbitrageOpportunity] = []
    
    def _normalize_question(self, question: str) -> str:
        """Normalize market question for matching."""
        # Simple normalization - in production would use NLP
        normalized = question.lower().strip()
        # Remove common prefixes/suffixes
        for prefix in ["will ", "is ", "does ", "can "]:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        return normalized
    
    def _find_correlated_market(
        self,
        market: MarketSnapshot,
    ) -> Optional[Tuple[str, Platform]]:
        """
        Find a correlated market on another platform.
        
        Returns:
            Tuple of (market_id, platform) if found, None otherwise
        """
        normalized = self._normalize_question(market.question)
        
        # Check if we have this market tracked
        if normalized in self._correlated_markets:
            correlations = self._correlated_markets[normalized]
            
            # Find market on different platform
            for platform, market_id in correlations.items():
                if platform != market.platform:
                    return (market_id, platform)
        
        return None
    
    def _register_market(self, market: MarketSnapshot):
        """Register a market for correlation tracking."""
        normalized = self._normalize_question(market.question)
        
        if normalized not in self._correlated_markets:
            self._correlated_markets[normalized] = {}
        
        self._correlated_markets[normalized][market.platform] = market.market_id
    
    def _calculate_spread(
        self,
        price_a: float,
        price_b: float,
    ) -> float:
        """Calculate spread between two prices."""
        return abs(price_a - price_b)
    
    def _detect_opportunity(
        self,
        market_a: MarketSnapshot,
        market_b: MarketSnapshot,
    ) -> Optional[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunity between two markets.
        
        Returns:
            ArbitrageOpportunity if found, None otherwise
        """
        spread = self._calculate_spread(market_a.yes_price, market_b.yes_price)
        
        # Check spread thresholds
        if spread < self.min_spread:
            return None
        if spread > self.max_spread:
            logger.warning(f"Spread {spread:.2%} exceeds max, skipping")
            return None
        
        # Check liquidity
        if market_a.liquidity < self.min_liquidity:
            return None
        if market_b.liquidity < self.min_liquidity:
            return None
        
        # Calculate expected profit (simplified)
        # In reality, would account for fees, slippage, etc.
        expected_profit = spread * self.max_position_per_market
        
        return ArbitrageOpportunity(
            market_id_a=market_a.market_id,
            market_id_b=market_b.market_id,
            platform_a=market_a.platform,
            platform_b=market_b.platform,
            price_a=market_a.yes_price,
            price_b=market_b.yes_price,
            spread=spread,
            expected_profit=expected_profit,
            timestamp=datetime.utcnow(),
        )
    
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio,
    ) -> List[StrategySignal]:
        """Process market update and detect arbitrage opportunities."""
        signals = []
        
        # Create snapshot from event
        snapshot = MarketSnapshot(
            market_id=event.market_id,
            platform=event.platform,
            timestamp=event.timestamp,
            question="",  # Would need to get from metadata
            yes_price=event.yes_price,
            no_price=event.no_price,
            volume_24h=event.volume,
            liquidity=0,  # Would need from metadata
        )
        
        # Update state
        self.update_market_state(snapshot)
        
        # Register for correlation tracking
        self._register_market(snapshot)
        
        # Look for correlated market
        correlated = self._find_correlated_market(snapshot)
        if not correlated:
            return signals
        
        correlated_id, correlated_platform = correlated
        correlated_market = self.get_market_state(correlated_id)
        
        if not correlated_market:
            return signals
        
        # Detect opportunity
        opportunity = self._detect_opportunity(snapshot, correlated_market)
        
        if opportunity:
            self._opportunities.append(opportunity)
            
            # Generate signals
            # Buy on cheaper platform, sell on expensive
            if snapshot.yes_price < correlated_market.yes_price:
                buy_market = snapshot
                sell_market = correlated_market
            else:
                buy_market = correlated_market
                sell_market = snapshot
            
            # Check if we should trade
            if not self.should_trade(buy_market.market_id, portfolio):
                return signals
            
            # Calculate position size
            size = self.calculate_position_size(
                portfolio,
                buy_market.yes_price,
                confidence=min(1.0, opportunity.spread / self.min_spread),
            )
            
            # Buy signal on cheaper platform
            buy_signal = StrategySignal(
                signal_type=SignalType.BUY_YES,
                market_id=buy_market.market_id,
                platform=buy_market.platform,
                timestamp=event.timestamp,
                confidence=min(1.0, opportunity.spread / self.min_spread),
                target_price=buy_market.yes_price,
                size=size,
                reason=f"Arbitrage: spread={opportunity.spread:.2%}",
                metadata={
                    "opportunity": {
                        "spread": opportunity.spread,
                        "expected_profit": opportunity.expected_profit,
                        "correlated_market": sell_market.market_id,
                    }
                }
            )
            signals.append(buy_signal)
            self._record_signal(buy_signal)
            
            # Sell signal on expensive platform (if we have position)
            position = portfolio.get_position(sell_market.market_id)
            if position and position.yes_shares > 0:
                sell_signal = StrategySignal(
                    signal_type=SignalType.SELL_YES,
                    market_id=sell_market.market_id,
                    platform=sell_market.platform,
                    timestamp=event.timestamp,
                    confidence=min(1.0, opportunity.spread / self.min_spread),
                    target_price=sell_market.yes_price,
                    size=min(size, position.yes_shares),
                    reason=f"Arbitrage exit: spread={opportunity.spread:.2%}",
                )
                signals.append(sell_signal)
                self._record_signal(sell_signal)
        
        return signals
    
    def get_statistics(self) -> Dict:
        """Get arbitrage strategy statistics."""
        stats = super().get_statistics()
        
        if self._opportunities:
            spreads = [o.spread for o in self._opportunities]
            profits = [o.expected_profit for o in self._opportunities]
            
            stats.update({
                "opportunities_found": len(self._opportunities),
                "avg_spread": sum(spreads) / len(spreads),
                "max_spread": max(spreads),
                "total_expected_profit": sum(profits),
                "correlated_markets": len(self._correlated_markets),
            })
        
        return stats
