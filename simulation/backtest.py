"""
PredictBot Simulation - Backtest Engine
========================================

Event-driven backtesting engine for prediction market strategies.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Generator
from pathlib import Path
import json
import logging
import heapq
import uuid

from .config import SimulationConfig, BacktestConfig
from .models import (
    Platform,
    OrderSide,
    OrderType,
    Order,
    MarketSnapshot,
    MarketResolution,
    ResolutionOutcome,
    SimulationEvent,
    MarketUpdateEvent,
    ResolutionEvent
)
from .exchange import (
    SimulatedExchange,
    FillModel,
    RealisticFillModel,
    LatencyModel,
    FeeModel,
    FillResult
)
from .portfolio import VirtualPortfolio, PortfolioMetrics, Trade

logger = logging.getLogger(__name__)


@dataclass
class BacktestResults:
    """Results from a backtest run."""
    # Configuration
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime = field(default_factory=datetime.utcnow)
    initial_capital: float = 0.0
    
    # Performance
    final_value: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    
    # Metrics
    metrics: Optional[PortfolioMetrics] = None
    
    # Trade history
    trades: List[Dict] = field(default_factory=list)
    resolutions: List[Dict] = field(default_factory=list)
    
    # Equity curve
    equity_curve: List[tuple] = field(default_factory=list)
    
    # Strategy breakdown
    by_strategy: Dict[str, Dict] = field(default_factory=dict)
    by_platform: Dict[str, Dict] = field(default_factory=dict)
    
    # Execution stats
    total_orders: int = 0
    filled_orders: int = 0
    rejected_orders: int = 0
    total_fees: float = 0.0
    avg_slippage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "total_return_pct": self.total_return_pct,
            "metrics": {
                "sharpe_ratio": self.metrics.sharpe_ratio if self.metrics else 0,
                "max_drawdown_pct": self.metrics.max_drawdown_pct if self.metrics else 0,
                "win_rate": self.metrics.win_rate if self.metrics else 0,
                "profit_factor": self.metrics.profit_factor if self.metrics else 0,
                "total_trades": self.metrics.total_trades if self.metrics else 0
            },
            "execution_stats": {
                "total_orders": self.total_orders,
                "filled_orders": self.filled_orders,
                "rejected_orders": self.rejected_orders,
                "total_fees": self.total_fees,
                "avg_slippage": self.avg_slippage
            },
            "by_platform": self.by_platform,
            "by_strategy": self.by_strategy
        }
    
    def save(self, path: str):
        """Save results to JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    def print_summary(self):
        """Print summary to console."""
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Value: ${self.final_value:,.2f}")
        print(f"Total Return: ${self.total_return:,.2f} ({self.total_return_pct:.2%})")
        print("-" * 60)
        
        if self.metrics:
            print("PERFORMANCE METRICS")
            print(f"  Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}")
            print(f"  Sortino Ratio: {self.metrics.sortino_ratio:.2f}")
            print(f"  Max Drawdown: {self.metrics.max_drawdown_pct:.2%}")
            print(f"  Win Rate: {self.metrics.win_rate:.2%}")
            print(f"  Profit Factor: {self.metrics.profit_factor:.2f}")
            print(f"  Expectancy: ${self.metrics.expectancy:.2f}")
            print("-" * 60)
            
        print("EXECUTION STATS")
        print(f"  Total Orders: {self.total_orders}")
        print(f"  Filled: {self.filled_orders} ({self.filled_orders/max(self.total_orders,1):.1%})")
        print(f"  Rejected: {self.rejected_orders}")
        print(f"  Total Fees: ${self.total_fees:.2f}")
        print(f"  Avg Slippage: {self.avg_slippage:.4f}")
        print("=" * 60 + "\n")


class TradingStrategy:
    """
    Base class for trading strategies.
    
    Strategies should inherit from this and implement on_market_update.
    """
    
    def __init__(self, name: str = "base_strategy"):
        self.name = name
        self.positions: Dict[str, Any] = {}
        
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio
    ) -> List[Order]:
        """
        Called when market data updates.
        
        Args:
            event: Market update event
            portfolio: Current portfolio state
            
        Returns:
            List of orders to submit
        """
        return []
    
    def on_resolution(
        self,
        event: ResolutionEvent,
        portfolio: VirtualPortfolio
    ):
        """
        Called when a market resolves.
        
        Args:
            event: Resolution event
            portfolio: Current portfolio state
        """
        pass


class DataFeed:
    """
    Base class for data feeds.
    
    Provides historical market data for backtesting.
    """
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: List[Platform]
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.platforms = platforms
        
    def get_events(self) -> Generator[SimulationEvent, None, None]:
        """
        Generate events in chronological order.
        
        Yields:
            SimulationEvent objects
        """
        raise NotImplementedError


class MockDataFeed(DataFeed):
    """
    Mock data feed for testing.
    
    Generates synthetic market data.
    """
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: List[Platform],
        num_markets: int = 10,
        update_interval_minutes: int = 5
    ):
        super().__init__(start_date, end_date, platforms)
        self.num_markets = num_markets
        self.update_interval = timedelta(minutes=update_interval_minutes)
        
    def get_events(self) -> Generator[SimulationEvent, None, None]:
        """Generate mock market events."""
        import random
        
        # Create mock markets
        markets = []
        for i in range(self.num_markets):
            platform = random.choice(self.platforms)
            resolution_date = self.start_date + timedelta(
                days=random.randint(7, 90)
            )
            markets.append({
                "market_id": f"mock_market_{i}",
                "platform": platform,
                "question": f"Mock Market Question {i}?",
                "yes_price": random.uniform(0.3, 0.7),
                "resolution_date": resolution_date,
                "resolved": False
            })
            
        # Generate events
        current_time = self.start_date
        
        while current_time <= self.end_date:
            for market in markets:
                if market["resolved"]:
                    continue
                    
                # Check for resolution
                if current_time >= market["resolution_date"]:
                    outcome = ResolutionOutcome.YES if random.random() > 0.5 else ResolutionOutcome.NO
                    yield ResolutionEvent(
                        timestamp=current_time,
                        resolution=MarketResolution(
                            market_id=market["market_id"],
                            platform=market["platform"],
                            timestamp=current_time,
                            outcome=outcome,
                            question=market["question"]
                        )
                    )
                    market["resolved"] = True
                else:
                    # Price update with random walk
                    price_change = random.gauss(0, 0.02)
                    market["yes_price"] = max(0.01, min(0.99, 
                        market["yes_price"] + price_change
                    ))
                    
                    yield MarketUpdateEvent(
                        timestamp=current_time,
                        market_id=market["market_id"],
                        platform=market["platform"],
                        yes_price=market["yes_price"],
                        no_price=1 - market["yes_price"],
                        volume=random.uniform(100, 10000)
                    )
                    
            current_time += self.update_interval


class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    Replays historical data through trading strategies and
    simulates order execution.
    """
    
    def __init__(self, config: SimulationConfig):
        """
        Initialize backtest engine.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self.bt_config = config.backtest
        
        # Initialize components
        self._init_exchange()
        self.portfolio = VirtualPortfolio(self.bt_config.initial_capital)
        self.strategies: List[TradingStrategy] = []
        self.data_feed: Optional[DataFeed] = None
        
        # Results tracking
        self.results = BacktestResults(
            start_date=self.bt_config.start_date,
            end_date=self.bt_config.end_date,
            initial_capital=self.bt_config.initial_capital
        )
        
        # State
        self.current_time: Optional[datetime] = None
        self._last_equity_record: Optional[datetime] = None
        self._slippage_sum = 0.0
        self._slippage_count = 0
        
    def _init_exchange(self):
        """Initialize simulated exchange from config."""
        fill_config = self.config.exchange.fill_model
        latency_config = self.config.exchange.latency_model
        
        # Create fill model
        if fill_config.model_type == "realistic":
            fill_model = RealisticFillModel(
                prob_fill_on_limit=fill_config.prob_fill_on_limit,
                prob_slippage=fill_config.prob_slippage,
                max_slippage_bps=fill_config.max_slippage_bps,
                price_impact_factor=fill_config.price_impact_factor,
                random_seed=fill_config.random_seed
            )
        else:
            fill_model = FillModel(
                prob_fill_on_limit=fill_config.prob_fill_on_limit,
                prob_slippage=fill_config.prob_slippage,
                max_slippage_bps=fill_config.max_slippage_bps,
                random_seed=fill_config.random_seed
            )
            
        # Create latency model
        latency_model = LatencyModel(
            mean_ms=latency_config.mean_ms,
            std_ms=latency_config.std_ms,
            min_ms=latency_config.min_ms,
            max_ms=latency_config.max_ms,
            random_seed=latency_config.random_seed
        )
        
        # Create fee model
        fee_model = FeeModel()
        
        self.exchange = SimulatedExchange(
            fill_model=fill_model,
            latency_model=latency_model,
            fee_model=fee_model
        )
        
    def add_strategy(self, strategy: TradingStrategy):
        """
        Add a trading strategy to the backtest.
        
        Args:
            strategy: Strategy instance
        """
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")
        
    def set_data_feed(self, data_feed: DataFeed):
        """
        Set the data feed for backtesting.
        
        Args:
            data_feed: DataFeed instance
        """
        self.data_feed = data_feed
        
    def run(self) -> BacktestResults:
        """
        Execute the backtest.
        
        Returns:
            BacktestResults with performance data
        """
        if not self.strategies:
            raise ValueError("No strategies added to backtest")
            
        if self.data_feed is None:
            # Use mock data feed if none provided
            logger.warning("No data feed provided, using mock data")
            self.data_feed = MockDataFeed(
                start_date=self.bt_config.start_date,
                end_date=self.bt_config.end_date,
                platforms=self.bt_config.platforms
            )
            
        logger.info(f"Starting backtest from {self.bt_config.start_date} to {self.bt_config.end_date}")
        logger.info(f"Initial capital: ${self.bt_config.initial_capital:,.2f}")
        logger.info(f"Strategies: {[s.name for s in self.strategies]}")
        
        # Process events
        event_count = 0
        for event in self.data_feed.get_events():
            self.current_time = event.timestamp
            self._process_event(event)
            event_count += 1
            
            # Record equity periodically
            self._maybe_record_equity()
            
            # Progress logging
            if event_count % 10000 == 0:
                logger.debug(f"Processed {event_count} events, current time: {self.current_time}")
                
        # Final equity record
        self.portfolio.record_equity(self.current_time or datetime.utcnow())
        
        # Calculate final results
        self._finalize_results()
        
        logger.info(f"Backtest complete. Processed {event_count} events.")
        
        return self.results
    
    def _process_event(self, event: SimulationEvent):
        """Process a single simulation event."""
        if isinstance(event, MarketUpdateEvent):
            self._handle_market_update(event)
        elif isinstance(event, ResolutionEvent):
            self._handle_resolution(event)
            
    def _handle_market_update(self, event: MarketUpdateEvent):
        """Handle market price update."""
        # Update exchange state
        snapshot = MarketSnapshot(
            market_id=event.market_id,
            platform=event.platform,
            timestamp=event.timestamp,
            question="",
            yes_price=event.yes_price,
            no_price=event.no_price,
            volume_24h=event.volume
        )
        self.exchange.update_market(snapshot)
        
        # Let strategies react
        for strategy in self.strategies:
            orders = strategy.on_market_update(event, self.portfolio)
            
            for order in orders:
                self._execute_order(order, strategy.name)
                
    def _handle_resolution(self, event: ResolutionEvent):
        """Handle market resolution."""
        resolution = event.resolution
        
        # Resolve position in portfolio
        pnl = self.portfolio.resolve_position(
            market_id=resolution.market_id,
            outcome=resolution.outcome,
            question=resolution.question
        )
        
        # Record resolution
        self.results.resolutions.append({
            "market_id": resolution.market_id,
            "platform": resolution.platform.value,
            "outcome": resolution.outcome.value,
            "pnl": pnl,
            "timestamp": resolution.timestamp.isoformat()
        })
        
        # Notify strategies
        for strategy in self.strategies:
            strategy.on_resolution(event, self.portfolio)
            
        logger.debug(f"Market {resolution.market_id} resolved {resolution.outcome.value}, PnL: ${pnl:.2f}")
        
    def _execute_order(self, order: Order, strategy_name: str):
        """Execute an order through the simulated exchange."""
        self.results.total_orders += 1
        
        # Submit to exchange
        result = self.exchange.submit_order(order)
        
        if result.filled:
            self.results.filled_orders += 1
            self.results.total_fees += result.fees
            self._slippage_sum += result.slippage
            self._slippage_count += 1
            
            # Update portfolio
            self.portfolio.execute_trade(
                trade_id=str(uuid.uuid4()),
                market_id=order.market_id,
                platform=order.platform,
                side=order.side,
                size=result.filled_size,
                price=result.fill_price,
                fees=result.fees
            )
            
            # Record trade
            self.results.trades.append({
                "order_id": order.order_id,
                "market_id": order.market_id,
                "platform": order.platform.value,
                "side": order.side.value,
                "size": result.filled_size,
                "price": result.fill_price,
                "fees": result.fees,
                "slippage": result.slippage,
                "strategy": strategy_name,
                "timestamp": self.current_time.isoformat() if self.current_time else None
            })
            
            # Update strategy breakdown
            if strategy_name not in self.results.by_strategy:
                self.results.by_strategy[strategy_name] = {
                    "trades": 0, "volume": 0, "fees": 0
                }
            self.results.by_strategy[strategy_name]["trades"] += 1
            self.results.by_strategy[strategy_name]["volume"] += result.filled_size * result.fill_price
            self.results.by_strategy[strategy_name]["fees"] += result.fees
            
            # Update platform breakdown
            platform_name = order.platform.value
            if platform_name not in self.results.by_platform:
                self.results.by_platform[platform_name] = {
                    "trades": 0, "volume": 0, "fees": 0
                }
            self.results.by_platform[platform_name]["trades"] += 1
            self.results.by_platform[platform_name]["volume"] += result.filled_size * result.fill_price
            self.results.by_platform[platform_name]["fees"] += result.fees
            
        else:
            self.results.rejected_orders += 1
            logger.debug(f"Order rejected: {result.reason}")
            
    def _maybe_record_equity(self):
        """Record equity if enough time has passed."""
        if self.current_time is None:
            return
            
        interval = timedelta(minutes=self.bt_config.record_equity_interval)
        
        if self._last_equity_record is None or \
           self.current_time - self._last_equity_record >= interval:
            # Get current prices for unrealized P&L
            current_prices = {
                market_id: snapshot.yes_price
                for market_id, snapshot in self.exchange.markets.items()
            }
            self.portfolio.record_equity(self.current_time, current_prices)
            self._last_equity_record = self.current_time
            
    def _finalize_results(self):
        """Calculate final results."""
        # Get current prices
        current_prices = {
            market_id: snapshot.yes_price
            for market_id, snapshot in self.exchange.markets.items()
        }
        
        # Final portfolio value
        self.results.final_value = self.portfolio.get_portfolio_value(current_prices)
        self.results.total_return = self.results.final_value - self.bt_config.initial_capital
        self.results.total_return_pct = self.results.total_return / self.bt_config.initial_capital
        
        # Get portfolio metrics
        self.results.metrics = self.portfolio.get_metrics()
        
        # Equity curve
        self.results.equity_curve = list(self.portfolio.equity_curve)
        
        # Average slippage
        if self._slippage_count > 0:
            self.results.avg_slippage = self._slippage_sum / self._slippage_count
            
    def reset(self):
        """Reset engine for another run."""
        self.portfolio.reset()
        self.exchange.reset()
        self.results = BacktestResults(
            start_date=self.bt_config.start_date,
            end_date=self.bt_config.end_date,
            initial_capital=self.bt_config.initial_capital
        )
        self.current_time = None
        self._last_equity_record = None
        self._slippage_sum = 0.0
        self._slippage_count = 0


# Example strategy for testing
class SimpleMovingAverageStrategy(TradingStrategy):
    """
    Simple strategy that buys when price is below moving average
    and sells when above.
    """
    
    def __init__(
        self,
        name: str = "sma_strategy",
        lookback_periods: int = 20,
        position_size: float = 100.0,
        threshold: float = 0.05
    ):
        super().__init__(name)
        self.lookback = lookback_periods
        self.position_size = position_size
        self.threshold = threshold
        self.price_history: Dict[str, List[float]] = {}
        
    def on_market_update(
        self,
        event: MarketUpdateEvent,
        portfolio: VirtualPortfolio
    ) -> List[Order]:
        """Generate orders based on SMA crossover."""
        market_id = event.market_id
        current_price = event.yes_price
        
        # Update price history
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        self.price_history[market_id].append(current_price)
        
        # Keep only lookback periods
        if len(self.price_history[market_id]) > self.lookback:
            self.price_history[market_id] = self.price_history[market_id][-self.lookback:]
            
        # Need enough history
        if len(self.price_history[market_id]) < self.lookback:
            return []
            
        # Calculate SMA
        sma = sum(self.price_history[market_id]) / len(self.price_history[market_id])
        
        orders = []
        position = portfolio.get_position(market_id)
        
        # Buy signal: price below SMA by threshold
        if current_price < sma * (1 - self.threshold):
            if position is None or position.yes_shares < self.position_size:
                orders.append(Order(
                    order_id=str(uuid.uuid4()),
                    market_id=market_id,
                    platform=event.platform,
                    side=OrderSide.BUY_YES,
                    order_type=OrderType.MARKET,
                    size=self.position_size
                ))
                
        # Sell signal: price above SMA by threshold
        elif current_price > sma * (1 + self.threshold):
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
