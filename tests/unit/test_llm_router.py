"""
Unit Tests - LLM Router
========================

Tests for the LLM router module.
"""

import pytest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.ai_orchestrator.src.llm.router import (
    LLMProvider,
    TaskType,
    ProviderConfig,
    CostTracker,
    LLMRouter,
)


class TestLLMProvider:
    """Tests for LLMProvider enum."""
    
    def test_provider_values(self):
        """Test provider enum values."""
        assert LLMProvider.OPENROUTER.value == "openrouter"
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"


class TestTaskType:
    """Tests for TaskType enum."""
    
    def test_task_type_values(self):
        """Test task type enum values."""
        assert TaskType.FAST.value == "fast"
        assert TaskType.ANALYSIS.value == "analysis"
        assert TaskType.REASONING.value == "reasoning"
        assert TaskType.CRITIQUE.value == "critique"
        assert TaskType.DEFAULT.value == "default"


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""
    
    def test_create_config(self):
        """Test creating provider config."""
        config = ProviderConfig(
            name="openrouter",
            enabled=True,
            api_key="test-key",
            default_model="anthropic/claude-3.5-sonnet",
        )
        
        assert config.name == "openrouter"
        assert config.enabled is True
        assert config.api_key == "test-key"
        assert config.default_model == "anthropic/claude-3.5-sonnet"
    
    def test_config_defaults(self):
        """Test provider config defaults."""
        config = ProviderConfig(name="test")
        
        assert config.enabled is True
        assert config.api_key is None
        assert config.monthly_budget == 0.0
        assert config.max_retries == 3
        assert config.timeout == 60.0


class TestCostTracker:
    """Tests for CostTracker class."""
    
    def test_init(self):
        """Test cost tracker initialization."""
        tracker = CostTracker()
        
        assert tracker.get_total_spend() == 0.0
    
    def test_add_usage(self):
        """Test adding usage records."""
        tracker = CostTracker()
        
        tracker.add(
            provider="openrouter",
            model="anthropic/claude-3.5-sonnet",
            input_tokens=1000,
            output_tokens=500,
            cost=0.05,
        )
        
        assert tracker.get_monthly_spend("openrouter") == 0.05
        assert tracker.get_total_spend() == 0.05
    
    def test_check_budget_within(self):
        """Test budget check when within limit."""
        tracker = CostTracker()
        
        tracker.add("openrouter", "model", 1000, 500, 10.0)
        
        assert tracker.check_budget("openrouter", 100.0) is True
    
    def test_check_budget_exceeded(self):
        """Test budget check when exceeded."""
        tracker = CostTracker()
        
        tracker.add("openrouter", "model", 1000, 500, 50.0)
        
        assert tracker.check_budget("openrouter", 40.0) is False
    
    def test_check_budget_unlimited(self):
        """Test budget check with no limit."""
        tracker = CostTracker()
        
        tracker.add("openrouter", "model", 1000, 500, 1000.0)
        
        # Budget of 0 means unlimited
        assert tracker.check_budget("openrouter", 0) is True
    
    def test_get_stats(self):
        """Test getting statistics."""
        tracker = CostTracker()
        
        tracker.add("openrouter", "model", 1000, 500, 0.05)
        
        stats = tracker.get_stats()
        
        assert "current_month" in stats
        assert "monthly_totals" in stats
        assert "total_spend" in stats
        assert stats["total_spend"] == 0.05


class TestLLMRouter:
    """Tests for LLMRouter class."""
    
    def test_router_init(self):
        """Test router initialization."""
        router = LLMRouter()
        
        assert router is not None
        assert len(router.providers) > 0
    
    def test_default_routing_config(self):
        """Test default routing configuration."""
        assert TaskType.FAST in LLMRouter.DEFAULT_ROUTING
        assert TaskType.ANALYSIS in LLMRouter.DEFAULT_ROUTING
        assert TaskType.REASONING in LLMRouter.DEFAULT_ROUTING
    
    def test_openrouter_models_config(self):
        """Test OpenRouter model configuration."""
        assert TaskType.FAST in LLMRouter.OPENROUTER_MODELS
        assert "primary" in LLMRouter.OPENROUTER_MODELS[TaskType.FAST]
        assert "fallbacks" in LLMRouter.OPENROUTER_MODELS[TaskType.FAST]
    
    def test_get_stats(self):
        """Test getting router statistics."""
        router = LLMRouter()
        
        stats = router.get_stats()
        
        assert "providers" in stats
        assert "cost_tracker" in stats
    
    def test_mark_provider_unhealthy(self):
        """Test marking provider as unhealthy."""
        router = LLMRouter()
        
        router.mark_provider_unhealthy(LLMProvider.OPENROUTER)
        
        assert router._provider_health[LLMProvider.OPENROUTER] is False
    
    def test_mark_provider_healthy(self):
        """Test marking provider as healthy."""
        router = LLMRouter()
        
        router.mark_provider_unhealthy(LLMProvider.OPENROUTER)
        router.mark_provider_healthy(LLMProvider.OPENROUTER)
        
        assert router._provider_health[LLMProvider.OPENROUTER] is True
