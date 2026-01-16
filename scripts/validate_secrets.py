#!/usr/bin/env python3
"""
PredictBot Stack - Secrets Validator

This script validates that all required API keys and secrets are present
in the environment or .env file, and performs basic format validation.

Usage:
    python scripts/validate_secrets.py [--env path/to/.env]
"""

import sys
import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SecretDefinition:
    """Definition of a secret/environment variable."""
    name: str
    required: bool
    description: str
    pattern: Optional[str] = None  # Regex pattern for validation
    min_length: Optional[int] = None
    depends_on: Optional[str] = None  # Only required if this env var is set


# Define all secrets and their validation rules
SECRET_DEFINITIONS: List[SecretDefinition] = [
    # Polymarket
    SecretDefinition(
        name="POLY_PRIVATE_KEY",
        required=True,
        description="Ethereum wallet private key for Polymarket",
        pattern=r"^0x[a-fA-F0-9]{64}$",
        depends_on="ENABLE_ARB,ENABLE_MM_POLYMARKET,ENABLE_SPIKE"
    ),
    SecretDefinition(
        name="POLY_RPC_URL",
        required=True,
        description="Polygon RPC endpoint URL",
        pattern=r"^https?://",
        depends_on="ENABLE_ARB,ENABLE_MM_POLYMARKET,ENABLE_SPIKE"
    ),
    
    # Kalshi
    SecretDefinition(
        name="KALSHI_API_KEY",
        required=True,
        description="Kalshi API key",
        min_length=10,
        depends_on="ENABLE_ARB,ENABLE_AI"
    ),
    SecretDefinition(
        name="KALSHI_API_SECRET",
        required=True,
        description="Kalshi API secret",
        min_length=10,
        depends_on="ENABLE_ARB,ENABLE_AI"
    ),
    
    # Manifold
    SecretDefinition(
        name="MANIFOLD_API_KEY",
        required=True,
        description="Manifold Markets API key",
        min_length=10,
        depends_on="ENABLE_MM_MANIFOLD"
    ),
    SecretDefinition(
        name="MANIFOLD_USERNAME",
        required=True,
        description="Manifold Markets username",
        min_length=1,
        depends_on="ENABLE_MM_MANIFOLD"
    ),
    
    # PredictIt (optional)
    SecretDefinition(
        name="PREDICTIT_API_TOKEN",
        required=False,
        description="PredictIt API token",
        min_length=10,
        depends_on="ARB_INCLUDE_PREDICTIT"
    ),
    
    # AI Services
    SecretDefinition(
        name="OPENAI_API_KEY",
        required=False,
        description="OpenAI API key for GPT models",
        pattern=r"^sk-[a-zA-Z0-9]{20,}$",
        depends_on="ENABLE_AI"
    ),
    SecretDefinition(
        name="ANTHROPIC_API_KEY",
        required=False,
        description="Anthropic API key for Claude",
        pattern=r"^sk-ant-",
        depends_on="ENABLE_AI"
    ),
    SecretDefinition(
        name="XAI_API_KEY",
        required=False,
        description="xAI API key for Grok",
        min_length=10,
        depends_on="ENABLE_AI"
    ),
    
    # Polyseer
    SecretDefinition(
        name="VALYU_API_KEY",
        required=False,
        description="Valyu API key for Polyseer",
        min_length=10,
        depends_on="POLYSEER_ENABLED"
    ),
]


class SecretsValidator:
    """Validates environment secrets for PredictBot."""
    
    def __init__(self, env_path: Optional[str] = None):
        self.env_path = Path(env_path) if env_path else None
        self.env_vars: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def load_env_file(self) -> bool:
        """Load environment variables from .env file."""
        # First, copy current environment
        self.env_vars = dict(os.environ)
        
        # Then load from .env file if specified
        if self.env_path:
            if not self.env_path.exists():
                self.errors.append(f"Environment file not found: {self.env_path}")
                return False
            
            try:
                with open(self.env_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Parse KEY=VALUE
                        if '=' not in line:
                            self.warnings.append(
                                f"Line {line_num}: Invalid format (missing '=')"
                            )
                            continue
                        
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        self.env_vars[key] = value
                
                return True
            except Exception as e:
                self.errors.append(f"Error reading env file: {e}")
                return False
        
        return True
    
    def get_env(self, name: str, default: str = "") -> str:
        """Get an environment variable value."""
        return self.env_vars.get(name, default)
    
    def is_enabled(self, flag_names: str) -> bool:
        """Check if any of the given feature flags are enabled."""
        if not flag_names:
            return True
        
        for flag in flag_names.split(','):
            flag = flag.strip()
            value = self.get_env(flag, "0")
            if value.lower() in ('1', 'true', 'yes', 'on'):
                return True
        
        return False
    
    def validate_secret(self, secret: SecretDefinition) -> bool:
        """Validate a single secret."""
        value = self.get_env(secret.name)
        
        # Check if this secret is needed based on dependencies
        if secret.depends_on and not self.is_enabled(secret.depends_on):
            self.info.append(
                f"{secret.name}: Skipped (dependent features not enabled)"
            )
            return True
        
        # Check if required and missing
        if not value:
            if secret.required:
                self.errors.append(
                    f"{secret.name}: Missing required secret - {secret.description}"
                )
                return False
            else:
                self.info.append(
                    f"{secret.name}: Not set (optional)"
                )
                return True
        
        # Check for placeholder values
        placeholder_patterns = [
            r'your_.*_here',
            r'YOUR_.*',
            r'xxx+',
            r'placeholder',
            r'changeme',
            r'<.*>',
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                self.errors.append(
                    f"{secret.name}: Contains placeholder value - please set actual secret"
                )
                return False
        
        # Validate pattern if specified
        if secret.pattern:
            if not re.match(secret.pattern, value):
                self.errors.append(
                    f"{secret.name}: Invalid format - expected pattern: {secret.pattern}"
                )
                return False
        
        # Validate minimum length
        if secret.min_length and len(value) < secret.min_length:
            self.errors.append(
                f"{secret.name}: Too short - minimum {secret.min_length} characters"
            )
            return False
        
        # Mask the value for display
        masked = self._mask_value(value)
        self.info.append(f"{secret.name}: ✓ Set ({masked})")
        return True
    
    def _mask_value(self, value: str) -> str:
        """Mask a secret value for safe display."""
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]
    
    def check_ai_keys(self) -> None:
        """Check that at least one AI key is set if AI is enabled."""
        if not self.is_enabled("ENABLE_AI"):
            return
        
        ai_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'XAI_API_KEY']
        has_ai_key = any(self.get_env(key) for key in ai_keys)
        
        if not has_ai_key:
            self.errors.append(
                "AI trading is enabled but no AI API key is set. "
                "Please set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, XAI_API_KEY"
            )
    
    def check_security_warnings(self) -> None:
        """Check for potential security issues."""
        # Check if private key looks like it might be a mainnet key with funds
        private_key = self.get_env("POLY_PRIVATE_KEY")
        if private_key and private_key.startswith("0x"):
            self.warnings.append(
                "SECURITY: Ensure POLY_PRIVATE_KEY is for a dedicated trading wallet, "
                "not your main wallet. Never use a wallet with significant funds."
            )
        
        # Check if dry run is disabled
        dry_run = self.get_env("DRY_RUN", "1")
        if dry_run.lower() in ('0', 'false', 'no', 'off'):
            self.warnings.append(
                "CAUTION: DRY_RUN is disabled. The bot will execute real trades!"
            )
        
        # Check for weak passwords/tokens
        for secret in SECRET_DEFINITIONS:
            value = self.get_env(secret.name)
            if value and len(value) < 20 and 'KEY' in secret.name:
                self.warnings.append(
                    f"SECURITY: {secret.name} appears short. Verify it's correct."
                )
    
    def validate(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """Run all validations and return results."""
        if not self.load_env_file():
            return False, self.errors, self.warnings, self.info
        
        # Validate each secret
        for secret in SECRET_DEFINITIONS:
            self.validate_secret(secret)
        
        # Additional checks
        self.check_ai_keys()
        self.check_security_warnings()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings, self.info


def main():
    parser = argparse.ArgumentParser(
        description='Validate PredictBot secrets and API keys'
    )
    parser.add_argument(
        '--env', '-e',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--strict', '-s',
        action='store_true',
        help='Treat warnings as errors'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PredictBot Secrets Validator")
    print("=" * 60)
    print(f"\nValidating: {args.env}\n")
    
    validator = SecretsValidator(args.env)
    is_valid, errors, warnings, info = validator.validate()
    
    # Print info (if verbose)
    if args.verbose and info:
        print("ℹ️  STATUS:")
        print("-" * 40)
        for item in info:
            print(f"  {item}")
        print()
    
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
    
    # Summary
    print("-" * 40)
    enabled_features = []
    if validator.is_enabled("ENABLE_ARB"):
        enabled_features.append("Arbitrage")
    if validator.is_enabled("ENABLE_MM_POLYMARKET"):
        enabled_features.append("Polymarket MM")
    if validator.is_enabled("ENABLE_MM_MANIFOLD"):
        enabled_features.append("Manifold MM")
    if validator.is_enabled("ENABLE_SPIKE"):
        enabled_features.append("Spike Trading")
    if validator.is_enabled("ENABLE_AI"):
        enabled_features.append("AI Trading")
    
    if enabled_features:
        print(f"Enabled features: {', '.join(enabled_features)}")
    else:
        print("No features enabled (check ENABLE_* flags)")
    print()
    
    # Final result
    if is_valid and not (args.strict and warnings):
        print("✅ All required secrets are valid!")
        if warnings:
            print(f"   ({len(warnings)} warning(s) - review recommended)")
        sys.exit(0)
    else:
        print("❌ Secrets validation failed!")
        print(f"   {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)


if __name__ == '__main__':
    main()
