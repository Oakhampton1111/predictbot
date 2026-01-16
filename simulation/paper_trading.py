"""
PredictBot Simulation - Paper Trading Engine
=============================================

Live market data with simulated execution for real-time testing.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import uuid

from .config import SimulationConfig, PaperTradingConfig
from .models import (
    Platform,
    OrderSide,
    OrderType,
    Order,
    MarketSnapshot,
    MarketResolution,
    ResolutionOutcome,
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
from .portfolio import VirtualPortfolio, PortfolioMetrics
from .backtest import TradingStrategy, BacktestResults

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """
    Base class for live market data providers.
    
    Implementations should connect to real platform APIs.
    """
    
    def __init__(self, platform: Platform):
        self.platform = platform
        self.connected = False
        self._callbacks: List[Callable] = []
        
    async def connect(self):
        """Connect to data source."""
        raise NotImplementedError
        
    async def disconnect(self):
        """Disconnect from data source."""
        raise NotImplementedError
        
    def on_update(self, callback: Callable):
        """Register callback for market updates."""
        self._callbacks.append(callback)
        
    async def _emit_update(self, event: MarketUpdateEvent):
        """Emit update to all callbacks."""
        for callback in self._callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)


class MockMarketDataProvider(MarketDataProvider):
    """
    Mock data provider for testing.
    
    Generates synthetic real-time data.
    """
    
    def __init__(
        self,
        platform: Platform,
        num_markets: int = 5,
        update_interval: float = 1.0
    ):
        super().__init__(platform)
        self.num_markets = num_markets
        self.update_interval = update_interval
        self._running = False
        self._markets: Dict[str, Dict] = {}
        
    async def connect(self):
        """Start generating mock data."""
        import random
        
        # Initialize mock markets
        for i in range(self.num_markets):
            market_id = f"{self.platform.value}_mock_{i}"
            self._markets[market_id] = {
                "market_id": market_id,
                "yes_price": random.uniform(0.3, 0.7),
                "volume": random.uniform(1000, 10000)
            }
            
        self.connected = True
        self._running = True
        
        # Start update loop
        asyncio.create_task(self._update_loop())
        logger.info(f"Mock data provider connected for {self.platform.value}")
        
    async def disconnect(self):
        """Stop generating data."""
        self._running = False
        self.connected = False
        logger.info(f"Mock data provider disconnected for {self.platform.value}")
        
    async def _update_loop(self):
        """Generate periodic updates."""
        import random
        
        while self._running:
            for market_id, market in self._markets.items():
                # Random walk price
                price_change = random.gauss(0, 0.01)
                market["yes_price"] = max(0.01, min(0.99,
                    market["yes_price"] + price_change
                ))
                
                # Create update event
                event = MarketUpdateEvent(
                    timestamp=datetime.utcnow(),
                    market_id=market_id,
                    platform=self.platform,
                    yes_price=market["yes_price"],
                    no_price=1 - market["yes_price"],
                    volume=market["volume"]
                )
                
                await self._emit_update(event)
                
            await asyncio.sleep(self.update_interval)


class PaperTradingEngine:
    """
    Paper trading engine with live market data.
    
    Connects to real market data feeds but executes trades
    on a simulated exchange.
    """
    
    def __init__(self, config: SimulationConfig):
        """
        Initialize paper trading engine.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self.pt_config = config.paper_trading
        
        # Initialize components
        self._init_exchange()
        self.portfolio = VirtualPortfolio(self.pt_config.initial_capital)
        self.strategies: List[TradingStrategy] = []
        self.data_providers: Dict[Platform, MarketDataProvider] = {}
        
        # State
        self._running = False
        self._start_time: Optional[datetime] = None
        self._event_count = 0
        
        # Results tracking
        self.results = BacktestResults(
            initial_capital=self.pt_config.initial_capital
        )
        
    def _init_exchange(self):
        """Initialize simulated exchange."""
        fill_config = self.config.exchange.fill_model
        latency_config = self.config.exchange.latency_model
        
        if fill_config.model_type == "realistic":
            fill_model = RealisticFillModel(
                prob_fill_on_limit=fill_config.prob_fill_on_limit,
                prob_slippage=fill_config.prob_slippage,
                max_slippage_bps=fill_config.max_slippage_bps,
                random_seed=fill_config.random_seed
            )
        else:
            fill_model = FillModel(
                prob_fill_on_limit=fill_config.prob_fill_on_limit,
                prob_slippage=fill_config.prob_slippage,
                max_slippage_bps=fill_config.max_slippage_bps,
                random_seed=fill_config.random_seed
            )
            
        latency_model = LatencyModel(
            mean_ms=latency_config.mean_ms,
            std_ms=latency_config.std_ms,
            random_seed=latency_config.random_seed
        )
        
        self.exchange = SimulatedExchange(
            fill_model=fill_model,
            latency_model=latency_model,
            fee_model=FeeModel()
        )
        
    def add_strategy(self, strategy: TradingStrategy):
        """Add a trading strategy."""
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")
        
    def add_data_provider(self, provider: MarketDataProvider):
        """Add a market data provider."""
        self.data_providers[provider.platform] = provider
        provider.on_update(self._on_market_update)
        logger.info(f"Added data provider for {provider.platform.value}")
        
    async def start(self):
        """Start paper trading session."""
        if self._running:
            logger.warning("Paper trading already running")
            return
            
        logger.info("Starting paper trading session...")
        logger.info(f"Initial capital: ${self.pt_config.initial_capital:,.2f}")
        logger.info(f"Strategies: {[s.name for s in self.strategies]}")
        
        self._running = True
        self._start_time = datetime.utcnow()
        self.results.start_date = self._start_time
        
        # Connect data providers
        if not self.data_providers:
            # Use mock providers if none configured
            logger.warning("No data providers configured, using mock data")
            for platform in self.pt_config.platforms:
                provider = MockMarketDataProvider(
                    platform=platform,
                    update_interval=self.pt_config.data_refresh_seconds
                )
                self.add_data_provider(provider)
                
        for provider in self.data_providers.values():
            await provider.connect()
            
        # Start equity recording task
        asyncio.create_task(self._equity_recording_loop())
        
        logger.info("Paper trading session started")
        
    async def stop(self):
        """Stop paper trading session."""
        if not self._running:
            return
            
        logger.info("Stopping paper trading session...")
        self._running = False
        
        # Disconnect data providers
        for provider in self.data_providers.values():
            await provider.disconnect()
            
        # Finalize results
        self._finalize_results()
        
        logger.info("Paper trading session stopped")
        
    async def _on_market_update(self, event: MarketUpdateEvent):
        """Handle market update from data provider."""
        if not self._running:
            return
            
        self._event_count += 1
        
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
            try:
                orders = strategy.on_market_update(event, self.portfolio)
                for order in orders:
                    await self._execute_order(order, strategy.name)
            except Exception as e:
                logger.error(f"Strategy {strategy.name} error: {e}")
                
    async def _execute_order(self, order: Order, strategy_name: str):
        """Execute order on simulated exchange."""
        self.results.total_orders += 1
        
        result = self.exchange.submit_order(order)
        
        if result.filled:
            self.results.filled_orders += 1
            self.results.total_fees += result.fees
            
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
                "strategy": strategy_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(
                f"Trade executed: {order.side.value} {result.filled_size:.2f} "
                f"@ {result.fill_price:.4f} on {order.market_id}"
            )
        else:
            self.results.rejected_orders += 1
            logger.debug(f"Order rejected: {result.reason}")
            
    async def _equity_recording_loop(self):
        """Periodically record equity."""
        interval = self.pt_config.record_equity_interval
        
        while self._running:
            current_prices = {
                market_id: snapshot.yes_price
                for market_id, snapshot in self.exchange.markets.items()
            }
            self.portfolio.record_equity(datetime.utcnow(), current_prices)
            
            await asyncio.sleep(interval)
            
    def _finalize_results(self):
        """Calculate final results."""
        current_prices = {
            market_id: snapshot.yes_price
            for market_id, snapshot in self.exchange.markets.items()
        }
        
        self.results.end_date = datetime.utcnow()
        self.results.final_value = self.portfolio.get_portfolio_value(current_prices)
        self.results.total_return = self.results.final_value - self.pt_config.initial_capital
        self.results.total_return_pct = self.results.total_return / self.pt_config.initial_capital
        self.results.metrics = self.portfolio.get_metrics()
        self.results.equity_curve = list(self.portfolio.equity_curve)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current paper trading status."""
        current_prices = {
            market_id: snapshot.yes_price
            for market_id, snapshot in self.exchange.markets.items()
        }
        
        return {
            "running": self._running,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "events_processed": self._event_count,
            "portfolio": self.portfolio.get_summary(),
            "portfolio_value": self.portfolio.get_portfolio_value(current_prices),
            "open_positions": len(self.portfolio.positions),
            "total_trades": len(self.results.trades),
            "strategies": [s.name for s in self.strategies],
            "data_providers": [p.value for p in self.data_providers.keys()]
        }
        
    def get_results(self) -> BacktestResults:
        """Get current results."""
        self._finalize_results()
        return self.results


async def run_paper_trading_demo():
    """Demo function to run paper trading."""
    from .backtest import SimpleMovingAverageStrategy
    
    # Create configuration
    config = SimulationConfig(mode="paper")
    config.paper_trading.initial_capital = 10000
    config.paper_trading.platforms = [Platform.POLYMARKET, Platform.KALSHI]
    
    # Create engine
    engine = PaperTradingEngine(config)
    
    # Add strategy
    strategy = SimpleMovingAverageStrategy(
        name="sma_demo",
        lookback_periods=10,
        position_size=50,
        threshold=0.03
    )
    engine.add_strategy(strategy)
    
    # Start paper trading
    await engine.start()
    
    # Run for a while
    try:
        while True:
            await asyncio.sleep(10)
            status = engine.get_status()
            print(f"Portfolio value: ${status['portfolio_value']:,.2f}")
            print(f"Events processed: {status['events_processed']}")
            print(f"Trades: {status['total_trades']}")
            print("-" * 40)
    except KeyboardInterrupt:
        pass
    finally:
        await engine.stop()
        
    # Print results
    results = engine.get_results()
    results.print_summary()


if __name__ == "__main__":
    asyncio.run(run_paper_trading_demo())
