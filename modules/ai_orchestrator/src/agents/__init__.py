"""
PredictBot AI Orchestrator - Agents Module
===========================================

This module contains the 6 specialized agents for the trading pipeline:

1. MarketAnalyst - Analyzes market structure, liquidity, and trends
2. NewsSentiment - Processes news and social media for sentiment
3. Forecaster - Generates probability forecasts
4. Critic - Validates and challenges forecasts
5. RiskAssessor - Evaluates trade risk and position sizing
6. TradeExecutor - Determines execution parameters
"""

from .base import BaseAgent
from .market_analyst import MarketAnalystAgent
from .news_sentiment import NewsSentimentAgent
from .forecaster import ForecasterAgent
from .critic import CriticAgent
from .risk_assessor import RiskAssessorAgent
from .trade_executor import TradeExecutorAgent

__all__ = [
    "BaseAgent",
    "MarketAnalystAgent",
    "NewsSentimentAgent",
    "ForecasterAgent",
    "CriticAgent",
    "RiskAssessorAgent",
    "TradeExecutorAgent",
]
