"""
PredictBot Simulation - Momentum Strategy Adapter
==================================================

Adapter for momentum-based trading strategy.
Follows price trends and trades in the direction of momentum.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Deque

from .base import BaseStrategyAdapter, StrategySignal, SignalType
from ..models import Platform, MarketUpdateEvent, MarketSnapshot
from ..portfolio import VirtualPortfolio


logger = logging.getLogger(__name__)


@dataclass
class MomentumIndicators:
    """Momentum indicators for a market."""
    rsi: float  # Relative Strength Index (0-100)
    momentum: float  # Price momentum
    trend_strength: float  # Trend strength (0-1)
    direction: str  # "bullish", "bearish", "neutral"


class MomentumAdapter(BaseStrategyAdapter):
    """
    Momentum trading strategy.
    
    Uses technical indicators to identify and follow price trends.
    Buys when momentum is positive and sells when momentum turns negative.
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        momentum_period: int = 10,
        min_trend_strength: float = 0.3,
        entry_threshold: float = 0.02,  # 2% momentum to enter
        exit_threshold: float = -0.01,  # -1% momentum to exit
        max_position_per_market: float = 300.0,
        platforms: Optional[List[Platform]] = None,
    ):
        """
        Initialize momentum strategy.
        
        Args:
            rsi_period: Period for RSI calculation
            rsi_overbought: RSI level considered overbought
            rsi_oversold: RSI level considered oversold
            momentum_period: Period for momentum calculation
            min_trend_strength: Minimum trend strength to trade
            entry_threshold: Momentum threshold to enter
            exit_threshold: Momentum threshold to exit
            max_position_per_market: Maximum position size
            platforms: Platforms to trade on
        """
        super().__init__(
            name="MomentumStrategy",
            platforms=platforms,
            position_size=max_position_per_market,
        )
        
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.momentum_period = momentum_period
        self.min_trend_strength = min_trend_strength
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.max_position_per_market = max_position_per_market
        
        # Price history per market
        self._price_history: Dict[str, Deque[float]] = {}
        
        # Track indicators
        self._indicators: Dict[str, MomentumIndicators] = {}
    
    def _get_price_history(self, market_id: str) -> Deque[float]:
        """Get or create price history for a market."""
        if market_id not in self._price_history:
            self._price_history[market_id] = deque(maxlen=max(self.rsi_period, self.momentum_period) * 2)
        return self._price_history[market_id]
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < self.rsi_period + 1:
            return 50.0  # Neutral
        
        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [max(0, c) for c in changes[-self.rsi_period:]]
        losses = [abs(min(0, c)) for c in changes[-self.rsi_period:]]
        
        avg_gain = sum(gains) / self.rsi_period
        avg_loss = sum(losses) / self.rsi_period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_momentum(self, prices: List[float]) -> float:
        """Calculate price momentum."""
        if len(prices) < self.momentum_period:
            return 0.0
        
        old_price = prices[-self.momentum_period]
        current_price = prices[-1]
        
        if old_price == 0:
            return 0.0
        
        return (current_price - old_price) / old_price
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """
        Calculate trend strength using linear regression R-squared.
        
        Returns value between 0 (no trend) and 1 (strong trend).
        """
        if len(prices) < 5:
            return 0.0
        
        n = len(prices)
        x = list(range(n))
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(prices) / n
        
        # Calculate slope and R-squared
        numerator = sum((x[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator_x = sum((x[i] - x_mean) ** 2 for i in range(n))
        denominator_y = sum((prices[i] - y_mean) ** 2 for i in range(n))
        
        if denominator_x == 0 or denominator_y == 0:
            return 0.0
        
        r = numerator / (denominator_x ** 0.5 * denominator_y ** 0.5)
        r_squared = r ** 2
        
        return r_squared
    
    def _calculate_indicators(self, market_id: str) -> Optional[MomentumIndicators]:
        """Calculate all momentum indicators for a market."""
        history = self._get_price_history(market_id)
        prices = list(history)
        
        if len(prices) < self.rsi_period:
            return None
        
        rsi = self._calculate_rsi(prices)
        momentum = self._calculate_momentum(prices)
        trend_strength = self._calculate_trend_strength(prices)
        
        # Determine direction
        if rsi > 50 and momentum > 0:
            direction = "bullish"
        elif rsi < 50 and momentum < 0:
            direction = "bearish"
        else:
            direction = "neutral"
        
        indicators = MomentumIndicators(
            rsi=rsi,
            momentum=momentum,
            trend_strength=trend_strength,
            direction=direction,
        )
        
        self._indicators[market_id] = indicators
        return indicators
    
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio,
    ) -> List[StrategySignal]:
        """Process market update and generate momentum signals."""
        signals = []
        market_id = event.market_id
        
        # Update price history
        history = self._get_price_history(market_id)
        history.append(event.yes_price)
        
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
        
        # Calculate indicators
        indicators = self._calculate_indicators(market_id)
        if not indicators:
            return signals
        
        # Check trend strength
        if indicators.trend_strength < self.min_trend_strength:
            return signals
        
        # Get current position
        position = portfolio.get_position(market_id)
        has_yes_position = position and position.yes_shares > 0
        has_no_position = position and position.no_shares > 0
        
        # Generate signals based on indicators
        if indicators.direction == "bullish":
            # Strong upward momentum
            if indicators.momentum > self.entry_threshold and not has_yes_position:
                # Check RSI not overbought
                if indicators.rsi < self.rsi_overbought:
                    confidence = min(1.0, indicators.trend_strength + abs(indicators.momentum))
                    size = self.calculate_position_size(portfolio, event.yes_price, confidence)
                    
                    signal = StrategySignal(
                        signal_type=SignalType.BUY_YES,
                        market_id=market_id,
                        platform=event.platform,
                        timestamp=event.timestamp,
                        confidence=confidence,
                        size=size,
                        reason=f"Bullish momentum: RSI={indicators.rsi:.1f}, mom={indicators.momentum:.2%}",
                        metadata={
                            "rsi": indicators.rsi,
                            "momentum": indicators.momentum,
                            "trend_strength": indicators.trend_strength,
                        }
                    )
                    signals.append(signal)
                    self._record_signal(signal)
            
            # Exit NO position on bullish signal
            if has_no_position:
                signal = StrategySignal(
                    signal_type=SignalType.SELL_NO,
                    market_id=market_id,
                    platform=event.platform,
                    timestamp=event.timestamp,
                    confidence=0.8,
                    size=position.no_shares,
                    reason="Exit NO on bullish momentum",
                )
                signals.append(signal)
                self._record_signal(signal)
        
        elif indicators.direction == "bearish":
            # Strong downward momentum
            if indicators.momentum < -self.entry_threshold and not has_no_position:
                # Check RSI not oversold
                if indicators.rsi > self.rsi_oversold:
                    confidence = min(1.0, indicators.trend_strength + abs(indicators.momentum))
                    size = self.calculate_position_size(portfolio, event.no_price, confidence)
                    
                    signal = StrategySignal(
                        signal_type=SignalType.BUY_NO,
                        market_id=market_id,
                        platform=event.platform,
                        timestamp=event.timestamp,
                        confidence=confidence,
                        size=size,
                        reason=f"Bearish momentum: RSI={indicators.rsi:.1f}, mom={indicators.momentum:.2%}",
                        metadata={
                            "rsi": indicators.rsi,
                            "momentum": indicators.momentum,
                            "trend_strength": indicators.trend_strength,
                        }
                    )
                    signals.append(signal)
                    self._record_signal(signal)
            
            # Exit YES position on bearish signal
            if has_yes_position:
                signal = StrategySignal(
                    signal_type=SignalType.SELL_YES,
                    market_id=market_id,
                    platform=event.platform,
                    timestamp=event.timestamp,
                    confidence=0.8,
                    size=position.yes_shares,
                    reason="Exit YES on bearish momentum",
                )
                signals.append(signal)
                self._record_signal(signal)
        
        # Check for exit signals on existing positions
        if has_yes_position and indicators.momentum < self.exit_threshold:
            signal = StrategySignal(
                signal_type=SignalType.SELL_YES,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=0.7,
                size=position.yes_shares,
                reason=f"Momentum exit: mom={indicators.momentum:.2%}",
            )
            signals.append(signal)
            self._record_signal(signal)
        
        if has_no_position and indicators.momentum > -self.exit_threshold:
            signal = StrategySignal(
                signal_type=SignalType.SELL_NO,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=0.7,
                size=position.no_shares,
                reason=f"Momentum exit: mom={indicators.momentum:.2%}",
            )
            signals.append(signal)
            self._record_signal(signal)
        
        return signals
    
    def get_statistics(self) -> Dict:
        """Get momentum strategy statistics."""
        stats = super().get_statistics()
        
        if self._indicators:
            bullish = sum(1 for i in self._indicators.values() if i.direction == "bullish")
            bearish = sum(1 for i in self._indicators.values() if i.direction == "bearish")
            neutral = sum(1 for i in self._indicators.values() if i.direction == "neutral")
            
            avg_rsi = sum(i.rsi for i in self._indicators.values()) / len(self._indicators)
            avg_momentum = sum(i.momentum for i in self._indicators.values()) / len(self._indicators)
            
            stats.update({
                "markets_analyzed": len(self._indicators),
                "bullish_markets": bullish,
                "bearish_markets": bearish,
                "neutral_markets": neutral,
                "avg_rsi": avg_rsi,
                "avg_momentum": avg_momentum,
            })
        
        return stats
