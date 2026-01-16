"""
PredictBot Simulation - Virtual Portfolio Manager
==================================================

Manages simulated positions, cash, and calculates performance metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math
import statistics

from .models import (
    Platform,
    OrderSide,
    ResolutionOutcome,
    TradeEvent,
    MarketResolution
)


@dataclass
class Position:
    """
    Represents a position in a prediction market.
    
    Tracks YES and NO shares separately since they can be held simultaneously.
    """
    market_id: str
    platform: Platform
    yes_shares: float = 0.0
    no_shares: float = 0.0
    yes_avg_price: float = 0.0
    no_avg_price: float = 0.0
    yes_cost_basis: float = 0.0
    no_cost_basis: float = 0.0
    opened_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_cost_basis(self) -> float:
        """Total cost basis for the position."""
        return self.yes_cost_basis + self.no_cost_basis
    
    @property
    def net_shares(self) -> float:
        """Net position (positive = long YES, negative = long NO)."""
        return self.yes_shares - self.no_shares
    
    @property
    def is_empty(self) -> bool:
        """Check if position is empty."""
        return self.yes_shares == 0 and self.no_shares == 0
    
    def add_shares(
        self,
        side: OrderSide,
        shares: float,
        price: float,
        fees: float = 0.0
    ):
        """
        Add shares to the position.
        
        Args:
            side: Which side to add (BUY_YES, BUY_NO, etc.)
            shares: Number of shares
            price: Price per share
            fees: Trading fees
        """
        cost = shares * price + fees
        
        if side == OrderSide.BUY_YES:
            # Update average price
            total_shares = self.yes_shares + shares
            if total_shares > 0:
                self.yes_avg_price = (
                    (self.yes_shares * self.yes_avg_price + shares * price) / total_shares
                )
            self.yes_shares = total_shares
            self.yes_cost_basis += cost
            
        elif side == OrderSide.BUY_NO:
            total_shares = self.no_shares + shares
            if total_shares > 0:
                self.no_avg_price = (
                    (self.no_shares * self.no_avg_price + shares * price) / total_shares
                )
            self.no_shares = total_shares
            self.no_cost_basis += cost
            
        elif side == OrderSide.SELL_YES:
            # Reduce YES position
            self.yes_shares = max(0, self.yes_shares - shares)
            # Proportionally reduce cost basis
            if self.yes_shares > 0:
                reduction_ratio = shares / (self.yes_shares + shares)
                self.yes_cost_basis *= (1 - reduction_ratio)
            else:
                self.yes_cost_basis = 0
                
        elif side == OrderSide.SELL_NO:
            self.no_shares = max(0, self.no_shares - shares)
            if self.no_shares > 0:
                reduction_ratio = shares / (self.no_shares + shares)
                self.no_cost_basis *= (1 - reduction_ratio)
            else:
                self.no_cost_basis = 0
                
        self.last_updated = datetime.utcnow()
    
    def get_unrealized_pnl(self, current_yes_price: float) -> float:
        """
        Calculate unrealized P&L at current prices.
        
        Args:
            current_yes_price: Current YES price
            
        Returns:
            Unrealized P&L
        """
        current_no_price = 1.0 - current_yes_price
        
        yes_value = self.yes_shares * current_yes_price
        no_value = self.no_shares * current_no_price
        
        return (yes_value + no_value) - self.total_cost_basis
    
    def get_market_value(self, current_yes_price: float) -> float:
        """Get current market value of position."""
        current_no_price = 1.0 - current_yes_price
        return self.yes_shares * current_yes_price + self.no_shares * current_no_price
    
    def resolve(self, outcome: ResolutionOutcome) -> Tuple[float, float]:
        """
        Resolve the position and calculate final P&L.
        
        Args:
            outcome: Market resolution outcome
            
        Returns:
            Tuple of (payout, realized_pnl)
        """
        if outcome == ResolutionOutcome.YES:
            payout = self.yes_shares * 1.0  # YES shares pay $1
        elif outcome == ResolutionOutcome.NO:
            payout = self.no_shares * 1.0   # NO shares pay $1
        elif outcome == ResolutionOutcome.CANCELLED:
            # Return cost basis on cancellation
            payout = self.total_cost_basis
        else:
            payout = 0.0
            
        realized_pnl = payout - self.total_cost_basis
        return payout, realized_pnl


@dataclass
class Trade:
    """Record of an executed trade."""
    trade_id: str
    market_id: str
    platform: Platform
    side: OrderSide
    size: float
    price: float
    fees: float
    timestamp: datetime
    pnl: Optional[float] = None  # Set when position is closed/resolved
    
    @property
    def cost(self) -> float:
        """Total cost of trade including fees."""
        return self.size * self.price + self.fees


@dataclass
class Resolution:
    """Record of a position resolution."""
    market_id: str
    platform: Platform
    outcome: ResolutionOutcome
    payout: float
    pnl: float
    timestamp: datetime
    question: str = ""


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    # Returns
    total_return: float = 0.0
    total_return_pct: float = 0.0
    annualized_return: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    calmar_ratio: float = 0.0
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    
    # Resolution statistics
    resolved_markets: int = 0
    correct_predictions: int = 0
    prediction_accuracy: float = 0.0
    
    # Position metrics
    avg_position_size: float = 0.0
    avg_holding_period_days: float = 0.0


class VirtualPortfolio:
    """
    Manages simulated positions and capital.
    
    Tracks:
    - Cash balance
    - Open positions by market
    - Realized P&L
    - Unrealized P&L
    - Trade and resolution history
    """
    
    def __init__(self, initial_capital: float):
        """
        Initialize portfolio with starting capital.
        
        Args:
            initial_capital: Starting cash balance
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.resolution_history: List[Resolution] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self._peak_equity = initial_capital
        self._max_drawdown = 0.0
        
    def get_position(self, market_id: str) -> Optional[Position]:
        """Get position for a market."""
        return self.positions.get(market_id)
    
    def execute_trade(
        self,
        trade_id: str,
        market_id: str,
        platform: Platform,
        side: OrderSide,
        size: float,
        price: float,
        fees: float = 0.0
    ) -> bool:
        """
        Execute a trade and update portfolio.
        
        Args:
            trade_id: Unique trade identifier
            market_id: Market identifier
            platform: Trading platform
            side: Order side
            size: Number of shares
            price: Execution price
            fees: Trading fees
            
        Returns:
            True if trade executed successfully
        """
        # Calculate cost
        if side in [OrderSide.BUY_YES, OrderSide.BUY_NO]:
            cost = size * price + fees
            if cost > self.cash:
                return False  # Insufficient funds
            self.cash -= cost
        else:
            # Selling - receive proceeds minus fees
            proceeds = size * price - fees
            self.cash += proceeds
            
        # Update or create position
        if market_id not in self.positions:
            self.positions[market_id] = Position(
                market_id=market_id,
                platform=platform
            )
            
        self.positions[market_id].add_shares(side, size, price, fees)
        
        # Remove empty positions
        if self.positions[market_id].is_empty:
            del self.positions[market_id]
            
        # Record trade
        trade = Trade(
            trade_id=trade_id,
            market_id=market_id,
            platform=platform,
            side=side,
            size=size,
            price=price,
            fees=fees,
            timestamp=datetime.utcnow()
        )
        self.trade_history.append(trade)
        
        return True
    
    def resolve_position(
        self,
        market_id: str,
        outcome: ResolutionOutcome,
        question: str = ""
    ) -> float:
        """
        Resolve a position when market settles.
        
        Args:
            market_id: Market identifier
            outcome: Resolution outcome
            question: Market question (for records)
            
        Returns:
            Realized P&L from resolution
        """
        if market_id not in self.positions:
            return 0.0
            
        position = self.positions[market_id]
        payout, pnl = position.resolve(outcome)
        
        # Update cash
        self.cash += payout
        
        # Record resolution
        resolution = Resolution(
            market_id=market_id,
            platform=position.platform,
            outcome=outcome,
            payout=payout,
            pnl=pnl,
            timestamp=datetime.utcnow(),
            question=question
        )
        self.resolution_history.append(resolution)
        
        # Remove position
        del self.positions[market_id]
        
        return pnl
    
    def get_portfolio_value(
        self,
        current_prices: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            current_prices: Dict of market_id -> current YES price
            
        Returns:
            Total portfolio value
        """
        if current_prices is None:
            current_prices = {}
            
        position_value = 0.0
        for market_id, position in self.positions.items():
            # Use current price if available, otherwise use avg price
            yes_price = current_prices.get(market_id, position.yes_avg_price)
            position_value += position.get_market_value(yes_price)
            
        return self.cash + position_value
    
    def get_unrealized_pnl(
        self,
        current_prices: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate total unrealized P&L."""
        if current_prices is None:
            current_prices = {}
            
        total_unrealized = 0.0
        for market_id, position in self.positions.items():
            yes_price = current_prices.get(market_id, position.yes_avg_price)
            total_unrealized += position.get_unrealized_pnl(yes_price)
            
        return total_unrealized
    
    def get_realized_pnl(self) -> float:
        """Calculate total realized P&L from resolutions."""
        return sum(r.pnl for r in self.resolution_history)
    
    def record_equity(
        self,
        timestamp: datetime,
        current_prices: Optional[Dict[str, float]] = None
    ):
        """
        Record current equity for equity curve.
        
        Args:
            timestamp: Current timestamp
            current_prices: Current market prices
        """
        equity = self.get_portfolio_value(current_prices)
        self.equity_curve.append((timestamp, equity))
        
        # Update peak and drawdown
        if equity > self._peak_equity:
            self._peak_equity = equity
        
        drawdown = (self._peak_equity - equity) / self._peak_equity
        if drawdown > self._max_drawdown:
            self._max_drawdown = drawdown
    
    def get_metrics(self) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics.
        
        Returns:
            PortfolioMetrics with all calculated values
        """
        metrics = PortfolioMetrics()
        
        # Basic returns
        current_value = self.get_portfolio_value()
        metrics.total_return = current_value - self.initial_capital
        metrics.total_return_pct = metrics.total_return / self.initial_capital
        
        # Trade statistics
        metrics.total_trades = len(self.trade_history)
        
        # Resolution statistics
        metrics.resolved_markets = len(self.resolution_history)
        winning_resolutions = [r for r in self.resolution_history if r.pnl > 0]
        losing_resolutions = [r for r in self.resolution_history if r.pnl < 0]
        
        metrics.winning_trades = len(winning_resolutions)
        metrics.losing_trades = len(losing_resolutions)
        
        if metrics.resolved_markets > 0:
            metrics.win_rate = metrics.winning_trades / metrics.resolved_markets
            
        if winning_resolutions:
            metrics.avg_win = sum(r.pnl for r in winning_resolutions) / len(winning_resolutions)
            
        if losing_resolutions:
            metrics.avg_loss = abs(sum(r.pnl for r in losing_resolutions) / len(losing_resolutions))
            
        # Profit factor
        total_wins = sum(r.pnl for r in winning_resolutions)
        total_losses = abs(sum(r.pnl for r in losing_resolutions))
        if total_losses > 0:
            metrics.profit_factor = total_wins / total_losses
            
        # Expectancy
        if metrics.resolved_markets > 0:
            metrics.expectancy = (
                metrics.win_rate * metrics.avg_win -
                (1 - metrics.win_rate) * metrics.avg_loss
            )
            
        # Risk metrics from equity curve
        if len(self.equity_curve) > 1:
            returns = self._calculate_returns()
            
            if returns:
                # Sharpe ratio (assuming 0% risk-free rate)
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0
                if std_return > 0:
                    metrics.sharpe_ratio = avg_return / std_return * math.sqrt(252)  # Annualized
                    
                # Sortino ratio (downside deviation)
                negative_returns = [r for r in returns if r < 0]
                if negative_returns:
                    downside_std = statistics.stdev(negative_returns)
                    if downside_std > 0:
                        metrics.sortino_ratio = avg_return / downside_std * math.sqrt(252)
                        
        # Max drawdown
        metrics.max_drawdown_pct = self._max_drawdown
        metrics.max_drawdown = self._max_drawdown * self._peak_equity
        
        # Calmar ratio
        if metrics.max_drawdown_pct > 0:
            metrics.calmar_ratio = metrics.total_return_pct / metrics.max_drawdown_pct
            
        # Annualized return (if we have time data)
        if len(self.equity_curve) >= 2:
            start_time = self.equity_curve[0][0]
            end_time = self.equity_curve[-1][0]
            days = (end_time - start_time).days
            if days > 0:
                years = days / 365.25
                metrics.annualized_return = (
                    (1 + metrics.total_return_pct) ** (1 / years) - 1
                ) if years > 0 else 0
                
        return metrics
    
    def _calculate_returns(self) -> List[float]:
        """Calculate period returns from equity curve."""
        if len(self.equity_curve) < 2:
            return []
            
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i - 1][1]
            curr_equity = self.equity_curve[i][1]
            if prev_equity > 0:
                returns.append((curr_equity - prev_equity) / prev_equity)
                
        return returns
    
    def get_summary(self) -> Dict:
        """Get portfolio summary."""
        return {
            "cash": self.cash,
            "initial_capital": self.initial_capital,
            "portfolio_value": self.get_portfolio_value(),
            "unrealized_pnl": self.get_unrealized_pnl(),
            "realized_pnl": self.get_realized_pnl(),
            "open_positions": len(self.positions),
            "total_trades": len(self.trade_history),
            "resolved_markets": len(self.resolution_history),
            "max_drawdown_pct": self._max_drawdown
        }
    
    def reset(self):
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.trade_history.clear()
        self.resolution_history.clear()
        self.equity_curve.clear()
        self._peak_equity = self.initial_capital
        self._max_drawdown = 0.0
