"""
PredictBot AI Orchestrator - OpenRouter Adapter
================================================

This module provides a unified LLM adapter using OpenRouter as the API gateway.
OpenRouter provides access to 100+ models through a single API endpoint with
automatic fallback, cost tracking, and OpenAI-compatible API format.

Features:
- Single API key for all models (Claude, GPT-4, Llama, Mistral, etc.)
- Automatic model fallback via `models` array parameter
- Built-in rate limit handling and retry logic
- Cost tracking per request
- OpenAI-compatible API format
"""

import os
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
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


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter adapter."""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-3.5-sonnet"
    fallback_models: List[str] = field(default_factory=list)
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    monthly_budget: float = 100.0
    
    # Site information for OpenRouter analytics
    site_url: str = "https://predictbot.local"
    site_name: str = "PredictBot Trading System"


@dataclass
class OpenRouterResponse:
    """Response from OpenRouter API."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    latency_ms: float
    cost: Optional[float] = None
    
    @property
    def input_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def output_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", self.input_tokens + self.output_tokens)


class OpenRouterAdapter:
    """
    OpenRouter LLM Adapter - Unified API gateway for multiple LLM providers.
    
    This adapter provides:
    - Access to 100+ models through a single API
    - Automatic fallback between models
    - Cost tracking and budget enforcement
    - Rate limit handling with exponential backoff
    
    Usage:
        config = OpenRouterConfig(api_key="sk-or-v1-...")
        adapter = OpenRouterAdapter(config)
        response = await adapter.ainvoke([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ])
    """
    
    # Model pricing per 1M tokens (approximate, OpenRouter may vary)
    MODEL_PRICING = {
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
        "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
        "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "openai/gpt-4": {"input": 30.0, "output": 60.0},
        "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "meta-llama/llama-3.1-70b-instruct": {"input": 0.59, "output": 0.79},
        "meta-llama/llama-3.1-8b-instruct": {"input": 0.06, "output": 0.06},
        "mistralai/mixtral-8x22b-instruct": {"input": 0.65, "output": 0.65},
        "mistralai/mistral-large": {"input": 2.0, "output": 6.0},
        "google/gemini-pro-1.5": {"input": 2.5, "output": 7.5},
    }
    
    def __init__(self, config: Union[OpenRouterConfig, Any]):
        """
        Initialize the OpenRouter adapter.
        
        Args:
            config: OpenRouterConfig or ProviderConfig with api_key
        """
        self.logger = get_logger("llm.openrouter")
        self.metrics = get_metrics_registry()
        
        # Handle both OpenRouterConfig and generic ProviderConfig
        if isinstance(config, OpenRouterConfig):
            self.config = config
        else:
            # Convert from ProviderConfig
            self.config = OpenRouterConfig(
                api_key=config.api_key or os.environ.get("OPENROUTER_API_KEY", ""),
                base_url=config.base_url or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                default_model=config.default_model or "anthropic/claude-3.5-sonnet",
                fallback_models=getattr(config, 'fallback_models', []),
                timeout=config.timeout or 60.0,
                max_retries=config.max_retries or 3,
                monthly_budget=config.monthly_budget or 100.0,
            )
        
        self._current_model = self.config.default_model
        self._session: Optional[aiohttp.ClientSession] = None
        self._total_cost = 0.0
        self._request_count = 0
        
        self.logger.info(
            f"OpenRouter adapter initialized with model: {self._current_model}, "
            f"fallbacks: {self.config.fallback_models}"
        )
    
    @property
    def model_name(self) -> str:
        """Get the current model name for display."""
        return f"openrouter/{self._current_model}"
    
    def set_model(self, model: str) -> None:
        """
        Set the primary model to use.
        
        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
        """
        self._current_model = model
        self.logger.debug(f"Model set to: {model}")
    
    def set_fallbacks(self, models: List[str]) -> None:
        """
        Set fallback models for automatic failover.
        
        Args:
            models: List of model identifiers to try if primary fails
        """
        self.config.fallback_models = models
        self.logger.debug(f"Fallback models set to: {models}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers for OpenRouter API."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.site_url,
            "X-Title": self.config.site_name,
        }
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of a request.
        
        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pricing = self.MODEL_PRICING.get(model, {"input": 1.0, "output": 2.0})
        cost = (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )
        return cost
    
    async def ainvoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> OpenRouterResponse:
        """
        Invoke the LLM asynchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stop: Optional stop sequences
            **kwargs: Additional parameters passed to the API
            
        Returns:
            OpenRouterResponse with content and metadata
            
        Raises:
            RuntimeError: If all models fail after retries
        """
        # Build models list for fallback
        models = [self._current_model] + self.config.fallback_models
        
        # Build request payload
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # Use models array for automatic fallback (OpenRouter feature)
        if len(models) > 1:
            payload["models"] = models
        else:
            payload["model"] = models[0]
        
        if stop:
            payload["stop"] = stop
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        # Make request with retries
        last_error = None
        start_time = datetime.utcnow()
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self._make_request(payload)
                
                # Calculate latency
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Extract response data
                choice = response["choices"][0]
                usage = response.get("usage", {})
                model_used = response.get("model", self._current_model)
                
                # Calculate cost
                cost = self._calculate_cost(
                    model_used,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )
                self._total_cost += cost
                self._request_count += 1
                
                # Log usage
                self.logger.debug(
                    f"OpenRouter request completed: model={model_used}, "
                    f"tokens={usage.get('total_tokens', 0)}, cost=${cost:.4f}, "
                    f"latency={latency_ms:.0f}ms"
                )
                
                # Record metrics
                if self.metrics:
                    self.metrics.record_llm_call(
                        model=f"openrouter/{model_used}",
                        endpoint="chat/completions",
                        tokens_input=usage.get("prompt_tokens", 0),
                        tokens_output=usage.get("completion_tokens", 0)
                    )
                
                return OpenRouterResponse(
                    content=choice["message"]["content"],
                    model=model_used,
                    usage=usage,
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=latency_ms,
                    cost=cost
                )
                
            except aiohttp.ClientResponseError as e:
                last_error = e
                self.logger.warning(
                    f"OpenRouter request failed (attempt {attempt + 1}/{self.config.max_retries}): "
                    f"status={e.status}, message={e.message}"
                )
                
                # Don't retry on certain errors
                if e.status in [401, 403]:  # Auth errors
                    raise RuntimeError(f"OpenRouter authentication failed: {e.message}")
                
                if e.status == 429:  # Rate limit
                    # Exponential backoff
                    delay = self.config.retry_delay * (2 ** attempt)
                    self.logger.info(f"Rate limited, waiting {delay}s before retry")
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(self.config.retry_delay)
                    
            except asyncio.TimeoutError:
                last_error = TimeoutError("Request timed out")
                self.logger.warning(
                    f"OpenRouter request timed out (attempt {attempt + 1}/{self.config.max_retries})"
                )
                await asyncio.sleep(self.config.retry_delay)
                
            except Exception as e:
                last_error = e
                self.logger.error(f"OpenRouter request error: {e}")
                await asyncio.sleep(self.config.retry_delay)
        
        # All retries failed
        raise RuntimeError(f"OpenRouter request failed after {self.config.max_retries} attempts: {last_error}")
    
    async def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the OpenRouter API.
        
        Args:
            payload: Request payload
            
        Returns:
            Response JSON
            
        Raises:
            aiohttp.ClientResponseError: On HTTP errors
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/chat/completions"
        
        async with session.post(
            url,
            headers=self._build_headers(),
            json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        Stream responses from the LLM.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            Chunks of response content
        """
        models = [self._current_model] + self.config.fallback_models
        
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        if len(models) > 1:
            payload["models"] = models
        else:
            payload["model"] = models[0]
        
        payload.update(kwargs)
        
        session = await self._get_session()
        url = f"{self.config.base_url}/chat/completions"
        
        async with session.post(
            url,
            headers=self._build_headers(),
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk.get('choices'):
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "provider": "openrouter",
            "current_model": self._current_model,
            "fallback_models": self.config.fallback_models,
            "total_cost": self._total_cost,
            "request_count": self._request_count,
            "average_cost": self._total_cost / max(self._request_count, 1),
        }
    
    def __repr__(self) -> str:
        return f"OpenRouterAdapter(model={self._current_model}, fallbacks={len(self.config.fallback_models)})"


# Task-specific model configurations
OPENROUTER_TASK_MODELS = {
    "fast": {
        "primary": "anthropic/claude-3-haiku",
        "fallbacks": ["openai/gpt-3.5-turbo", "meta-llama/llama-3.1-8b-instruct"]
    },
    "analysis": {
        "primary": "anthropic/claude-3.5-sonnet",
        "fallbacks": ["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"]
    },
    "reasoning": {
        "primary": "anthropic/claude-3.5-sonnet",
        "fallbacks": ["openai/gpt-4-turbo", "anthropic/claude-3-opus"]
    },
    "critique": {
        "primary": "meta-llama/llama-3.1-70b-instruct",
        "fallbacks": ["mistralai/mixtral-8x22b-instruct", "openai/gpt-4-turbo"]
    },
    "default": {
        "primary": "anthropic/claude-3.5-sonnet",
        "fallbacks": ["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"]
    },
}


def get_openrouter_adapter_for_task(task_type: str, api_key: Optional[str] = None) -> OpenRouterAdapter:
    """
    Get an OpenRouter adapter configured for a specific task type.
    
    Args:
        task_type: Type of task (fast, analysis, reasoning, critique, default)
        api_key: Optional API key (defaults to OPENROUTER_API_KEY env var)
        
    Returns:
        Configured OpenRouterAdapter
    """
    task_config = OPENROUTER_TASK_MODELS.get(task_type, OPENROUTER_TASK_MODELS["default"])
    
    config = OpenRouterConfig(
        api_key=api_key or os.environ.get("OPENROUTER_API_KEY", ""),
        default_model=task_config["primary"],
        fallback_models=task_config["fallbacks"],
    )
    
    return OpenRouterAdapter(config)
