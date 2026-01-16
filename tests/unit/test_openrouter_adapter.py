"""
Unit Tests - OpenRouter Adapter
===============================

Tests for the OpenRouter LLM adapter with automatic fallback.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.ai_orchestrator.src.llm.openrouter_adapter import (
    OpenRouterAdapter,
    OpenRouterConfig,
    OpenRouterResponse,
    get_openrouter_adapter_for_task,
    OPENROUTER_TASK_MODELS,
)


class TestOpenRouterConfig:
    """Tests for OpenRouterConfig dataclass."""
    
    def test_create_config(self):
        """Test creating OpenRouter config."""
        config = OpenRouterConfig(
            api_key="sk-or-test-key",
            default_model="anthropic/claude-3.5-sonnet",
            fallback_models=["openai/gpt-4-turbo", "meta-llama/llama-3.1-70b-instruct"],
            max_retries=3,
            timeout=30.0,
        )
        
        assert config.api_key == "sk-or-test-key"
        assert config.default_model == "anthropic/claude-3.5-sonnet"
        assert len(config.fallback_models) == 2
        assert config.max_retries == 3
    
    def test_config_defaults(self):
        """Test config default values."""
        config = OpenRouterConfig(api_key="test-key")
        
        assert config.default_model == "anthropic/claude-3.5-sonnet"
        assert config.max_retries == 3
        assert config.timeout == 60.0
        assert config.base_url == "https://openrouter.ai/api/v1"


class TestOpenRouterResponse:
    """Tests for OpenRouterResponse dataclass."""
    
    def test_create_response(self):
        """Test creating OpenRouter response."""
        response = OpenRouterResponse(
            content="This is the response content",
            model="anthropic/claude-3.5-sonnet",
            usage={
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75,
            },
            finish_reason="stop",
            latency_ms=500.0,
            cost=0.001,
        )
        
        assert response.content == "This is the response content"
        assert response.model == "anthropic/claude-3.5-sonnet"
        assert response.finish_reason == "stop"
    
    def test_response_token_properties(self):
        """Test response token properties."""
        response = OpenRouterResponse(
            content="Test",
            model="test",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            finish_reason="stop",
            latency_ms=100.0,
        )
        
        assert response.input_tokens == 100
        assert response.output_tokens == 50
        assert response.total_tokens == 150


class TestOpenRouterAdapter:
    """Tests for OpenRouterAdapter class."""
    
    @pytest.fixture
    def adapter(self):
        """Create an adapter for testing."""
        config = OpenRouterConfig(
            api_key="test-api-key",
            default_model="anthropic/claude-3.5-sonnet",
            fallback_models=["openai/gpt-4-turbo"],
        )
        return OpenRouterAdapter(config)
    
    def test_init(self, adapter):
        """Test adapter initialization."""
        assert adapter._current_model == "anthropic/claude-3.5-sonnet"
        assert adapter.config.api_key == "test-api-key"
    
    def test_model_name_property(self, adapter):
        """Test model_name property."""
        assert adapter.model_name == "openrouter/anthropic/claude-3.5-sonnet"
    
    def test_set_model(self, adapter):
        """Test setting model."""
        adapter.set_model("openai/gpt-4-turbo")
        assert adapter._current_model == "openai/gpt-4-turbo"
    
    def test_set_fallbacks(self, adapter):
        """Test setting fallback models."""
        adapter.set_fallbacks(["meta-llama/llama-3.1-70b-instruct"])
        assert "meta-llama/llama-3.1-70b-instruct" in adapter.config.fallback_models
    
    def test_build_headers(self, adapter):
        """Test request headers are correct."""
        headers = adapter._build_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers
    
    def test_calculate_cost(self, adapter):
        """Test cost calculation."""
        cost = adapter._calculate_cost(
            model="anthropic/claude-3.5-sonnet",
            input_tokens=1000,
            output_tokens=500,
        )
        
        # Should be > 0
        assert cost > 0
    
    def test_get_stats(self, adapter):
        """Test getting adapter statistics."""
        stats = adapter.get_stats()
        
        assert stats["provider"] == "openrouter"
        assert stats["current_model"] == "anthropic/claude-3.5-sonnet"
        assert "total_cost" in stats
        assert "request_count" in stats
    
    def test_repr(self, adapter):
        """Test string representation."""
        repr_str = repr(adapter)
        assert "OpenRouterAdapter" in repr_str
        assert "claude-3.5-sonnet" in repr_str


class TestOpenRouterTaskModels:
    """Tests for task-specific model configurations."""
    
    def test_fast_task_config(self):
        """Test fast task configuration."""
        config = OPENROUTER_TASK_MODELS["fast"]
        assert "haiku" in config["primary"] or "gpt-3.5" in config["primary"]
    
    def test_analysis_task_config(self):
        """Test analysis task configuration."""
        config = OPENROUTER_TASK_MODELS["analysis"]
        assert "sonnet" in config["primary"] or "gpt-4" in config["primary"]
    
    def test_reasoning_task_config(self):
        """Test reasoning task configuration."""
        config = OPENROUTER_TASK_MODELS["reasoning"]
        assert config["primary"] is not None
        assert len(config["fallbacks"]) > 0
    
    def test_default_task_config(self):
        """Test default task configuration."""
        config = OPENROUTER_TASK_MODELS["default"]
        assert config["primary"] is not None


class TestGetOpenRouterAdapterForTask:
    """Tests for factory function."""
    
    def test_create_fast_adapter(self):
        """Test creating adapter for fast tasks."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = get_openrouter_adapter_for_task("fast")
            
            assert adapter is not None
            assert isinstance(adapter, OpenRouterAdapter)
    
    def test_create_analysis_adapter(self):
        """Test creating adapter for analysis tasks."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = get_openrouter_adapter_for_task("analysis")
            
            assert adapter is not None
    
    def test_create_with_api_key(self):
        """Test creating adapter with explicit API key."""
        adapter = get_openrouter_adapter_for_task("default", api_key="explicit-key")
        
        assert adapter.config.api_key == "explicit-key"
    
    def test_create_unknown_task_uses_default(self):
        """Test unknown task type uses default config."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            adapter = get_openrouter_adapter_for_task("unknown_task")
            
            # Should use default config
            assert adapter is not None
