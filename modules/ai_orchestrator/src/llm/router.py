"""
PredictBot AI Orchestrator - LLM Router
========================================

This module provides intelligent routing of LLM requests to appropriate
providers based on task type, cost, and availability.

Routing Strategy (Updated for OpenRouter):
- Primary: OpenRouter for all cloud LLM requests (unified API gateway)
- Fallback: Ollama for local inference when OpenRouter unavailable
- OpenRouter provides automatic model fallback via `models` array

Benefits of OpenRouter:
- Single API key for 100+ models (Claude, GPT-4, Llama, Mistral, etc.)
- Automatic fallback between models on rate limits/errors
- Unified cost tracking across all providers
- OpenAI-compatible API format
"""

import os
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from shared.logging_config import get_logger
    from shared.metrics import get_metrics_registry
except ImportError:
    import logging
    def get_logger(name: str, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_metrics_registry():
        return None


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENROUTER = "openrouter"  # Primary - unified API gateway
    OLLAMA = "ollama"          # Fallback - local inference
    # Legacy providers (deprecated, use OpenRouter instead)
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class TaskType(str, Enum):
    """Task types for routing decisions."""
    FAST = "fast"           # Quick analysis, low latency needed
    ANALYSIS = "analysis"   # Market analysis, moderate complexity
    REASONING = "reasoning" # Complex reasoning, forecasting
    CRITIQUE = "critique"   # Adversarial review
    DEFAULT = "default"     # General purpose


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = ""
    models: List[str] = field(default_factory=list)
    monthly_budget: float = 0.0  # 0 = unlimited
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_retries: int = 3
    timeout: float = 60.0


@dataclass
class UsageRecord:
    """Record of LLM usage for cost tracking."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime


class CostTracker:
    """
    Tracks LLM API costs across providers.
    
    Maintains running totals and enforces budget limits.
    """
    
    def __init__(self):
        self.logger = get_logger("llm.cost_tracker")
        self._usage_records: List[UsageRecord] = []
        self._monthly_totals: Dict[str, float] = {}
        self._current_month = datetime.utcnow().strftime("%Y-%m")
    
    def add(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ) -> None:
        """Record usage and cost."""
        # Check if we've moved to a new month
        current_month = datetime.utcnow().strftime("%Y-%m")
        if current_month != self._current_month:
            self._monthly_totals = {}
            self._current_month = current_month
        
        # Record usage
        record = UsageRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            timestamp=datetime.utcnow()
        )
        self._usage_records.append(record)
        
        # Update monthly total
        self._monthly_totals[provider] = self._monthly_totals.get(provider, 0) + cost
        
        self.logger.debug(
            f"LLM usage: {provider}/{model} - {input_tokens}+{output_tokens} tokens, ${cost:.4f}"
        )
    
    def get_monthly_spend(self, provider: str) -> float:
        """Get current month's spend for a provider."""
        return self._monthly_totals.get(provider, 0.0)
    
    def get_total_spend(self) -> float:
        """Get total spend across all providers this month."""
        return sum(self._monthly_totals.values())
    
    def check_budget(self, provider: str, budget: float) -> bool:
        """Check if provider is within budget."""
        if budget <= 0:
            return True  # No budget limit
        return self.get_monthly_spend(provider) < budget
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "current_month": self._current_month,
            "monthly_totals": self._monthly_totals.copy(),
            "total_spend": self.get_total_spend(),
            "total_records": len(self._usage_records)
        }


class LLMRouter:
    """
    Routes LLM requests to appropriate providers based on task type.
    
    Features:
    - OpenRouter as primary provider (unified API gateway for 100+ models)
    - Ollama as local fallback for privacy/cost savings
    - Task-based model selection with automatic fallback
    - Cost tracking and budget enforcement
    - Provider health monitoring
    
    OpenRouter Benefits:
    - Single API key for Claude, GPT-4, Llama, Mistral, and more
    - Automatic model fallback on rate limits/errors
    - Unified cost tracking across all providers
    """
    
    # Default routing configuration - OpenRouter primary, Ollama fallback
    DEFAULT_ROUTING = {
        TaskType.FAST: [LLMProvider.OPENROUTER, LLMProvider.OLLAMA],
        TaskType.ANALYSIS: [LLMProvider.OPENROUTER, LLMProvider.OLLAMA],
        TaskType.REASONING: [LLMProvider.OPENROUTER, LLMProvider.OLLAMA],
        TaskType.CRITIQUE: [LLMProvider.OPENROUTER, LLMProvider.OLLAMA],
        TaskType.DEFAULT: [LLMProvider.OPENROUTER, LLMProvider.OLLAMA],
    }
    
    # OpenRouter model configurations with automatic fallback
    OPENROUTER_MODELS = {
        TaskType.FAST: {
            "primary": "anthropic/claude-3-haiku",
            "fallbacks": ["openai/gpt-3.5-turbo", "meta-llama/llama-3.1-8b-instruct"]
        },
        TaskType.ANALYSIS: {
            "primary": "anthropic/claude-3.5-sonnet",
            "fallbacks": ["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"]
        },
        TaskType.REASONING: {
            "primary": "anthropic/claude-3.5-sonnet",
            "fallbacks": ["openai/gpt-4-turbo", "anthropic/claude-3-opus"]
        },
        TaskType.CRITIQUE: {
            "primary": "meta-llama/llama-3.1-70b-instruct",
            "fallbacks": ["mistralai/mixtral-8x22b-instruct", "openai/gpt-4-turbo"]
        },
        TaskType.DEFAULT: {
            "primary": "anthropic/claude-3.5-sonnet",
            "fallbacks": ["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"]
        },
    }
    
    # Model recommendations per provider (including legacy providers)
    RECOMMENDED_MODELS = {
        LLMProvider.OPENROUTER: {
            TaskType.FAST: "anthropic/claude-3-haiku",
            TaskType.ANALYSIS: "anthropic/claude-3.5-sonnet",
            TaskType.REASONING: "anthropic/claude-3.5-sonnet",
            TaskType.CRITIQUE: "meta-llama/llama-3.1-70b-instruct",
            TaskType.DEFAULT: "anthropic/claude-3.5-sonnet",
        },
        LLMProvider.OLLAMA: {
            TaskType.FAST: "llama3.2:3b",
            TaskType.ANALYSIS: "llama3.1:8b",
            TaskType.REASONING: "qwen2.5:32b",
            TaskType.CRITIQUE: "llama3.1:8b",
            TaskType.DEFAULT: "llama3.1:8b",
        },
        # Legacy providers (deprecated)
        LLMProvider.OPENAI: {
            TaskType.FAST: "gpt-3.5-turbo",
            TaskType.ANALYSIS: "gpt-4-turbo-preview",
            TaskType.REASONING: "gpt-4-turbo-preview",
            TaskType.CRITIQUE: "gpt-4-turbo-preview",
            TaskType.DEFAULT: "gpt-4-turbo-preview",
        },
        LLMProvider.ANTHROPIC: {
            TaskType.FAST: "claude-3-haiku-20240307",
            TaskType.ANALYSIS: "claude-3-sonnet-20240229",
            TaskType.REASONING: "claude-3-opus-20240229",
            TaskType.CRITIQUE: "claude-3-opus-20240229",
            TaskType.DEFAULT: "claude-3-sonnet-20240229",
        },
        LLMProvider.GROQ: {
            TaskType.FAST: "llama-3.1-8b-instant",
            TaskType.ANALYSIS: "llama-3.1-70b-versatile",
            TaskType.REASONING: "llama-3.1-70b-versatile",
            TaskType.CRITIQUE: "llama-3.1-70b-versatile",
            TaskType.DEFAULT: "llama-3.1-8b-instant",
        },
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM router.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = get_logger("llm.router")
        self.metrics = get_metrics_registry()
        self.cost_tracker = CostTracker()
        
        # Initialize provider configurations
        self.providers: Dict[str, ProviderConfig] = {}
        self._adapters: Dict[str, Any] = {}
        self._provider_health: Dict[str, bool] = {}
        
        # Load configuration
        self._load_config(config or {})
        
        # Initialize adapters
        self._init_adapters()
        
        self.logger.info(f"LLM Router initialized with providers: {list(self.providers.keys())}")
    
    def _load_config(self, config: Dict[str, Any]) -> None:
        """Load provider configurations from config and environment."""
        
        # OpenRouter configuration (PRIMARY - unified API gateway)
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        openrouter_enabled = os.environ.get("OPENROUTER_ENABLED", "true").lower() == "true"
        self.providers[LLMProvider.OPENROUTER] = ProviderConfig(
            name=LLMProvider.OPENROUTER,
            enabled=bool(openrouter_key) and openrouter_enabled,
            api_key=openrouter_key,
            base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_model=os.environ.get("LLM_MODEL_DEFAULT", "anthropic/claude-3.5-sonnet"),
            models=[
                "anthropic/claude-3.5-sonnet",
                "anthropic/claude-3-haiku",
                "anthropic/claude-3-opus",
                "openai/gpt-4-turbo",
                "openai/gpt-3.5-turbo",
                "meta-llama/llama-3.1-70b-instruct",
                "meta-llama/llama-3.1-8b-instruct",
                "mistralai/mixtral-8x22b-instruct",
            ],
            monthly_budget=float(os.environ.get("OPENROUTER_MONTHLY_BUDGET", "100")),
            cost_per_1k_input=0.003,  # Average across models
            cost_per_1k_output=0.015,
            timeout=float(os.environ.get("OPENROUTER_TIMEOUT", "60")),
        )
        
        # Ollama configuration (FALLBACK - local inference)
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_enabled = os.environ.get("OLLAMA_ENABLED", "true").lower() == "true"
        self.providers[LLMProvider.OLLAMA] = ProviderConfig(
            name=LLMProvider.OLLAMA,
            enabled=ollama_enabled,
            base_url=ollama_url,
            default_model="llama3.1:8b",
            models=["llama3.2:3b", "llama3.1:8b", "qwen2.5:32b"],
            monthly_budget=0,  # Local, no cost
        )
        
        # Legacy providers (deprecated - use OpenRouter instead)
        # These are kept for backward compatibility but disabled by default
        
        # OpenAI configuration (deprecated)
        openai_key = os.environ.get("OPENAI_API_KEY")
        self.providers[LLMProvider.OPENAI] = ProviderConfig(
            name=LLMProvider.OPENAI,
            enabled=bool(openai_key) and not openrouter_enabled,  # Disabled if OpenRouter is enabled
            api_key=openai_key,
            default_model="gpt-4-turbo-preview",
            models=["gpt-3.5-turbo", "gpt-4-turbo-preview", "gpt-4"],
            monthly_budget=float(os.environ.get("OPENAI_MONTHLY_BUDGET", "50")),
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
        )
        
        # Anthropic configuration (deprecated)
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.providers[LLMProvider.ANTHROPIC] = ProviderConfig(
            name=LLMProvider.ANTHROPIC,
            enabled=bool(anthropic_key) and not openrouter_enabled,
            api_key=anthropic_key,
            default_model="claude-3-sonnet-20240229",
            models=["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
            monthly_budget=float(os.environ.get("ANTHROPIC_MONTHLY_BUDGET", "30")),
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        
        # Groq configuration (deprecated)
        groq_key = os.environ.get("GROQ_API_KEY")
        self.providers[LLMProvider.GROQ] = ProviderConfig(
            name=LLMProvider.GROQ,
            enabled=bool(groq_key) and not openrouter_enabled,
            api_key=groq_key,
            default_model="llama-3.1-8b-instant",
            models=["llama-3.1-8b-instant", "llama-3.1-70b-versatile"],
            monthly_budget=float(os.environ.get("GROQ_MONTHLY_BUDGET", "10")),
            cost_per_1k_input=0.0001,
            cost_per_1k_output=0.0001,
        )
        
        # Mark all as healthy initially
        for provider in self.providers:
            self._provider_health[provider] = True
        
        # Log provider status
        enabled_providers = [p for p, c in self.providers.items() if c.enabled]
        self.logger.info(f"Enabled LLM providers: {enabled_providers}")
    
    def _init_adapters(self) -> None:
        """Initialize LLM adapters for each enabled provider."""
        from .ollama_adapter import OllamaAdapter
        from .openrouter_adapter import OpenRouterAdapter
        
        # Import legacy adapters only if needed
        legacy_adapters_imported = False
        OpenAIAdapter = None
        AnthropicAdapter = None
        GroqAdapter = None
        
        for provider_name, config in self.providers.items():
            if not config.enabled:
                continue
            
            try:
                if provider_name == LLMProvider.OPENROUTER:
                    # Configure OpenRouter with task-specific model and fallbacks
                    adapter = OpenRouterAdapter(config)
                    self._adapters[provider_name] = adapter
                    self.logger.info(f"Initialized OpenRouter adapter (primary provider)")
                    
                elif provider_name == LLMProvider.OLLAMA:
                    self._adapters[provider_name] = OllamaAdapter(config)
                    self.logger.info(f"Initialized Ollama adapter (local fallback)")
                    
                # Legacy providers (deprecated)
                elif provider_name == LLMProvider.OPENAI:
                    if not legacy_adapters_imported:
                        from .openai_adapter import OpenAIAdapter as OAI
                        from .anthropic_adapter import AnthropicAdapter as AA
                        from .groq_adapter import GroqAdapter as GA
                        OpenAIAdapter, AnthropicAdapter, GroqAdapter = OAI, AA, GA
                        legacy_adapters_imported = True
                    self._adapters[provider_name] = OpenAIAdapter(config)
                    self.logger.warning(f"Initialized legacy OpenAI adapter (deprecated, use OpenRouter)")
                    
                elif provider_name == LLMProvider.ANTHROPIC:
                    if not legacy_adapters_imported:
                        from .openai_adapter import OpenAIAdapter as OAI
                        from .anthropic_adapter import AnthropicAdapter as AA
                        from .groq_adapter import GroqAdapter as GA
                        OpenAIAdapter, AnthropicAdapter, GroqAdapter = OAI, AA, GA
                        legacy_adapters_imported = True
                    self._adapters[provider_name] = AnthropicAdapter(config)
                    self.logger.warning(f"Initialized legacy Anthropic adapter (deprecated, use OpenRouter)")
                    
                elif provider_name == LLMProvider.GROQ:
                    if not legacy_adapters_imported:
                        from .openai_adapter import OpenAIAdapter as OAI
                        from .anthropic_adapter import AnthropicAdapter as AA
                        from .groq_adapter import GroqAdapter as GA
                        OpenAIAdapter, AnthropicAdapter, GroqAdapter = OAI, AA, GA
                        legacy_adapters_imported = True
                    self._adapters[provider_name] = GroqAdapter(config)
                    self.logger.warning(f"Initialized legacy Groq adapter (deprecated, use OpenRouter)")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider_name} adapter: {e}")
                self._provider_health[provider_name] = False
    
    def get_llm_for_task(self, task_type: str) -> Any:
        """
        Get an LLM instance appropriate for the given task type.
        
        Args:
            task_type: Type of task (fast, analysis, reasoning, critique, default)
            
        Returns:
            LLM adapter instance
            
        Raises:
            RuntimeError: If no suitable provider is available
        """
        # Convert string to enum
        try:
            task = TaskType(task_type)
        except ValueError:
            task = TaskType.DEFAULT
        
        # Get routing order for this task
        routing_order = self.DEFAULT_ROUTING.get(task, self.DEFAULT_ROUTING[TaskType.DEFAULT])
        
        # Try each provider in order
        for provider in routing_order:
            if self._can_use_provider(provider):
                adapter = self._adapters.get(provider)
                if adapter:
                    # Configure model based on provider type
                    if provider == LLMProvider.OPENROUTER:
                        # Set primary model and fallbacks for OpenRouter
                        model_config = self.OPENROUTER_MODELS.get(task, self.OPENROUTER_MODELS[TaskType.DEFAULT])
                        adapter.set_model(model_config["primary"])
                        adapter.set_fallbacks(model_config["fallbacks"])
                        self.logger.debug(
                            f"Routing {task_type} task to OpenRouter: "
                            f"primary={model_config['primary']}, fallbacks={model_config['fallbacks']}"
                        )
                    else:
                        # Set the recommended model for legacy providers
                        model = self.RECOMMENDED_MODELS.get(provider, {}).get(task)
                        if model:
                            adapter.set_model(model)
                        self.logger.debug(f"Routing {task_type} task to {provider}")
                    
                    return adapter
        
        # No provider available
        raise RuntimeError(f"No LLM provider available for task type: {task_type}")
    
    def _can_use_provider(self, provider: str) -> bool:
        """Check if a provider can be used."""
        config = self.providers.get(provider)
        if not config or not config.enabled:
            return False
        
        # Check health
        if not self._provider_health.get(provider, False):
            return False
        
        # Check budget
        if not self.cost_tracker.check_budget(provider, config.monthly_budget):
            self.logger.warning(f"Provider {provider} over budget")
            return False
        
        return True
    
    def mark_provider_unhealthy(self, provider: str) -> None:
        """Mark a provider as unhealthy after failures."""
        self._provider_health[provider] = False
        self.logger.warning(f"Provider {provider} marked as unhealthy")
    
    def mark_provider_healthy(self, provider: str) -> None:
        """Mark a provider as healthy."""
        self._provider_health[provider] = True
        self.logger.info(f"Provider {provider} marked as healthy")
    
    def track_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """Track LLM usage and costs."""
        config = self.providers.get(provider)
        if not config:
            return
        
        # Calculate cost
        cost = (
            (input_tokens / 1000) * config.cost_per_1k_input +
            (output_tokens / 1000) * config.cost_per_1k_output
        )
        
        self.cost_tracker.add(provider, model, input_tokens, output_tokens, cost)
        
        # Update metrics
        if self.metrics:
            self.metrics.record_llm_call(
                model=f"{provider}/{model}",
                endpoint="chat",
                tokens_input=input_tokens,
                tokens_output=output_tokens
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "providers": {
                name: {
                    "enabled": config.enabled,
                    "healthy": self._provider_health.get(name, False),
                    "monthly_spend": self.cost_tracker.get_monthly_spend(name),
                    "budget": config.monthly_budget
                }
                for name, config in self.providers.items()
            },
            "cost_tracker": self.cost_tracker.get_stats()
        }
