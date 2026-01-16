"""
PredictBot AI Orchestrator - LLM Module
========================================

This module provides multi-provider LLM support with intelligent routing.

Primary Provider:
- OpenRouter (unified API gateway for 100+ models)
  - Access to Claude, GPT-4, Llama, Mistral, and more
  - Single API key for all models
  - Automatic fallback between models

Fallback Provider:
- Ollama (local, GPU-accelerated)

Legacy Providers (deprecated, use OpenRouter instead):
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Groq (fast inference)
"""

from .router import LLMRouter, CostTracker
from .openrouter_adapter import OpenRouterAdapter, OpenRouterConfig, OPENROUTER_TASK_MODELS
from .ollama_adapter import OllamaAdapter

# Legacy adapters (deprecated)
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .groq_adapter import GroqAdapter

__all__ = [
    # Core
    "LLMRouter",
    "CostTracker",
    # Primary provider
    "OpenRouterAdapter",
    "OpenRouterConfig",
    "OPENROUTER_TASK_MODELS",
    # Fallback provider
    "OllamaAdapter",
    # Legacy providers (deprecated)
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GroqAdapter",
]
