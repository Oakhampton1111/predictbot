"""
PredictBot Simulation Module
============================

This module provides backtesting and paper trading capabilities for
testing prediction market trading strategies in a safe environment.

Modes:
- backtest: Historical data replay
- paper: Live data with simulated execution
- sandbox: Platform demo/test environments

Usage:
    from simulation import BacktestEngine, PaperTradingEngine
    from simulation.config import SimulationConfig
    
    # Historical backtesting
    config = SimulationConfig.from_yaml("config/simulation.yml")
    engine = BacktestEngine(config)
    engine.add_strategy(my_strategy)
    results = engine.run()
    
    # Paper trading
    paper_engine = PaperTradingEngine(config)
    await paper_engine.start()
    
    # Data collection
    from simulation.data import PolymarketCollector, SQLiteDataStore
    store = SQLiteDataStore("market_data.db")
    collector = PolymarketCollector(config)
"""

from .config import SimulationConfig
from .portfolio import VirtualPortfolio, Position, PortfolioMetrics
from .exchange import SimulatedExchange, FillResult
from .models import (
    MarketSnapshot,
    OrderBookSnapshot,
    TradeEvent,
    MarketResolution,
    Platform,
    OrderSide,
    OrderType,
)
from .backtest import BacktestEngine, BacktestResults
from .paper_trading import PaperTradingEngine

# Data collection submodule
from . import data

__all__ = [
    # Config
    "SimulationConfig",
    # Portfolio
    "VirtualPortfolio",
    "Position",
    "PortfolioMetrics",
    # Exchange
    "SimulatedExchange",
    "FillResult",
    # Models
    "MarketSnapshot",
    "OrderBookSnapshot",
    "TradeEvent",
    "MarketResolution",
    "Platform",
    "OrderSide",
    "OrderType",
    # Engines
    "BacktestEngine",
    "BacktestResults",
    "PaperTradingEngine",
    # Data submodule
    "data",
]

__version__ = "1.0.0"
