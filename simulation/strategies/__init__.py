"""
PredictBot Simulation - Strategy Adapters
==========================================

This module provides adapters that wrap existing PredictBot trading strategies
to work with the simulation/backtesting framework.

Adapters:
- BaseStrategyAdapter: Abstract base for all adapters
- ArbitrageAdapter: Wraps polymarket_arb strategy
- AIOrchestatorAdapter: Wraps ai_orchestrator strategy
- SpikeDetectorAdapter: Wraps polymarket_spike strategy
- MarketMakerAdapter: Wraps manifold_mm strategy

Usage:
    from simulation.strategies import ArbitrageAdapter
    from simulation import BacktestEngine
    
    engine = BacktestEngine(config)
    engine.add_strategy(ArbitrageAdapter(min_spread=0.02))
    results = engine.run()
"""

from .base import BaseStrategyAdapter, StrategySignal, SignalType
from .arbitrage import ArbitrageAdapter
from .spike_detector import SpikeDetectorAdapter
from .market_maker import MarketMakerAdapter
from .momentum import MomentumAdapter
from .mean_reversion import MeanReversionAdapter

__all__ = [
    "BaseStrategyAdapter",
    "StrategySignal",
    "SignalType",
    "ArbitrageAdapter",
    "SpikeDetectorAdapter",
    "MarketMakerAdapter",
    "MomentumAdapter",
    "MeanReversionAdapter",
]
