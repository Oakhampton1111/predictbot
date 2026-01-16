#!/usr/bin/env python3
"""
PredictBot Stack - Configuration Validator

This script validates the config.yml file to ensure all required
parameters are present and have valid values.

Usage:
    python scripts/validate_config.py [--config path/to/config.yml]
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


class ConfigValidator:
    """Validates the PredictBot configuration file."""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def load_config(self) -> bool:
        """Load the configuration file."""
        if not self.config_path.exists():
            self.errors.append(f"Configuration file not found: {self.config_path}")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading config file: {e}")
            return False
    
    def validate_required_section(self, section: str) -> bool:
        """Check if a required section exists."""
        if section not in self.config:
            self.errors.append(f"Missing required section: '{section}'")
            return False
        return True
    
    def validate_type(self, path: str, value: Any, expected_type: type, 
                      required: bool = True) -> bool:
        """Validate that a value is of the expected type."""
        if value is None:
            if required:
                self.errors.append(f"Missing required value: '{path}'")
                return False
            return True
        
        if not isinstance(value, expected_type):
            self.errors.append(
                f"Invalid type for '{path}': expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
            return False
        return True
    
    def validate_range(self, path: str, value: float, 
                       min_val: Optional[float] = None,
                       max_val: Optional[float] = None) -> bool:
        """Validate that a numeric value is within range."""
        if value is None:
            return True
        
        if min_val is not None and value < min_val:
            self.errors.append(
                f"Value for '{path}' ({value}) is below minimum ({min_val})"
            )
            return False
        
        if max_val is not None and value > max_val:
            self.errors.append(
                f"Value for '{path}' ({value}) is above maximum ({max_val})"
            )
            return False
        
        return True
    
    def validate_enum(self, path: str, value: str, 
                      valid_values: List[str]) -> bool:
        """Validate that a value is one of the allowed options."""
        if value is None:
            return True
        
        if value not in valid_values:
            self.errors.append(
                f"Invalid value for '{path}': '{value}'. "
                f"Must be one of: {', '.join(valid_values)}"
            )
            return False
        return True
    
    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """Get a nested value from the config."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def validate_global(self) -> None:
        """Validate global settings."""
        if not self.validate_required_section('global'):
            return
        
        global_cfg = self.config['global']
        
        # Validate total_bankroll
        bankroll = global_cfg.get('total_bankroll')
        self.validate_type('global.total_bankroll', bankroll, (int, float))
        self.validate_range('global.total_bankroll', bankroll, min_val=0)
        
        # Validate data_refresh_interval
        interval = global_cfg.get('data_refresh_interval')
        self.validate_type('global.data_refresh_interval', interval, (int, float))
        self.validate_range('global.data_refresh_interval', interval, min_val=1)
    
    def validate_arbitrage(self) -> None:
        """Validate arbitrage strategy settings."""
        if not self.validate_required_section('arbitrage'):
            return
        
        arb = self.config['arbitrage']
        
        # Validate min_profit
        min_profit = arb.get('min_profit')
        self.validate_type('arbitrage.min_profit', min_profit, (int, float))
        self.validate_range('arbitrage.min_profit', min_profit, min_val=0, max_val=1)
        
        if min_profit is not None and min_profit < 0.01:
            self.warnings.append(
                f"arbitrage.min_profit ({min_profit}) is very low. "
                "Consider setting at least 0.02 (2%) to cover fees."
            )
        
        # Validate max_trade_size
        max_size = arb.get('max_trade_size')
        self.validate_type('arbitrage.max_trade_size', max_size, (int, float))
        self.validate_range('arbitrage.max_trade_size', max_size, min_val=1)
        
        # Validate platform_pairs
        pairs = arb.get('platform_pairs', [])
        valid_pairs = ['polymarket-kalshi', 'polymarket-predictit', 'kalshi-predictit']
        for pair in pairs:
            self.validate_enum(f'arbitrage.platform_pairs[{pair}]', pair, valid_pairs)
        
        # Validate discovery_mode
        discovery = arb.get('discovery_mode')
        self.validate_enum('arbitrage.discovery_mode', discovery, ['auto', 'manual'])
        
        # Validate execution settings
        execution = arb.get('execution', {})
        max_slippage = execution.get('max_slippage')
        self.validate_range('arbitrage.execution.max_slippage', max_slippage, 
                           min_val=0, max_val=0.1)
    
    def validate_market_making(self) -> None:
        """Validate market making strategy settings."""
        if not self.validate_required_section('market_making'):
            return
        
        mm = self.config['market_making']
        
        # Validate Polymarket MM
        if 'polymarket' in mm:
            poly = mm['polymarket']
            
            spread = poly.get('spread_bps')
            self.validate_type('market_making.polymarket.spread_bps', spread, (int, float))
            self.validate_range('market_making.polymarket.spread_bps', spread, 
                               min_val=10, max_val=5000)
            
            order_size = poly.get('order_size')
            self.validate_type('market_making.polymarket.order_size', order_size, (int, float))
            self.validate_range('market_making.polymarket.order_size', order_size, min_val=1)
            
            inv_limit = poly.get('inventory_limit')
            self.validate_type('market_making.polymarket.inventory_limit', inv_limit, (int, float))
            self.validate_range('market_making.polymarket.inventory_limit', inv_limit, min_val=0)
        
        # Validate Manifold MM
        if 'manifold' in mm:
            mf = mm['manifold']
            
            order_size = mf.get('order_size')
            self.validate_type('market_making.manifold.order_size', order_size, (int, float))
            self.validate_range('market_making.manifold.order_size', order_size, min_val=1)
    
    def validate_spike_trading(self) -> None:
        """Validate spike trading strategy settings."""
        if not self.validate_required_section('spike_trading'):
            return
        
        spike = self.config['spike_trading']
        
        # Validate sensitivity
        sensitivity = spike.get('sensitivity')
        self.validate_type('spike_trading.sensitivity', sensitivity, (int, float))
        self.validate_range('spike_trading.sensitivity', sensitivity, min_val=0.01, max_val=0.5)
        
        # Validate strategy
        strategy = spike.get('strategy')
        self.validate_enum('spike_trading.strategy', strategy, 
                          ['mean_reversion', 'momentum', 'hybrid'])
        
        # Validate max_size
        max_size = spike.get('max_size')
        self.validate_type('spike_trading.max_size', max_size, (int, float))
        self.validate_range('spike_trading.max_size', max_size, min_val=1)
        
        # Validate cooldown
        cooldown = spike.get('cooldown')
        self.validate_type('spike_trading.cooldown', cooldown, (int, float))
        self.validate_range('spike_trading.cooldown', cooldown, min_val=0)
        
        # Validate exit settings
        exit_cfg = spike.get('exit', {})
        take_profit = exit_cfg.get('take_profit')
        self.validate_range('spike_trading.exit.take_profit', take_profit, min_val=0, max_val=1)
        
        stop_loss = exit_cfg.get('stop_loss')
        self.validate_range('spike_trading.exit.stop_loss', stop_loss, min_val=0, max_val=1)
    
    def validate_ai_trading(self) -> None:
        """Validate AI trading strategy settings."""
        if not self.validate_required_section('ai_trading'):
            return
        
        ai = self.config['ai_trading']
        
        # Validate model settings
        model = ai.get('model', {})
        primary = model.get('primary')
        valid_models = [
            'openai:gpt-4', 'openai:gpt-3.5-turbo', 
            'anthropic:claude-3', 'xai:grok'
        ]
        if primary and not any(primary.startswith(m.split(':')[0]) for m in valid_models):
            self.warnings.append(
                f"ai_trading.model.primary '{primary}' may not be supported. "
                f"Known models: {', '.join(valid_models)}"
            )
        
        temperature = model.get('temperature')
        self.validate_range('ai_trading.model.temperature', temperature, min_val=0, max_val=2)
        
        # Validate thresholds
        thresholds = ai.get('thresholds', {})
        
        min_confidence = thresholds.get('min_confidence')
        self.validate_range('ai_trading.thresholds.min_confidence', min_confidence, 
                           min_val=0, max_val=1)
        
        if min_confidence is not None and min_confidence < 0.5:
            self.warnings.append(
                f"ai_trading.thresholds.min_confidence ({min_confidence}) is low. "
                "Consider setting at least 0.5 (50%) for safety."
            )
        
        min_edge = thresholds.get('min_edge')
        self.validate_range('ai_trading.thresholds.min_edge', min_edge, min_val=0, max_val=0.5)
        
        max_bet = thresholds.get('max_bet')
        self.validate_type('ai_trading.thresholds.max_bet', max_bet, (int, float))
        self.validate_range('ai_trading.thresholds.max_bet', max_bet, min_val=1)
        
        # Validate agents
        agents = ai.get('agents', {})
        trader = agents.get('trader', {})
        sizing_method = trader.get('sizing_method')
        self.validate_enum('ai_trading.agents.trader.sizing_method', sizing_method,
                          ['kelly', 'fixed', 'fractional'])
        
        kelly_fraction = trader.get('kelly_fraction')
        self.validate_range('ai_trading.agents.trader.kelly_fraction', kelly_fraction,
                           min_val=0.01, max_val=1)
    
    def validate_risk_management(self) -> None:
        """Validate risk management settings."""
        if not self.validate_required_section('risk_management'):
            return
        
        risk = self.config['risk_management']
        
        # Validate global limits
        global_limits = risk.get('global', {})
        
        max_daily_loss = global_limits.get('max_daily_loss')
        self.validate_type('risk_management.global.max_daily_loss', max_daily_loss, (int, float))
        self.validate_range('risk_management.global.max_daily_loss', max_daily_loss, min_val=0)
        
        max_total_position = global_limits.get('max_total_position')
        self.validate_type('risk_management.global.max_total_position', max_total_position, (int, float))
        self.validate_range('risk_management.global.max_total_position', max_total_position, min_val=0)
        
        # Validate circuit breaker
        cb = risk.get('circuit_breaker', {})
        
        failure_threshold = cb.get('failure_threshold')
        self.validate_type('risk_management.circuit_breaker.failure_threshold', 
                          failure_threshold, int)
        self.validate_range('risk_management.circuit_breaker.failure_threshold',
                           failure_threshold, min_val=1, max_val=100)
        
        cooldown = cb.get('cooldown_period')
        self.validate_type('risk_management.circuit_breaker.cooldown_period', cooldown, (int, float))
        self.validate_range('risk_management.circuit_breaker.cooldown_period', cooldown, min_val=0)
    
    def validate_capital_allocation(self) -> None:
        """Validate that capital allocations don't exceed total bankroll."""
        bankroll = self.get_nested('global', 'total_bankroll', default=0)
        
        allocations = {
            'arbitrage': self.get_nested('arbitrage', 'capital_allocation', default=0),
            'polymarket_mm': self.get_nested('market_making', 'polymarket', 
                                             'capital_allocation', default=0),
            'spike_trading': self.get_nested('spike_trading', 'capital_allocation', default=0),
            'ai_trading': self.get_nested('ai_trading', 'capital_allocation', default=0),
        }
        
        total_allocated = sum(allocations.values())
        
        if total_allocated > bankroll:
            self.errors.append(
                f"Total capital allocation ({total_allocated}) exceeds "
                f"total bankroll ({bankroll}). Allocations: {allocations}"
            )
        elif total_allocated > bankroll * 0.9:
            self.warnings.append(
                f"Capital allocation ({total_allocated}) is close to total bankroll "
                f"({bankroll}). Consider leaving some buffer."
            )
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations and return results."""
        if not self.load_config():
            return False, self.errors, self.warnings
        
        # Run all validators
        self.validate_global()
        self.validate_arbitrage()
        self.validate_market_making()
        self.validate_spike_trading()
        self.validate_ai_trading()
        self.validate_risk_management()
        self.validate_capital_allocation()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings


def main():
    parser = argparse.ArgumentParser(
        description='Validate PredictBot configuration file'
    )
    parser.add_argument(
        '--config', '-c',
        default='config/config.yml',
        help='Path to configuration file (default: config/config.yml)'
    )
    parser.add_argument(
        '--strict', '-s',
        action='store_true',
        help='Treat warnings as errors'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PredictBot Configuration Validator")
    print("=" * 60)
    print(f"\nValidating: {args.config}\n")
    
    validator = ConfigValidator(args.config)
    is_valid, errors, warnings = validator.validate()
    
    # Print warnings
    if warnings:
        print("⚠️  WARNINGS:")
        print("-" * 40)
        for warning in warnings:
            print(f"  • {warning}")
        print()
    
    # Print errors
    if errors:
        print("❌ ERRORS:")
        print("-" * 40)
        for error in errors:
            print(f"  • {error}")
        print()
    
    # Final result
    if is_valid and not (args.strict and warnings):
        print("✅ Configuration is valid!")
        if warnings:
            print(f"   ({len(warnings)} warning(s) - review recommended)")
        sys.exit(0)
    else:
        print("❌ Configuration validation failed!")
        print(f"   {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)


if __name__ == '__main__':
    main()
