"""
PredictBot AI Orchestrator - Ollama Adapter
============================================

Adapter for local Ollama LLM server with GPU acceleration.
"""

from typing import Any, Dict, List, Optional
import httpx
import asyncio
import json


class OllamaAdapter:
    """
    Adapter for Ollama local LLM server.
    
    Ollama provides local GPU-accelerated inference for open-source models.
    This adapter wraps the Ollama API for use with the LLM router.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the Ollama adapter.
        
        Args:
            config: ProviderConfig instance
        """
        self.base_url = config.base_url or "http://localhost:11434"
        self.model = config.default_model or "llama3.1:8b"
        self.timeout = config.timeout or 60.0
        self.max_retries = config.max_retries or 3
        
        # Model name for tracking
        self.model_name = f"ollama/{self.model}"
    
    def set_model(self, model: str) -> None:
        """Set the model to use."""
        self.model = model
        self.model_name = f"ollama/{model}"
    
    async def ainvoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> 'OllamaResponse':
        """
        Invoke the Ollama model asynchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            OllamaResponse object
        """
        # Convert messages to Ollama format
        prompt = self._format_messages(messages)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    return OllamaResponse(
                        content=data.get("response", ""),
                        model=self.model,
                        usage={
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                        }
                    )
                    
                except httpx.TimeoutException:
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))
                    
                except httpx.HTTPStatusError as e:
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages for Ollama prompt.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Formatted prompt string
        """
        parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                parts.append(f"System: {content}\n")
            elif role == "assistant":
                parts.append(f"Assistant: {content}\n")
            else:
                parts.append(f"User: {content}\n")
        
        parts.append("Assistant: ")
        return "".join(parts)
    
    async def check_health(self) -> bool:
        """Check if Ollama server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []


class OllamaResponse:
    """Response object from Ollama API."""
    
    def __init__(self, content: str, model: str, usage: Dict[str, int]):
        self.content = content
        self.model = model
        self.usage = usage
    
    def __str__(self) -> str:
        return self.content
