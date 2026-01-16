"""
PredictBot AI Orchestrator - Integrations Module
=================================================

This module provides clients for external services:
- MCP Server - Market data and trading operations
- Polyseer - Research and information retrieval
"""

from .mcp_client import MCPClient
from .polyseer_client import PolyseerClient

__all__ = [
    "MCPClient",
    "PolyseerClient",
]
