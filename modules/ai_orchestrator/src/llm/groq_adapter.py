"""
PredictBot AI Orchestrator - Groq Adapter
==========================================

Adapter for Groq API (fast inference).
"""

from typing import Any, Dict, List, Optional
import asyncio

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqAdapter:
    """
    Adapter for Groq API.
    
    Groq provides extremely fast inference for open-source models,
    ideal for time-sensitive tasks like news analysis and quick decisions.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the Groq adapter.
        
        Args:
            config: ProviderConfig instance
        """
        if not GROQ_AVAILABLE:
            raise ImportError("groq package not installed")
        
        self.api_key = config.api_key
        self.model = config.default_model or "llama-3.1-8b-instant"
        self.timeout = config.timeout or 30.0  # Groq is fast, shorter timeout
        self.max_retries = config.max_retries or 3
        
        # Initialize client
        self.client = AsyncGroq(
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        # Model name for tracking
        self.model_name = f"groq/{self.model}"
    
    def set_model(self, model: str) -> None:
        """Set the model to use."""
        self.model = model
        self.model_name = f"groq/{model}"
    
    async def ainvoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> 'GroqResponse':
        """
        Invoke the Groq model asynchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            GroqResponse object
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return GroqResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )
    
    async def check_health(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            # Simple models list call to verify API key
            await self.client.models.list()
            return True
        except Exception:
            return False


class GroqResponse:
    """Response object from Groq API."""
    
    def __init__(self, content: str, model: str, usage: Dict[str, int]):
        self.content = content
        self.model = model
        self.usage = usage
    
    def __str__(self) -> str:
        return self.content
