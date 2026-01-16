"""
PredictBot Simulation - Spike Detector Strategy Adapter
========================================================

Adapter for spike detection strategy.
Detects sudden price movements and trades on momentum or mean reversion.
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
class PricePoint:
    """A single price observation."""
    timestamp: datetime
    price: float
    volume: float


@dataclass
class SpikeEvent:
    """Detected spike event."""
    market_id: str
    platform: Platform
    timestamp: datetime
    price_before: float
    price_after: float
    change_pct: float
    volume: float
    direction: str  # "up" or "down"


class SpikeDetectorAdapter(BaseStrategyAdapter):
    """
    Spike detection strategy.
    
    Monitors price movements and detects sudden spikes.
    Can trade either:
    - Momentum: Follow the spike direction
    - Mean reversion: Bet on price returning to normal
    
    Based on polymarket_spike module logic.
    """
    
    def __init__(
        self,
        spike_threshold: float = 0.05,  # 5% price change
        lookback_periods: int = 10,
        min_volume_spike: float = 2.0,  # Volume must be 2x normal
        strategy_mode: str = "mean_reversion",  # or "momentum"
        cooldown_minutes: int = 30,
        max_position_per_market: float = 200.0,
        platforms: Optional[List[Platform]] = None,
    ):
        """
        Initialize spike detector.
        
        Args:
            spike_threshold: Minimum price change to trigger
            lookback_periods: Number of periods to analyze
            min_volume_spike: Minimum volume multiplier
            strategy_mode: "momentum" or "mean_reversion"
            cooldown_minutes: Minutes to wait between trades
            max_position_per_market: Maximum position size
            platforms: Platforms to trade on
        """
        super().__init__(
            name="SpikeDetectorStrategy",
            platforms=platforms,
            position_size=max_position_per_market,
        )
        
        self.spike_threshold = spike_threshold
        self.lookback_periods = lookback_periods
        self.min_volume_spike = min_volume_spike
        self.strategy_mode = strategy_mode
        self.cooldown_minutes = cooldown_minutes
        self.max_position_per_market = max_position_per_market
        
        # Price history per market
        self._price_history: Dict[str, Deque[PricePoint]] = {}
        
        # Track detected spikes
        self._spikes: List[SpikeEvent] = []
        
        # Cooldown tracking
        self._last_trade_time: Dict[str, datetime] = {}
    
    def _get_price_history(self, market_id: str) -> Deque[PricePoint]:
        """Get or create price history for a market."""
        if market_id not in self._price_history:
            self._price_history[market_id] = deque(maxlen=self.lookback_periods * 2)
        return self._price_history[market_id]
    
    def _calculate_average_price(self, history: Deque[PricePoint]) -> float:
        """Calculate average price from history."""
        if not history:
            return 0.5
        return sum(p.price for p in history) / len(history)
    
    def _calculate_average_volume(self, history: Deque[PricePoint]) -> float:
        """Calculate average volume from history."""
        if not history:
            return 0
        return sum(p.volume for p in history) / len(history)
    
    def _calculate_volatility(self, history: Deque[PricePoint]) -> float:
        """Calculate price volatility (standard deviation)."""
        if len(history) < 2:
            return 0
        
        avg = self._calculate_average_price(history)
        variance = sum((p.price - avg) ** 2 for p in history) / len(history)
        return variance ** 0.5
    
    def _detect_spike(
        self,
        market_id: str,
        current_price: float,
        current_volume: float,
        timestamp: datetime,
    ) -> Optional[SpikeEvent]:
        """
        Detect if current price represents a spike.
        
        Returns:
            SpikeEvent if spike detected, None otherwise
        """
        history = self._get_price_history(market_id)
        
        if len(history) < self.lookback_periods:
            return None
        
        avg_price = self._calculate_average_price(history)
        avg_volume = self._calculate_average_volume(history)
        
        # Calculate price change
        price_change = (current_price - avg_price) / avg_price if avg_price > 0 else 0
        
        # Check if this is a spike
        if abs(price_change) < self.spike_threshold:
            return None
        
        # Check volume spike
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        if volume_ratio < self.min_volume_spike:
            return None
        
        # Determine direction
        direction = "up" if price_change > 0 else "down"
        
        return SpikeEvent(
            market_id=market_id,
            platform=Platform.POLYMARKET,  # Will be set by caller
            timestamp=timestamp,
            price_before=avg_price,
            price_after=current_price,
            change_pct=price_change,
            volume=current_volume,
            direction=direction,
        )
    
    def _is_in_cooldown(self, market_id: str, timestamp: datetime) -> bool:
        """Check if market is in cooldown period."""
        last_trade = self._last_trade_time.get(market_id)
        if not last_trade:
            return False
        
        cooldown_end = last_trade + timedelta(minutes=self.cooldown_minutes)
        return timestamp < cooldown_end
    
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio,
    ) -> List[StrategySignal]:
        """Process market update and detect spikes."""
        signals = []
        
        market_id = event.market_id
        
        # Add to price history
        history = self._get_price_history(market_id)
        history.append(PricePoint(
            timestamp=event.timestamp,
            price=event.yes_price,
            volume=event.volume,
        ))
        
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
        
        # Check cooldown
        if self._is_in_cooldown(market_id, event.timestamp):
            return signals
        
        # Detect spike
        spike = self._detect_spike(
            market_id,
            event.yes_price,
            event.volume,
            event.timestamp,
        )
        
        if not spike:
            return signals
        
        # Update spike platform
        spike.platform = event.platform
        self._spikes.append(spike)
        
        logger.info(
            f"Spike detected: {market_id} {spike.direction} "
            f"{spike.change_pct:.1%} (vol: {spike.volume:.0f})"
        )
        
        # Check if we should trade
        if not self.should_trade(market_id, portfolio):
            return signals
        
        # Generate signal based on strategy mode
        if self.strategy_mode == "momentum":
            # Follow the spike
            signal_type = SignalType.BUY_YES if spike.direction == "up" else SignalType.BUY_NO
            reason = f"Momentum: spike {spike.direction} {spike.change_pct:.1%}"
        else:
            # Mean reversion - bet against the spike
            signal_type = SignalType.BUY_NO if spike.direction == "up" else SignalType.BUY_YES
            reason = f"Mean reversion: spike {spike.direction} {spike.change_pct:.1%}"
        
        # Calculate confidence based on spike magnitude
        confidence = min(1.0, abs(spike.change_pct) / (self.spike_threshold * 2))
        
        # Calculate position size
        size = self.calculate_position_size(
            portfolio,
            event.yes_price if signal_type in [SignalType.BUY_YES, SignalType.SELL_YES] else event.no_price,
            confidence=confidence,
        )
        
        signal = StrategySignal(
            signal_type=signal_type,
            market_id=market_id,
            platform=event.platform,
            timestamp=event.timestamp,
            confidence=confidence,
            target_price=spike.price_before if self.strategy_mode == "mean_reversion" else None,
            size=size,
            stop_loss=spike.price_after * 0.9 if spike.direction == "up" else spike.price_after * 1.1,
            take_profit=spike.price_before if self.strategy_mode == "mean_reversion" else None,
            reason=reason,
            metadata={
                "spike": {
                    "direction": spike.direction,
                    "change_pct": spike.change_pct,
                    "volume": spike.volume,
                    "price_before": spike.price_before,
                    "price_after": spike.price_after,
                }
            }
        )
        
        signals.append(signal)
        self._record_signal(signal)
        self._last_trade_time[market_id] = event.timestamp
        
        return signals
    
    def get_statistics(self) -> Dict:
        """Get spike detector statistics."""
        stats = super().get_statistics()
        
        if self._spikes:
            up_spikes = [s for s in self._spikes if s.direction == "up"]
            down_spikes = [s for s in self._spikes if s.direction == "down"]
            
            stats.update({
                "total_spikes": len(self._spikes),
                "up_spikes": len(up_spikes),
                "down_spikes": len(down_spikes),
                "avg_spike_magnitude": sum(abs(s.change_pct) for s in self._spikes) / len(self._spikes),
                "max_spike": max(abs(s.change_pct) for s in self._spikes),
                "strategy_mode": self.strategy_mode,
            })
        
        return stats
