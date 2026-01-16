"""
PredictBot Simulation - Mean Reversion Strategy Adapter
========================================================

Adapter for mean reversion trading strategy.
Bets on prices returning to their historical average.
"""

import logging
import statistics
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Deque

from .base import BaseStrategyAdapter, StrategySignal, SignalType
from ..models import Platform, MarketUpdateEvent, MarketSnapshot
from ..portfolio import VirtualPortfolio


logger = logging.getLogger(__name__)


@dataclass
class MeanReversionIndicators:
    """Mean reversion indicators for a market."""
    mean: float
    std_dev: float
    z_score: float  # How many std devs from mean
    bollinger_upper: float
    bollinger_lower: float
    is_overbought: bool
    is_oversold: bool


class MeanReversionAdapter(BaseStrategyAdapter):
    """
    Mean reversion trading strategy.
    
    Assumes prices tend to revert to their historical mean.
    Buys when price is significantly below mean, sells when above.
    Uses Bollinger Bands and Z-score for entry/exit signals.
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        z_score_entry: float = 2.0,  # Enter when Z-score exceeds this
        z_score_exit: float = 0.5,  # Exit when Z-score falls below this
        bollinger_std: float = 2.0,  # Bollinger Band standard deviations
        min_std_dev: float = 0.01,  # Minimum volatility to trade
        max_position_per_market: float = 300.0,
        hold_period_hours: int = 24,  # Maximum hold period
        platforms: Optional[List[Platform]] = None,
    ):
        """
        Initialize mean reversion strategy.
        
        Args:
            lookback_period: Period for calculating mean/std
            z_score_entry: Z-score threshold for entry
            z_score_exit: Z-score threshold for exit
            bollinger_std: Standard deviations for Bollinger Bands
            min_std_dev: Minimum standard deviation to trade
            max_position_per_market: Maximum position size
            hold_period_hours: Maximum hours to hold position
            platforms: Platforms to trade on
        """
        super().__init__(
            name="MeanReversionStrategy",
            platforms=platforms,
            position_size=max_position_per_market,
        )
        
        self.lookback_period = lookback_period
        self.z_score_entry = z_score_entry
        self.z_score_exit = z_score_exit
        self.bollinger_std = bollinger_std
        self.min_std_dev = min_std_dev
        self.max_position_per_market = max_position_per_market
        self.hold_period_hours = hold_period_hours
        
        # Price history per market
        self._price_history: Dict[str, Deque[float]] = {}
        
        # Track indicators
        self._indicators: Dict[str, MeanReversionIndicators] = {}
        
        # Track entry times for hold period
        self._entry_times: Dict[str, datetime] = {}
    
    def _get_price_history(self, market_id: str) -> Deque[float]:
        """Get or create price history for a market."""
        if market_id not in self._price_history:
            self._price_history[market_id] = deque(maxlen=self.lookback_period * 2)
        return self._price_history[market_id]
    
    def _calculate_indicators(
        self,
        market_id: str,
        current_price: float,
    ) -> Optional[MeanReversionIndicators]:
        """Calculate mean reversion indicators."""
        history = self._get_price_history(market_id)
        prices = list(history)
        
        if len(prices) < self.lookback_period:
            return None
        
        # Use last N prices for calculations
        recent_prices = prices[-self.lookback_period:]
        
        # Calculate mean and standard deviation
        mean = statistics.mean(recent_prices)
        std_dev = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
        
        # Check minimum volatility
        if std_dev < self.min_std_dev:
            return None
        
        # Calculate Z-score
        z_score = (current_price - mean) / std_dev if std_dev > 0 else 0
        
        # Calculate Bollinger Bands
        bollinger_upper = mean + (self.bollinger_std * std_dev)
        bollinger_lower = mean - (self.bollinger_std * std_dev)
        
        # Determine overbought/oversold
        is_overbought = current_price > bollinger_upper or z_score > self.z_score_entry
        is_oversold = current_price < bollinger_lower or z_score < -self.z_score_entry
        
        indicators = MeanReversionIndicators(
            mean=mean,
            std_dev=std_dev,
            z_score=z_score,
            bollinger_upper=bollinger_upper,
            bollinger_lower=bollinger_lower,
            is_overbought=is_overbought,
            is_oversold=is_oversold,
        )
        
        self._indicators[market_id] = indicators
        return indicators
    
    def _check_hold_period(self, market_id: str, current_time: datetime) -> bool:
        """Check if position has exceeded hold period."""
        entry_time = self._entry_times.get(market_id)
        if not entry_time:
            return False
        
        hold_duration = current_time - entry_time
        max_hold = timedelta(hours=self.hold_period_hours)
        
        return hold_duration > max_hold
    
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio,
    ) -> List[StrategySignal]:
        """Process market update and generate mean reversion signals."""
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
        indicators = self._calculate_indicators(market_id, event.yes_price)
        if not indicators:
            return signals
        
        # Get current position
        position = portfolio.get_position(market_id)
        has_yes_position = position and position.yes_shares > 0
        has_no_position = position and position.no_shares > 0
        
        # Check hold period for existing positions
        if (has_yes_position or has_no_position) and self._check_hold_period(market_id, event.timestamp):
            # Force exit on hold period expiry
            if has_yes_position:
                signal = StrategySignal(
                    signal_type=SignalType.SELL_YES,
                    market_id=market_id,
                    platform=event.platform,
                    timestamp=event.timestamp,
                    confidence=0.6,
                    size=position.yes_shares,
                    reason="Hold period expired",
                )
                signals.append(signal)
                self._record_signal(signal)
                del self._entry_times[market_id]
            
            if has_no_position:
                signal = StrategySignal(
                    signal_type=SignalType.SELL_NO,
                    market_id=market_id,
                    platform=event.platform,
                    timestamp=event.timestamp,
                    confidence=0.6,
                    size=position.no_shares,
                    reason="Hold period expired",
                )
                signals.append(signal)
                self._record_signal(signal)
                del self._entry_times[market_id]
            
            return signals
        
        # Entry signals
        if indicators.is_oversold and not has_yes_position:
            # Price is below mean - buy YES expecting reversion up
            confidence = min(1.0, abs(indicators.z_score) / self.z_score_entry)
            size = self.calculate_position_size(portfolio, event.yes_price, confidence)
            
            signal = StrategySignal(
                signal_type=SignalType.BUY_YES,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=confidence,
                target_price=indicators.mean,  # Target mean reversion
                size=size,
                stop_loss=indicators.bollinger_lower * 0.95,
                take_profit=indicators.mean,
                reason=f"Oversold: Z={indicators.z_score:.2f}, price={event.yes_price:.3f}, mean={indicators.mean:.3f}",
                metadata={
                    "z_score": indicators.z_score,
                    "mean": indicators.mean,
                    "std_dev": indicators.std_dev,
                    "bollinger_lower": indicators.bollinger_lower,
                }
            )
            signals.append(signal)
            self._record_signal(signal)
            self._entry_times[market_id] = event.timestamp
        
        elif indicators.is_overbought and not has_no_position:
            # Price is above mean - buy NO expecting reversion down
            confidence = min(1.0, abs(indicators.z_score) / self.z_score_entry)
            size = self.calculate_position_size(portfolio, event.no_price, confidence)
            
            signal = StrategySignal(
                signal_type=SignalType.BUY_NO,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=confidence,
                target_price=1 - indicators.mean,  # Target mean reversion
                size=size,
                stop_loss=(1 - indicators.bollinger_upper) * 0.95,
                take_profit=1 - indicators.mean,
                reason=f"Overbought: Z={indicators.z_score:.2f}, price={event.yes_price:.3f}, mean={indicators.mean:.3f}",
                metadata={
                    "z_score": indicators.z_score,
                    "mean": indicators.mean,
                    "std_dev": indicators.std_dev,
                    "bollinger_upper": indicators.bollinger_upper,
                }
            )
            signals.append(signal)
            self._record_signal(signal)
            self._entry_times[market_id] = event.timestamp
        
        # Exit signals - price reverted to mean
        if has_yes_position and abs(indicators.z_score) < self.z_score_exit:
            signal = StrategySignal(
                signal_type=SignalType.SELL_YES,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=0.8,
                size=position.yes_shares,
                reason=f"Mean reversion complete: Z={indicators.z_score:.2f}",
            )
            signals.append(signal)
            self._record_signal(signal)
            self._entry_times.pop(market_id, None)
        
        if has_no_position and abs(indicators.z_score) < self.z_score_exit:
            signal = StrategySignal(
                signal_type=SignalType.SELL_NO,
                market_id=market_id,
                platform=event.platform,
                timestamp=event.timestamp,
                confidence=0.8,
                size=position.no_shares,
                reason=f"Mean reversion complete: Z={indicators.z_score:.2f}",
            )
            signals.append(signal)
            self._record_signal(signal)
            self._entry_times.pop(market_id, None)
        
        return signals
    
    def get_statistics(self) -> Dict:
        """Get mean reversion strategy statistics."""
        stats = super().get_statistics()
        
        if self._indicators:
            overbought = sum(1 for i in self._indicators.values() if i.is_overbought)
            oversold = sum(1 for i in self._indicators.values() if i.is_oversold)
            
            z_scores = [i.z_score for i in self._indicators.values()]
            avg_z_score = sum(z_scores) / len(z_scores)
            max_z_score = max(abs(z) for z in z_scores)
            
            stats.update({
                "markets_analyzed": len(self._indicators),
                "overbought_markets": overbought,
                "oversold_markets": oversold,
                "avg_z_score": avg_z_score,
                "max_z_score": max_z_score,
                "active_positions": len(self._entry_times),
            })
        
        return stats
