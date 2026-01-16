# PredictBot Backtesting & Simulation System Design

## Executive Summary

This document outlines the architecture for a backtesting and simulation system that allows safe testing of the PredictBot trading stack before deploying with real capital. The system supports three modes:

1. **Historical Backtesting** - Replay historical market data to test strategies
2. **Paper Trading (Simulation)** - Live market data with simulated execution
3. **Sandbox Mode** - Use platform-provided test environments (Kalshi demo, etc.)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PredictBot Simulation Layer                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  Historical  │  │    Paper     │  │   Sandbox    │               │
│  │  Backtest    │  │   Trading    │  │    Mode      │               │
│  │   Engine     │  │   Engine     │  │   (Demo)     │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
│         └────────────┬────┴────────────────┘                        │
│                      │                                               │
│         ┌────────────▼────────────┐                                 │
│         │   Simulated Exchange    │                                 │
│         │   (Order Matching)      │                                 │
│         └────────────┬────────────┘                                 │
│                      │                                               │
│         ┌────────────▼────────────┐                                 │
│         │   Virtual Portfolio     │                                 │
│         │   & Risk Manager        │                                 │
│         └────────────┬────────────┘                                 │
│                      │                                               │
├──────────────────────┼──────────────────────────────────────────────┤
│                      │                                               │
│         ┌────────────▼────────────┐                                 │
│         │   Existing PredictBot   │                                 │
│         │   Trading Strategies    │                                 │
│         │   (Unchanged Code)      │                                 │
│         └─────────────────────────┘                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Components

### 2.1 Data Layer

#### Historical Data Store
```python
# Database schema for historical prediction market data
class MarketSnapshot:
    market_id: str
    platform: str  # polymarket, kalshi, manifold
    timestamp: datetime
    question: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    resolution_date: datetime
    resolved: bool
    resolution_outcome: Optional[str]  # YES, NO, or None
    
class OrderBookSnapshot:
    market_id: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # (price, size)
    asks: List[Tuple[float, float]]
    
class TradeEvent:
    market_id: str
    timestamp: datetime
    side: str  # BUY_YES, BUY_NO, SELL_YES, SELL_NO
    price: float
    size: float
```

#### Data Collection Pipeline
```yaml
# Data sources for backtesting
data_sources:
  polymarket:
    - REST API polling (every 5 min for prices)
    - WebSocket for real-time trades
    - CLOB order book snapshots
    
  kalshi:
    - REST API for market data
    - WebSocket for order book
    - Historical trades export
    
  manifold:
    - REST API for market data
    - Bet history endpoint
    
  external:
    - News events (for correlation analysis)
    - Economic calendar
    - Social sentiment data
```

### 2.2 Simulated Exchange Engine

```python
class SimulatedExchange:
    """
    Simulates order execution for prediction markets.
    
    Key differences from traditional exchanges:
    - Binary outcomes (YES/NO contracts)
    - Price range 0.01 to 0.99
    - Resolution events
    - Platform-specific fee structures
    """
    
    def __init__(self, config: SimulationConfig):
        self.fill_model = config.fill_model
        self.latency_model = config.latency_model
        self.fee_model = config.fee_model
        self.order_book = SimulatedOrderBook()
        self.pending_orders = []
        
    def submit_order(self, order: Order) -> OrderResult:
        """Submit order with simulated latency and fill logic."""
        # Apply latency
        execution_time = self.latency_model.get_latency()
        
        # Check if order can be filled
        fill_result = self.fill_model.attempt_fill(
            order=order,
            order_book=self.order_book,
            market_price=self.get_market_price(order.market_id)
        )
        
        # Apply fees
        if fill_result.filled:
            fill_result.fees = self.fee_model.calculate_fees(
                platform=order.platform,
                size=fill_result.filled_size,
                price=fill_result.fill_price
            )
            
        return fill_result
    
    def resolve_market(self, market_id: str, outcome: str):
        """Handle market resolution - settle all positions."""
        pass
```

### 2.3 Fill Models

```python
class PredictionMarketFillModel:
    """
    Fill model specific to prediction markets.
    
    Considerations:
    - Lower liquidity than traditional markets
    - Wider spreads
    - Price impact on larger orders
    - Time-to-resolution affects liquidity
    """
    
    def __init__(
        self,
        base_fill_probability: float = 0.8,
        slippage_model: str = "linear",  # linear, sqrt, or custom
        max_slippage_bps: int = 50,
        partial_fill_enabled: bool = True
    ):
        self.base_fill_prob = base_fill_probability
        self.slippage_model = slippage_model
        self.max_slippage = max_slippage_bps / 10000
        self.partial_fill = partial_fill_enabled
        
    def attempt_fill(
        self,
        order: Order,
        order_book: OrderBook,
        market_price: float
    ) -> FillResult:
        """
        Attempt to fill an order with realistic simulation.
        """
        # Calculate available liquidity
        available_liquidity = self._get_available_liquidity(
            order_book, order.side
        )
        
        # Determine fill size (may be partial)
        fill_size = min(order.size, available_liquidity)
        
        if fill_size == 0:
            return FillResult(filled=False, reason="no_liquidity")
        
        # Calculate price impact / slippage
        slippage = self._calculate_slippage(
            order_size=fill_size,
            available_liquidity=available_liquidity,
            market_price=market_price
        )
        
        # Determine fill price
        if order.side in ["BUY_YES", "BUY_NO"]:
            fill_price = min(market_price + slippage, order.limit_price or 1.0)
        else:
            fill_price = max(market_price - slippage, order.limit_price or 0.0)
            
        return FillResult(
            filled=True,
            filled_size=fill_size,
            fill_price=fill_price,
            slippage=slippage
        )
```

### 2.4 Fee Models

```python
class PlatformFeeModel:
    """Platform-specific fee structures."""
    
    FEE_STRUCTURES = {
        "polymarket": {
            "maker_fee": 0.0,      # 0% maker fee
            "taker_fee": 0.02,     # 2% taker fee
            "withdrawal_fee": 0.0,
        },
        "kalshi": {
            "maker_fee": 0.0,
            "taker_fee": 0.07,     # 7 cents per contract (capped)
            "fee_cap": 0.07,       # Max 7 cents per contract
        },
        "manifold": {
            "maker_fee": 0.0,
            "taker_fee": 0.0,      # No fees (play money)
            "withdrawal_fee": 0.0,
        }
    }
    
    def calculate_fees(
        self,
        platform: str,
        size: float,
        price: float,
        is_maker: bool = False
    ) -> float:
        """Calculate trading fees for a given platform."""
        fees = self.FEE_STRUCTURES.get(platform, {})
        
        if is_maker:
            return size * price * fees.get("maker_fee", 0)
        else:
            if platform == "kalshi":
                # Kalshi charges per contract, capped
                return min(size * fees["taker_fee"], size * fees["fee_cap"])
            else:
                return size * price * fees.get("taker_fee", 0)
```

---

## 3. Simulation Modes

### 3.1 Historical Backtesting

```python
class HistoricalBacktestEngine:
    """
    Replay historical data through trading strategies.
    
    Features:
    - Event-driven simulation
    - Configurable time acceleration
    - Market resolution handling
    - Performance analytics
    """
    
    def __init__(self, config: BacktestConfig):
        self.start_date = config.start_date
        self.end_date = config.end_date
        self.initial_capital = config.initial_capital
        self.exchange = SimulatedExchange(config.exchange_config)
        self.portfolio = VirtualPortfolio(config.initial_capital)
        self.strategies = []
        
    def add_strategy(self, strategy: TradingStrategy):
        """Add a trading strategy to backtest."""
        self.strategies.append(strategy)
        
    def run(self) -> BacktestResults:
        """Execute the backtest."""
        # Load historical data
        data_feed = HistoricalDataFeed(
            start=self.start_date,
            end=self.end_date
        )
        
        results = BacktestResults()
        
        for event in data_feed:
            if isinstance(event, MarketUpdate):
                # Update market prices
                self.exchange.update_market(event)
                
                # Let strategies react
                for strategy in self.strategies:
                    signals = strategy.on_market_update(event)
                    for signal in signals:
                        result = self.exchange.submit_order(signal)
                        self.portfolio.update(result)
                        results.record_trade(result)
                        
            elif isinstance(event, MarketResolution):
                # Handle market resolution
                pnl = self.portfolio.resolve_position(
                    event.market_id,
                    event.outcome
                )
                results.record_resolution(event, pnl)
                
        return results
```

### 3.2 Paper Trading (Live Simulation)

```python
class PaperTradingEngine:
    """
    Live market data with simulated execution.
    
    Features:
    - Real-time market data
    - Simulated order execution
    - No real capital at risk
    - Performance tracking
    """
    
    def __init__(self, config: PaperTradingConfig):
        self.exchange = SimulatedExchange(config.exchange_config)
        self.portfolio = VirtualPortfolio(config.initial_capital)
        self.data_feeds = self._setup_live_feeds(config.platforms)
        
    async def start(self):
        """Start paper trading session."""
        # Connect to live data feeds
        for feed in self.data_feeds:
            await feed.connect()
            
        # Start processing loop
        async for event in self._event_stream():
            await self._process_event(event)
            
    async def _process_event(self, event: MarketEvent):
        """Process incoming market event."""
        # Update simulated exchange with real prices
        self.exchange.update_market(event)
        
        # Forward to strategies (same interface as live trading)
        for strategy in self.strategies:
            signals = await strategy.on_market_update(event)
            for signal in signals:
                # Execute on simulated exchange
                result = self.exchange.submit_order(signal)
                self.portfolio.update(result)
                
                # Log for analysis
                self._log_trade(signal, result)
```

### 3.3 Sandbox Mode (Platform Demo Accounts)

```python
class SandboxModeConfig:
    """
    Configuration for platform sandbox/demo environments.
    
    Supported platforms:
    - Kalshi: Demo environment available
    - Polymarket: Testnet (Polygon Mumbai)
    - Manifold: Play money by default
    """
    
    SANDBOX_ENDPOINTS = {
        "kalshi": {
            "api_url": "https://demo-api.kalshi.co",
            "ws_url": "wss://demo-api.kalshi.co/trade-api/ws/v2",
            "requires_demo_account": True
        },
        "polymarket": {
            "api_url": "https://clob.polymarket.com",  # Use testnet RPC
            "rpc_url": "https://rpc-mumbai.maticvigil.com",
            "chain_id": 80001,  # Mumbai testnet
            "requires_testnet_tokens": True
        },
        "manifold": {
            "api_url": "https://api.manifold.markets",
            "is_play_money": True,  # Already simulated
            "no_special_config": True
        }
    }
```

---

## 4. Virtual Portfolio Manager

```python
class VirtualPortfolio:
    """
    Manages simulated positions and capital.
    
    Tracks:
    - Cash balance
    - Open positions by market
    - Realized P&L
    - Unrealized P&L
    - Position history
    """
    
    def __init__(self, initial_capital: float):
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.resolution_history: List[Resolution] = []
        
    def open_position(
        self,
        market_id: str,
        side: str,
        size: float,
        price: float,
        fees: float
    ) -> bool:
        """Open or add to a position."""
        cost = size * price + fees
        
        if cost > self.cash:
            return False  # Insufficient funds
            
        self.cash -= cost
        
        if market_id in self.positions:
            self.positions[market_id].add(side, size, price)
        else:
            self.positions[market_id] = Position(
                market_id=market_id,
                side=side,
                size=size,
                avg_price=price
            )
            
        self.trade_history.append(Trade(
            market_id=market_id,
            side=side,
            size=size,
            price=price,
            fees=fees,
            timestamp=datetime.utcnow()
        ))
        
        return True
        
    def resolve_position(self, market_id: str, outcome: str) -> float:
        """
        Resolve a position when market settles.
        
        Returns realized P&L.
        """
        if market_id not in self.positions:
            return 0.0
            
        position = self.positions[market_id]
        
        # Calculate payout
        if outcome == "YES":
            payout = position.yes_shares * 1.0  # $1 per YES share
        else:
            payout = position.no_shares * 1.0   # $1 per NO share
            
        # Calculate P&L
        cost_basis = position.total_cost
        pnl = payout - cost_basis
        
        # Update cash
        self.cash += payout
        
        # Record resolution
        self.resolution_history.append(Resolution(
            market_id=market_id,
            outcome=outcome,
            payout=payout,
            pnl=pnl,
            timestamp=datetime.utcnow()
        ))
        
        # Remove position
        del self.positions[market_id]
        
        return pnl
        
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value including unrealized P&L."""
        position_value = sum(
            pos.size * current_prices.get(pos.market_id, pos.avg_price)
            for pos in self.positions.values()
        )
        return self.cash + position_value
        
    def get_metrics(self) -> PortfolioMetrics:
        """Calculate portfolio performance metrics."""
        total_pnl = self.cash - self.initial_capital + sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        
        winning_trades = [t for t in self.resolution_history if t.pnl > 0]
        losing_trades = [t for t in self.resolution_history if t.pnl < 0]
        
        return PortfolioMetrics(
            total_return=total_pnl / self.initial_capital,
            win_rate=len(winning_trades) / max(len(self.resolution_history), 1),
            avg_win=sum(t.pnl for t in winning_trades) / max(len(winning_trades), 1),
            avg_loss=sum(t.pnl for t in losing_trades) / max(len(losing_trades), 1),
            sharpe_ratio=self._calculate_sharpe(),
            max_drawdown=self._calculate_max_drawdown(),
            total_trades=len(self.trade_history),
            resolved_markets=len(self.resolution_history)
        )
```

---

## 5. Integration with Existing Stack

### 5.1 Strategy Adapter Pattern

```python
class SimulationAdapter:
    """
    Adapter that allows existing strategies to run in simulation mode
    without code changes.
    
    Intercepts API calls and routes to simulated exchange.
    """
    
    def __init__(
        self,
        mode: str,  # "backtest", "paper", "sandbox"
        config: SimulationConfig
    ):
        self.mode = mode
        self.config = config
        
        if mode == "backtest":
            self.engine = HistoricalBacktestEngine(config)
        elif mode == "paper":
            self.engine = PaperTradingEngine(config)
        else:
            self.engine = SandboxEngine(config)
            
    def wrap_strategy(self, strategy: TradingStrategy) -> TradingStrategy:
        """
        Wrap a strategy to intercept trading calls.
        """
        # Replace API clients with simulated versions
        strategy.polymarket_client = SimulatedPolymarketClient(self.engine)
        strategy.kalshi_client = SimulatedKalshiClient(self.engine)
        strategy.manifold_client = SimulatedManifoldClient(self.engine)
        
        return strategy
```

### 5.2 Configuration

```yaml
# config/simulation.yml
simulation:
  mode: "paper"  # backtest, paper, sandbox
  
  backtest:
    start_date: "2024-01-01"
    end_date: "2024-12-31"
    initial_capital: 10000
    data_source: "historical_db"
    
  paper_trading:
    initial_capital: 10000
    platforms:
      - polymarket
      - kalshi
    real_time_data: true
    
  sandbox:
    kalshi_demo_api_key: "${KALSHI_DEMO_API_KEY}"
    polymarket_testnet: true
    
  exchange:
    fill_model:
      type: "realistic"
      base_fill_probability: 0.85
      slippage_model: "sqrt"
      max_slippage_bps: 30
      
    latency_model:
      type: "normal"
      mean_ms: 50
      std_ms: 20
      
    fee_model:
      use_platform_fees: true
      
  risk_limits:
    max_position_size: 500
    max_daily_loss: 200
    max_open_positions: 10
```

---

## 6. Analytics & Reporting

### 6.1 Performance Metrics

```python
@dataclass
class BacktestReport:
    """Comprehensive backtest performance report."""
    
    # Overall Performance
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    
    # Risk Metrics
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR
    beta: float
    
    # Strategy-Specific
    by_strategy: Dict[str, StrategyMetrics]
    by_platform: Dict[str, PlatformMetrics]
    by_market_category: Dict[str, CategoryMetrics]
    
    # Time Analysis
    daily_returns: List[float]
    monthly_returns: List[float]
    equity_curve: List[Tuple[datetime, float]]
    drawdown_curve: List[Tuple[datetime, float]]
```

### 6.2 Visualization Dashboard

The admin portal will include a simulation dashboard with:

1. **Equity Curve** - Portfolio value over time
2. **Drawdown Chart** - Maximum drawdown visualization
3. **Trade Distribution** - Win/loss distribution histogram
4. **Strategy Comparison** - Side-by-side strategy performance
5. **Risk Metrics** - VaR, Sharpe, etc. displayed
6. **Position Heatmap** - Current positions by market/platform

---

## 7. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Historical data collection pipeline
- [ ] Database schema for market snapshots
- [ ] Basic simulated exchange engine
- [ ] Virtual portfolio manager

### Phase 2: Backtest Engine (Week 3-4)
- [ ] Event-driven backtest framework
- [ ] Fill models (basic, realistic)
- [ ] Fee model implementation
- [ ] Market resolution handling

### Phase 3: Paper Trading (Week 5-6)
- [ ] Live data feed integration
- [ ] Real-time simulation engine
- [ ] Strategy adapter pattern
- [ ] Performance tracking

### Phase 4: Analytics & UI (Week 7-8)
- [ ] Performance metrics calculation
- [ ] Admin portal simulation dashboard
- [ ] Report generation
- [ ] Strategy comparison tools

### Phase 5: Advanced Features (Week 9+)
- [ ] Monte Carlo simulation
- [ ] Walk-forward optimization
- [ ] Multi-strategy backtesting
- [ ] Sandbox mode integration

---

## 8. Data Collection Requirements

### 8.1 Minimum Data for Backtesting

| Data Type | Frequency | Retention | Priority |
|-----------|-----------|-----------|----------|
| Market prices (YES/NO) | 5 min | 2 years | High |
| Order book snapshots | 15 min | 6 months | Medium |
| Trade events | Real-time | 1 year | High |
| Market metadata | Daily | Forever | High |
| Resolution outcomes | On event | Forever | Critical |
| News/events | Hourly | 1 year | Medium |

### 8.2 Data Collection Script

```python
# scripts/collect_historical_data.py
async def collect_market_data():
    """Collect and store historical market data."""
    
    platforms = [
        PolymarketCollector(),
        KalshiCollector(),
        ManifoldCollector()
    ]
    
    for platform in platforms:
        # Get all active markets
        markets = await platform.get_active_markets()
        
        for market in markets:
            # Store market snapshot
            snapshot = MarketSnapshot(
                market_id=market.id,
                platform=platform.name,
                timestamp=datetime.utcnow(),
                question=market.question,
                yes_price=market.yes_price,
                no_price=market.no_price,
                volume_24h=market.volume,
                liquidity=market.liquidity,
                resolution_date=market.end_date
            )
            await db.store_snapshot(snapshot)
            
            # Store order book if available
            if hasattr(market, 'order_book'):
                await db.store_order_book(market.order_book)
```

---

## 9. Risk Considerations

### 9.1 Simulation vs Reality Gaps

| Factor | Simulation | Reality | Mitigation |
|--------|------------|---------|------------|
| Liquidity | Estimated | Variable | Conservative fill assumptions |
| Slippage | Modeled | Unpredictable | Add safety margin |
| Latency | Simulated | Network-dependent | Test with higher latency |
| Fees | Known | May change | Monitor platform updates |
| Market impact | Simplified | Complex | Limit position sizes |

### 9.2 Overfitting Prevention

- Use walk-forward validation
- Out-of-sample testing periods
- Parameter sensitivity analysis
- Monte Carlo stress testing
- Cross-platform validation

---

## 10. Conclusion

This backtesting and simulation system provides a comprehensive framework for:

1. **Safe Strategy Development** - Test ideas without risking capital
2. **Performance Validation** - Verify strategies work before deployment
3. **Risk Assessment** - Understand potential drawdowns and losses
4. **Continuous Improvement** - Iterate on strategies with historical data

The modular design allows existing PredictBot strategies to run unchanged in simulation mode, ensuring consistency between testing and production environments.
