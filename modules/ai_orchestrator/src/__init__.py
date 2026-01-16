"""
PredictBot AI Orchestrator
===========================

LangGraph-based multi-agent system for prediction market trading.

This module provides:
- 6 specialized trading agents (market analyst, news sentiment, forecaster, critic, risk assessor, trade executor)
- Multi-LLM provider support (Ollama, OpenAI, Anthropic, Groq)
- Redis-backed state checkpointing
- FastAPI endpoints for control and monitoring
"""

__version__ = "0.1.0"
__author__ = "PredictBot Team"
