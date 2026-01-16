"""
PredictBot Stack - Secure Configuration Loader

This module provides secure loading of environment variables and configuration
files with validation and sanitization.
"""

import os
import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


@dataclass
class SecureConfig:
    """Secure configuration container with masked secret display."""
    
    # Platform credentials
    poly_private_key: str = ""
    poly_rpc_url: str = ""
    kalshi_api_key: str = ""
    kalshi_api_secret: str = ""
    manifold_api_key: str = ""
    manifold_username: str = ""
    predictit_api_token: str = ""
    
    # AI credentials
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    xai_api_key: str = ""
    valyu_api_key: str = ""
    
    # System settings
    dry_run: bool = True
    log_level: str = "INFO"
    
    # Feature flags
    enable_arb: bool = True
    enable_mm_polymarket: bool = True
    enable_mm_manifold: bool = True
    enable_spike: bool = True
    enable_ai: bool = True
    
    # Risk management
    max_daily_loss: float = 100.0
    max_total_position: float = 1000.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_cooldown: int = 300
    
    # Strategy config (loaded from YAML)
    strategy_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        # Ensure dry_run is boolean
        if isinstance(self.dry_run, str):
            self.dry_run = self.dry_run.lower() in ('1', 'true', 'yes', 'on')
        
        # Validate numeric ranges
        if self.max_daily_loss < 0:
            raise ValueError("max_daily_loss must be non-negative")
        if self.max_total_position < 0:
            raise ValueError("max_total_position must be non-negative")
        if self.circuit_breaker_threshold < 1:
            raise ValueError("circuit_breaker_threshold must be at least 1")
    
    def mask_secret(self, value: str) -> str:
        """Mask a secret value for safe display."""
        if not value or len(value) <= 8:
            return "*" * len(value) if value else "(not set)"
        return value[:4] + "*" * (len(value) - 8) + value[-4:]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of configuration status with masked secrets."""
        return {
            "platforms": {
                "polymarket": {
                    "configured": bool(self.poly_private_key and self.poly_rpc_url),
                    "private_key": self.mask_secret(self.poly_private_key),
                    "rpc_url": self.poly_rpc_url[:30] + "..." if self.poly_rpc_url else "(not set)"
                },
                "kalshi": {
                    "configured": bool(self.kalshi_api_key and self.kalshi_api_secret),
                    "api_key": self.mask_secret(self.kalshi_api_key)
                },
                "manifold": {
                    "configured": bool(self.manifold_api_key),
                    "username": self.manifold_username or "(not set)"
                },
                "predictit": {
                    "configured": bool(self.predictit_api_token),
                }
            },
            "ai_services": {
                "openai": bool(self.openai_api_key),
                "anthropic": bool(self.anthropic_api_key),
                "xai": bool(self.xai_api_key),
                "polyseer": bool(self.valyu_api_key)
            },
            "features": {
                "arbitrage": self.enable_arb,
                "market_making_polymarket": self.enable_mm_polymarket,
                "market_making_manifold": self.enable_mm_manifold,
                "spike_trading": self.enable_spike,
                "ai_trading": self.enable_ai
            },
            "risk_management": {
                "dry_run": self.dry_run,
                "max_daily_loss": self.max_daily_loss,
                "max_total_position": self.max_total_position,
                "circuit_breaker_threshold": self.circuit_breaker_threshold
            }
        }


class ConfigLoader:
    """Secure configuration loader with validation."""
    
    # Sensitive keys that should never be logged
    SENSITIVE_KEYS = {
        'POLY_PRIVATE_KEY', 'KALSHI_API_SECRET', 'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY', 'XAI_API_KEY', 'VALYU_API_KEY',
        'PREDICTIT_PASSWORD', 'SMTP_PASSWORD'
    }
    
    def __init__(self, env_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            env_path: Path to .env file (optional, uses environment if not provided)
            config_path: Path to config.yml file (optional)
        """
        self.env_path = Path(env_path) if env_path else None
        self.config_path = Path(config_path) if config_path else None
        self._env_vars: Dict[str, str] = {}
        self._yaml_config: Dict[str, Any] = {}
    
    def load(self) -> SecureConfig:
        """Load and validate all configuration."""
        # Load environment variables
        self._load_env()
        
        # Load YAML config if available
        if self.config_path:
            self._load_yaml()
        
        # Build secure config object
        config = self._build_config()
        
        logger.info("Configuration loaded successfully")
        logger.debug(f"Configuration status: {config.get_status_summary()}")
        
        return config
    
    def _load_env(self):
        """Load environment variables from file and/or environment."""
        # Start with current environment
        self._env_vars = dict(os.environ)
        
        # Load from .env file if specified
        if self.env_path and self.env_path.exists():
            self._parse_env_file(self.env_path)
            logger.info(f"Loaded environment from: {self.env_path}")
        elif self.env_path:
            logger.warning(f"Environment file not found: {self.env_path}")
    
    def _parse_env_file(self, path: Path):
        """Parse a .env file and add to environment variables."""
        try:
            with open(path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE
                    if '=' not in line:
                        logger.warning(f"Line {line_num}: Invalid format (missing '=')")
                        continue
                    
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Sanitize the value
                    value = self._sanitize_value(value)
                    
                    self._env_vars[key] = value
                    
                    # Log non-sensitive keys
                    if key not in self.SENSITIVE_KEYS:
                        logger.debug(f"Loaded: {key}={value}")
                    else:
                        logger.debug(f"Loaded: {key}=***")
        
        except Exception as e:
            logger.error(f"Error reading env file: {e}")
            raise
    
    def _sanitize_value(self, value: str) -> str:
        """Sanitize a configuration value."""
        # Remove any null bytes
        value = value.replace('\x00', '')
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        # Expand environment variable references
        # e.g., ${HOME} or $HOME
        def expand_var(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))
        
        value = re.sub(r'\$\{(\w+)\}|\$(\w+)', expand_var, value)
        
        return value
    
    def _load_yaml(self):
        """Load YAML configuration file."""
        if yaml is None:
            logger.warning("PyYAML not installed, skipping YAML config")
            return
        
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                self._yaml_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded YAML config from: {self.config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML syntax: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            raise
    
    def _get_env(self, key: str, default: str = "") -> str:
        """Get an environment variable with default."""
        return self._env_vars.get(key, default)
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get an environment variable as boolean."""
        value = self._get_env(key, str(default))
        return value.lower() in ('1', 'true', 'yes', 'on')
    
    def _get_env_float(self, key: str, default: float = 0.0) -> float:
        """Get an environment variable as float."""
        try:
            return float(self._get_env(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid float value for {key}, using default: {default}")
            return default
    
    def _get_env_int(self, key: str, default: int = 0) -> int:
        """Get an environment variable as integer."""
        try:
            return int(self._get_env(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid int value for {key}, using default: {default}")
            return default
    
    def _build_config(self) -> SecureConfig:
        """Build the SecureConfig object from loaded values."""
        return SecureConfig(
            # Platform credentials
            poly_private_key=self._get_env('POLY_PRIVATE_KEY'),
            poly_rpc_url=self._get_env('POLY_RPC_URL'),
            kalshi_api_key=self._get_env('KALSHI_API_KEY'),
            kalshi_api_secret=self._get_env('KALSHI_API_SECRET'),
            manifold_api_key=self._get_env('MANIFOLD_API_KEY'),
            manifold_username=self._get_env('MANIFOLD_USERNAME'),
            predictit_api_token=self._get_env('PREDICTIT_API_TOKEN'),
            
            # AI credentials
            openai_api_key=self._get_env('OPENAI_API_KEY'),
            anthropic_api_key=self._get_env('ANTHROPIC_API_KEY'),
            xai_api_key=self._get_env('XAI_API_KEY'),
            valyu_api_key=self._get_env('VALYU_API_KEY'),
            
            # System settings
            dry_run=self._get_env_bool('DRY_RUN', True),
            log_level=self._get_env('LOG_LEVEL', 'INFO'),
            
            # Feature flags
            enable_arb=self._get_env_bool('ENABLE_ARB', True),
            enable_mm_polymarket=self._get_env_bool('ENABLE_MM_POLYMARKET', True),
            enable_mm_manifold=self._get_env_bool('ENABLE_MM_MANIFOLD', True),
            enable_spike=self._get_env_bool('ENABLE_SPIKE', True),
            enable_ai=self._get_env_bool('ENABLE_AI', True),
            
            # Risk management
            max_daily_loss=self._get_env_float('MAX_DAILY_LOSS', 100.0),
            max_total_position=self._get_env_float('MAX_TOTAL_POSITION', 1000.0),
            circuit_breaker_threshold=self._get_env_int('CIRCUIT_BREAKER_THRESHOLD', 5),
            circuit_breaker_cooldown=self._get_env_int('CIRCUIT_BREAKER_COOLDOWN', 300),
            
            # Strategy config from YAML
            strategy_config=self._yaml_config
        )


def load_config(env_path: Optional[str] = None, 
                config_path: Optional[str] = None) -> SecureConfig:
    """
    Convenience function to load configuration.
    
    Args:
        env_path: Path to .env file
        config_path: Path to config.yml file
    
    Returns:
        SecureConfig object with all configuration
    """
    loader = ConfigLoader(env_path, config_path)
    return loader.load()


if __name__ == '__main__':
    # Test the configuration loader
    import json
    
    logging.basicConfig(level=logging.DEBUG)
    
    config = load_config(
        env_path='.env',
        config_path='config/config.yml'
    )
    
    print("\nConfiguration Status:")
    print(json.dumps(config.get_status_summary(), indent=2))
