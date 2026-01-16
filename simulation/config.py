"""
PredictBot Simulation - Configuration
======================================

Configuration classes for simulation modes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

from .models import Platform


@dataclass
class FillModelConfig:
    """Configuration for fill model."""
    model_type: str = "basic"  # basic, realistic
    prob_fill_on_limit: float = 0.8
    prob_slippage: float = 0.3
    max_slippage_bps: int = 50
    price_impact_factor: float = 0.1
    random_seed: Optional[int] = None


@dataclass
class LatencyModelConfig:
    """Configuration for latency model."""
    mean_ms: float = 50.0
    std_ms: float = 20.0
    min_ms: float = 10.0
    max_ms: float = 500.0
    random_seed: Optional[int] = None


@dataclass
class FeeModelConfig:
    """Configuration for fee model."""
    use_platform_fees: bool = True
    custom_fees: Optional[Dict[str, Dict]] = None


@dataclass
class ExchangeConfig:
    """Configuration for simulated exchange."""
    fill_model: FillModelConfig = field(default_factory=FillModelConfig)
    latency_model: LatencyModelConfig = field(default_factory=LatencyModelConfig)
    fee_model: FeeModelConfig = field(default_factory=FeeModelConfig)


@dataclass
class RiskLimitsConfig:
    """Risk limits for simulation."""
    max_position_size: float = 500.0
    max_daily_loss: float = 200.0
    max_open_positions: int = 10
    max_position_pct: float = 0.1  # Max 10% of portfolio per position
    stop_loss_pct: Optional[float] = None


@dataclass
class BacktestConfig:
    """Configuration for historical backtesting."""
    start_date: datetime = field(default_factory=lambda: datetime(2024, 1, 1))
    end_date: datetime = field(default_factory=datetime.utcnow)
    initial_capital: float = 10000.0
    data_source: str = "historical_db"
    data_path: Optional[str] = None
    platforms: List[Platform] = field(default_factory=lambda: [
        Platform.POLYMARKET,
        Platform.KALSHI
    ])
    time_step_minutes: int = 5  # Simulation time step
    record_equity_interval: int = 60  # Record equity every N minutes


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading."""
    initial_capital: float = 10000.0
    platforms: List[Platform] = field(default_factory=lambda: [
        Platform.POLYMARKET,
        Platform.KALSHI
    ])
    real_time_data: bool = True
    data_refresh_seconds: int = 5
    record_equity_interval: int = 60


@dataclass
class SandboxConfig:
    """Configuration for sandbox/demo mode."""
    kalshi_demo_api_key: Optional[str] = None
    kalshi_demo_api_secret: Optional[str] = None
    polymarket_testnet: bool = True
    polymarket_testnet_rpc: str = "https://rpc-mumbai.maticvigil.com"
    initial_capital: float = 10000.0


@dataclass
class SimulationConfig:
    """
    Main simulation configuration.
    
    Supports three modes:
    - backtest: Historical data replay
    - paper: Live data with simulated execution
    - sandbox: Platform demo environments
    """
    mode: str = "paper"  # backtest, paper, sandbox
    
    # Mode-specific configs
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    paper_trading: PaperTradingConfig = field(default_factory=PaperTradingConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    
    # Shared configs
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    risk_limits: RiskLimitsConfig = field(default_factory=RiskLimitsConfig)
    
    # Output settings
    output_dir: str = "./simulation_results"
    save_trades: bool = True
    save_equity_curve: bool = True
    generate_report: bool = True
    
    @classmethod
    def from_yaml(cls, path: str) -> "SimulationConfig":
        """
        Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            SimulationConfig instance
        """
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        return cls.from_dict(data.get("simulation", data))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationConfig":
        """
        Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            SimulationConfig instance
        """
        config = cls()
        
        # Set mode
        config.mode = data.get("mode", "paper")
        
        # Parse backtest config
        if "backtest" in data:
            bt = data["backtest"]
            config.backtest = BacktestConfig(
                start_date=datetime.fromisoformat(bt["start_date"]) if isinstance(bt.get("start_date"), str) else bt.get("start_date", config.backtest.start_date),
                end_date=datetime.fromisoformat(bt["end_date"]) if isinstance(bt.get("end_date"), str) else bt.get("end_date", config.backtest.end_date),
                initial_capital=bt.get("initial_capital", config.backtest.initial_capital),
                data_source=bt.get("data_source", config.backtest.data_source),
                data_path=bt.get("data_path"),
                platforms=[Platform(p) for p in bt.get("platforms", ["polymarket", "kalshi"])],
                time_step_minutes=bt.get("time_step_minutes", 5),
                record_equity_interval=bt.get("record_equity_interval", 60)
            )
            
        # Parse paper trading config
        if "paper_trading" in data:
            pt = data["paper_trading"]
            config.paper_trading = PaperTradingConfig(
                initial_capital=pt.get("initial_capital", config.paper_trading.initial_capital),
                platforms=[Platform(p) for p in pt.get("platforms", ["polymarket", "kalshi"])],
                real_time_data=pt.get("real_time_data", True),
                data_refresh_seconds=pt.get("data_refresh_seconds", 5),
                record_equity_interval=pt.get("record_equity_interval", 60)
            )
            
        # Parse sandbox config
        if "sandbox" in data:
            sb = data["sandbox"]
            config.sandbox = SandboxConfig(
                kalshi_demo_api_key=sb.get("kalshi_demo_api_key"),
                kalshi_demo_api_secret=sb.get("kalshi_demo_api_secret"),
                polymarket_testnet=sb.get("polymarket_testnet", True),
                polymarket_testnet_rpc=sb.get("polymarket_testnet_rpc", config.sandbox.polymarket_testnet_rpc),
                initial_capital=sb.get("initial_capital", config.sandbox.initial_capital)
            )
            
        # Parse exchange config
        if "exchange" in data:
            ex = data["exchange"]
            
            fill_config = FillModelConfig()
            if "fill_model" in ex:
                fm = ex["fill_model"]
                fill_config = FillModelConfig(
                    model_type=fm.get("type", "basic"),
                    prob_fill_on_limit=fm.get("prob_fill_on_limit", 0.8),
                    prob_slippage=fm.get("prob_slippage", 0.3),
                    max_slippage_bps=fm.get("max_slippage_bps", 50),
                    price_impact_factor=fm.get("price_impact_factor", 0.1),
                    random_seed=fm.get("random_seed")
                )
                
            latency_config = LatencyModelConfig()
            if "latency_model" in ex:
                lm = ex["latency_model"]
                latency_config = LatencyModelConfig(
                    mean_ms=lm.get("mean_ms", 50.0),
                    std_ms=lm.get("std_ms", 20.0),
                    min_ms=lm.get("min_ms", 10.0),
                    max_ms=lm.get("max_ms", 500.0),
                    random_seed=lm.get("random_seed")
                )
                
            fee_config = FeeModelConfig()
            if "fee_model" in ex:
                fm = ex["fee_model"]
                fee_config = FeeModelConfig(
                    use_platform_fees=fm.get("use_platform_fees", True),
                    custom_fees=fm.get("custom_fees")
                )
                
            config.exchange = ExchangeConfig(
                fill_model=fill_config,
                latency_model=latency_config,
                fee_model=fee_config
            )
            
        # Parse risk limits
        if "risk_limits" in data:
            rl = data["risk_limits"]
            config.risk_limits = RiskLimitsConfig(
                max_position_size=rl.get("max_position_size", 500.0),
                max_daily_loss=rl.get("max_daily_loss", 200.0),
                max_open_positions=rl.get("max_open_positions", 10),
                max_position_pct=rl.get("max_position_pct", 0.1),
                stop_loss_pct=rl.get("stop_loss_pct")
            )
            
        # Output settings
        config.output_dir = data.get("output_dir", "./simulation_results")
        config.save_trades = data.get("save_trades", True)
        config.save_equity_curve = data.get("save_equity_curve", True)
        config.generate_report = data.get("generate_report", True)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "mode": self.mode,
            "backtest": {
                "start_date": self.backtest.start_date.isoformat(),
                "end_date": self.backtest.end_date.isoformat(),
                "initial_capital": self.backtest.initial_capital,
                "data_source": self.backtest.data_source,
                "platforms": [p.value for p in self.backtest.platforms]
            },
            "paper_trading": {
                "initial_capital": self.paper_trading.initial_capital,
                "platforms": [p.value for p in self.paper_trading.platforms],
                "real_time_data": self.paper_trading.real_time_data
            },
            "exchange": {
                "fill_model": {
                    "type": self.exchange.fill_model.model_type,
                    "prob_fill_on_limit": self.exchange.fill_model.prob_fill_on_limit,
                    "max_slippage_bps": self.exchange.fill_model.max_slippage_bps
                }
            },
            "risk_limits": {
                "max_position_size": self.risk_limits.max_position_size,
                "max_daily_loss": self.risk_limits.max_daily_loss,
                "max_open_positions": self.risk_limits.max_open_positions
            }
        }
    
    def save(self, path: str):
        """Save configuration to YAML file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump({"simulation": self.to_dict()}, f, default_flow_style=False)
    
    def get_initial_capital(self) -> float:
        """Get initial capital based on current mode."""
        if self.mode == "backtest":
            return self.backtest.initial_capital
        elif self.mode == "paper":
            return self.paper_trading.initial_capital
        else:
            return self.sandbox.initial_capital
    
    def get_platforms(self) -> List[Platform]:
        """Get platforms based on current mode."""
        if self.mode == "backtest":
            return self.backtest.platforms
        elif self.mode == "paper":
            return self.paper_trading.platforms
        else:
            return [Platform.KALSHI, Platform.POLYMARKET]
