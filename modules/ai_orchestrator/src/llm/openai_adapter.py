"""
PredictBot AI Orchestrator - OpenAI Adapter
============================================

Adapter for OpenAI API (GPT-4, GPT-3.5).
"""

from typing import Any, Dict, List, Optional
import asyncio

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIAdapter:
    """
    Adapter for OpenAI API.
    
    Provides access to GPT-4 and GPT-3.5 models for high-quality
    reasoning and analysis tasks.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the OpenAI adapter.
        
        Args:
            config: ProviderConfig instance
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed")
        
        self.api_key = config.api_key
        self.model = config.default_model or "gpt-4-turbo-preview"
        self.timeout = config.timeout or 60.0
        self.max_retries = config.max_retries or 3
        
        # Initialize client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        # Model name for tracking
        self.model_name = f"openai/{self.model}"
    
    def set_model(self, model: str) -> None:
        """Set the model to use."""
        self.model = model
        self.model_name = f"openai/{model}"
    
    async def ainvoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> 'OpenAIResponse':
        """
        Invoke the OpenAI model asynchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            OpenAIResponse object
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return OpenAIResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
    
    async def check_health(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Simple models list call to verify API key
            await self.client.models.list()
            return True
        except Exception:
            return False


class OpenAIResponse:
    """Response object from OpenAI API."""
    
    def __init__(self, content: str, model: str, usage: Dict[str, int]):
        self.content = content
        self.model = model
        self.usage = usage
    
    def __str__(self) -> str:
        return self.content
