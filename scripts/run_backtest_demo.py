#!/usr/bin/env python3
"""
PredictBot Backtest Demo
========================

Demonstrates how to run a backtest with the simulation framework.

Usage:
    python scripts/run_backtest_demo.py
    python scripts/run_backtest_demo.py --config config/simulation.yml
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.config import SimulationConfig
from simulation.models import Platform, OrderSide, OrderType, Order
from simulation.backtest import (
    BacktestEngine,
    TradingStrategy,
    MockDataFeed,
    MarketUpdateEvent
)
from simulation.portfolio import VirtualPortfolio
import uuid


class MeanReversionStrategy(TradingStrategy):
    """
    Mean reversion strategy for prediction markets.
    
    Buys when price drops significantly below recent average,
    sells when price rises above average.
    """
    
    def __init__(
        self,
        name: str = "mean_reversion",
        lookback: int = 20,
        entry_threshold: float = 0.05,
        exit_threshold: float = 0.02,
        position_size: float = 100.0,
        max_positions: int = 5
    ):
        super().__init__(name)
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.position_size = position_size
        self.max_positions = max_positions
        self.price_history: dict = {}
        self.open_positions: set = set()
        
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio
    ) -> list:
        """Generate orders based on mean reversion signals."""
        market_id = event.market_id
        price = event.yes_price
        
        # Update price history
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        self.price_history[market_id].append(price)
        
        # Keep only lookback periods
        if len(self.price_history[market_id]) > self.lookback:
            self.price_history[market_id] = self.price_history[market_id][-self.lookback:]
            
        # Need enough history
        if len(self.price_history[market_id]) < self.lookback:
            return []
            
        # Calculate mean and standard deviation
        prices = self.price_history[market_id]
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_price = variance ** 0.5 if variance > 0 else 0.01
        
        orders = []
        position = portfolio.get_position(market_id)
        
        # Entry signal: price significantly below mean
        deviation = (price - mean_price) / std_price if std_price > 0 else 0
        
        if deviation < -self.entry_threshold * 10:  # More than 0.5 std below
            if market_id not in self.open_positions:
                if len(self.open_positions) < self.max_positions:
                    # Check if we have enough cash
                    cost = self.position_size * price
                    if portfolio.cash >= cost:
                        orders.append(Order(
                            order_id=str(uuid.uuid4()),
                            market_id=market_id,
                            platform=event.platform,
                            side=OrderSide.BUY_YES,
                            order_type=OrderType.MARKET,
                            size=self.position_size
                        ))
                        self.open_positions.add(market_id)
                        
        # Exit signal: price back to or above mean
        elif deviation > self.exit_threshold * 10:  # More than 0.2 std above
            if market_id in self.open_positions and position:
                if position.yes_shares > 0:
                    orders.append(Order(
                        order_id=str(uuid.uuid4()),
                        market_id=market_id,
                        platform=event.platform,
                        side=OrderSide.SELL_YES,
                        order_type=OrderType.MARKET,
                        size=position.yes_shares
                    ))
                    self.open_positions.discard(market_id)
                    
        return orders


class MomentumStrategy(TradingStrategy):
    """
    Momentum strategy that follows price trends.
    
    Buys when price is trending up, sells when trending down.
    """
    
    def __init__(
        self,
        name: str = "momentum",
        short_period: int = 5,
        long_period: int = 20,
        position_size: float = 100.0
    ):
        super().__init__(name)
        self.short_period = short_period
        self.long_period = long_period
        self.position_size = position_size
        self.price_history: dict = {}
        
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio
    ) -> list:
        """Generate orders based on momentum signals."""
        market_id = event.market_id
        price = event.yes_price
        
        # Update price history
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        self.price_history[market_id].append(price)
        
        # Keep only long_period prices
        if len(self.price_history[market_id]) > self.long_period:
            self.price_history[market_id] = self.price_history[market_id][-self.long_period:]
            
        # Need enough history
        if len(self.price_history[market_id]) < self.long_period:
            return []
            
        prices = self.price_history[market_id]
        
        # Calculate short and long moving averages
        short_ma = sum(prices[-self.short_period:]) / self.short_period
        long_ma = sum(prices) / len(prices)
        
        orders = []
        position = portfolio.get_position(market_id)
        
        # Buy signal: short MA crosses above long MA
        if short_ma > long_ma * 1.02:  # 2% above
            if position is None or position.yes_shares == 0:
                cost = self.position_size * price
                if portfolio.cash >= cost:
                    orders.append(Order(
                        order_id=str(uuid.uuid4()),
                        market_id=market_id,
                        platform=event.platform,
                        side=OrderSide.BUY_YES,
                        order_type=OrderType.MARKET,
                        size=self.position_size
                    ))
                    
        # Sell signal: short MA crosses below long MA
        elif short_ma < long_ma * 0.98:  # 2% below
            if position and position.yes_shares > 0:
                orders.append(Order(
                    order_id=str(uuid.uuid4()),
                    market_id=market_id,
                    platform=event.platform,
                    side=OrderSide.SELL_YES,
                    order_type=OrderType.MARKET,
                    size=position.yes_shares
                ))
                
        return orders


def run_backtest(config_path: str = None):
    """Run a backtest with demo strategies."""
    
    print("=" * 60)
    print("PredictBot Backtest Demo")
    print("=" * 60)
    
    # Load or create configuration
    if config_path and os.path.exists(config_path):
        print(f"Loading configuration from {config_path}")
        config = SimulationConfig.from_yaml(config_path)
    else:
        print("Using default configuration")
        config = SimulationConfig(mode="backtest")
        config.backtest.start_date = datetime.now() - timedelta(days=90)
        config.backtest.end_date = datetime.now()
        config.backtest.initial_capital = 10000
        config.backtest.platforms = [Platform.POLYMARKET, Platform.KALSHI]
        
    print(f"\nBacktest Period: {config.backtest.start_date.date()} to {config.backtest.end_date.date()}")
    print(f"Initial Capital: ${config.backtest.initial_capital:,.2f}")
    print(f"Platforms: {[p.value for p in config.backtest.platforms]}")
    
    # Create backtest engine
    engine = BacktestEngine(config)
    
    # Add strategies
    print("\nAdding strategies...")
    
    mean_reversion = MeanReversionStrategy(
        name="mean_reversion",
        lookback=20,
        entry_threshold=0.05,
        exit_threshold=0.02,
        position_size=100,
        max_positions=5
    )
    engine.add_strategy(mean_reversion)
    
    momentum = MomentumStrategy(
        name="momentum",
        short_period=5,
        long_period=20,
        position_size=100
    )
    engine.add_strategy(momentum)
    
    # Create mock data feed
    print("\nCreating mock data feed...")
    data_feed = MockDataFeed(
        start_date=config.backtest.start_date,
        end_date=config.backtest.end_date,
        platforms=config.backtest.platforms,
        num_markets=15,
        update_interval_minutes=5
    )
    engine.set_data_feed(data_feed)
    
    # Run backtest
    print("\nRunning backtest...")
    print("-" * 60)
    
    results = engine.run()
    
    # Print results
    results.print_summary()
    
    # Save results
    output_dir = config.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    results_path = os.path.join(output_dir, "backtest_results.json")
    results.save(results_path)
    print(f"\nResults saved to: {results_path}")
    
    # Print strategy breakdown
    if results.by_strategy:
        print("\nStrategy Breakdown:")
        print("-" * 40)
        for strategy_name, stats in results.by_strategy.items():
            print(f"  {strategy_name}:")
            print(f"    Trades: {stats['trades']}")
            print(f"    Volume: ${stats['volume']:,.2f}")
            print(f"    Fees: ${stats['fees']:.2f}")
            
    # Print platform breakdown
    if results.by_platform:
        print("\nPlatform Breakdown:")
        print("-" * 40)
        for platform_name, stats in results.by_platform.items():
            print(f"  {platform_name}:")
            print(f"    Trades: {stats['trades']}")
            print(f"    Volume: ${stats['volume']:,.2f}")
            print(f"    Fees: ${stats['fees']:.2f}")
            
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run PredictBot backtest demo"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to simulation configuration file"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_backtest(args.config)
        
        # Return exit code based on results
        if results.total_return >= 0:
            print("\n✅ Backtest completed successfully with positive returns!")
            sys.exit(0)
        else:
            print("\n⚠️ Backtest completed with negative returns")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
