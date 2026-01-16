"""
PredictBot AI Orchestrator - Anthropic Adapter
===============================================

Adapter for Anthropic API (Claude models).
"""

from typing import Any, Dict, List, Optional
import asyncio

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicAdapter:
    """
    Adapter for Anthropic API.
    
    Provides access to Claude models for high-quality reasoning,
    particularly useful for critique and adversarial analysis.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the Anthropic adapter.
        
        Args:
            config: ProviderConfig instance
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package not installed")
        
        self.api_key = config.api_key
        self.model = config.default_model or "claude-3-sonnet-20240229"
        self.timeout = config.timeout or 60.0
        self.max_retries = config.max_retries or 3
        
        # Initialize client
        self.client = AsyncAnthropic(
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        # Model name for tracking
        self.model_name = f"anthropic/{self.model}"
    
    def set_model(self, model: str) -> None:
        """Set the model to use."""
        self.model = model
        self.model_name = f"anthropic/{model}"
    
    async def ainvoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> 'AnthropicResponse':
        """
        Invoke the Anthropic model asynchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            AnthropicResponse object
        """
        # Extract system message if present
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Ensure we have at least one user message
        if not chat_messages:
            chat_messages = [{"role": "user", "content": "Hello"}]
        
        # Build request kwargs
        request_kwargs = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_message:
            request_kwargs["system"] = system_message
        
        response = await self.client.messages.create(**request_kwargs)
        
        # Extract content from response
        content = ""
        if response.content:
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
        
        return AnthropicResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
            }
        )
    
    async def check_health(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Simple message to verify API key
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False


class AnthropicResponse:
    """Response object from Anthropic API."""
    
    def __init__(self, content: str, model: str, usage: Dict[str, int]):
        self.content = content
        self.model = model
        self.usage = usage
    
    def __str__(self) -> str:
        return self.content
