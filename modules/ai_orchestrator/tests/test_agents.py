"""
PredictBot AI Orchestrator - Agent Tests
=========================================

Unit tests for the specialized trading agents.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Import test subjects
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from state import TradingState, create_initial_state, WorkflowStep
from agents.base import BaseAgent
from agents.market_analyst import MarketAnalystAgent
from agents.news_sentiment import NewsSentimentAgent
from agents.forecaster import ForecasterAgent
from agents.critic import CriticAgent
from agents.risk_assessor import RiskAssessorAgent
from agents.trade_executor import TradeExecutorAgent


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_router():
    """Create a mock LLM router."""
    router = Mock()
    
    # Create mock LLM that returns JSON responses
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=Mock(
        content='{"test": "response"}',
        usage={"prompt_tokens": 100, "completion_tokens": 50}
    ))
    
    router.get_llm_for_task = Mock(return_value=mock_llm)
    return router


@pytest.fixture
def sample_opportunities():
    """Create sample market opportunities."""
    return [
        {
            "market_id": "market_1",
            "platform": "polymarket",
            "question": "Will Bitcoin reach $100k by end of 2024?",
            "current_price": 0.45,
            "volume_24h": 50000,
            "liquidity_score": 0.8,
            "end_date": "2024-12-31T23:59:59Z"
        },
        {
            "market_id": "market_2",
            "platform": "kalshi",
            "question": "Will the Fed cut rates in March?",
            "current_price": 0.35,
            "volume_24h": 25000,
            "liquidity_score": 0.6,
            "end_date": "2024-03-20T18:00:00Z"
        },
        {
            "market_id": "market_3",
            "platform": "polymarket",
            "question": "Will it rain in NYC tomorrow?",
            "current_price": 0.02,  # Too extreme, should be filtered
            "volume_24h": 500,  # Too low volume
            "liquidity_score": 0.2,
            "end_date": "2024-01-16T00:00:00Z"
        }
    ]


@pytest.fixture
def initial_state(sample_opportunities):
    """Create initial trading state with opportunities."""
    state = create_initial_state("test_cycle_001")
    state["opportunities"] = sample_opportunities
    return state


# =============================================================================
# State Tests
# =============================================================================

class TestTradingState:
    """Tests for TradingState creation and manipulation."""
    
    def test_create_initial_state(self):
        """Test creating initial state."""
        state = create_initial_state("test_123")
        
        assert state["cycle_id"] == "test_123"
        assert state["current_step"] == WorkflowStep.INITIALIZED.value
        assert state["opportunities"] == []
        assert state["forecasts"] == []
        assert state["trade_signals"] == []
        assert state["errors"] == []
    
    def test_state_has_required_fields(self):
        """Test that state has all required fields."""
        state = create_initial_state("test")
        
        required_fields = [
            "cycle_id", "started_at", "current_step",
            "opportunities", "selected_markets",
            "market_analysis", "news_sentiment", "forecasts",
            "critic_feedback", "risk_assessment",
            "trade_signals", "executed_trades",
            "portfolio", "errors", "retry_count"
        ]
        
        for field in required_fields:
            assert field in state, f"Missing field: {field}"


# =============================================================================
# Market Analyst Tests
# =============================================================================

class TestMarketAnalystAgent:
    """Tests for the Market Analyst agent."""
    
    @pytest.mark.asyncio
    async def test_pre_filter_markets(self, mock_llm_router, sample_opportunities):
        """Test market pre-filtering."""
        agent = MarketAnalystAgent(mock_llm_router)
        
        filtered = agent._pre_filter_markets(sample_opportunities)
        
        # Should filter out market_3 (low volume, low liquidity, extreme price)
        assert len(filtered) == 2
        assert all(m["market_id"] != "market_3" for m in filtered)
    
    @pytest.mark.asyncio
    async def test_process_with_no_opportunities(self, mock_llm_router):
        """Test processing with no opportunities."""
        agent = MarketAnalystAgent(mock_llm_router)
        state = create_initial_state("test")
        
        result = await agent.process(state)
        
        assert result["selected_markets"] == []
        assert result["market_analysis"]["status"] == "no_opportunities"
    
    @pytest.mark.asyncio
    async def test_score_markets(self, mock_llm_router):
        """Test market scoring."""
        agent = MarketAnalystAgent(mock_llm_router)
        
        analysis_results = {
            "market_1": {
                "liquidity_assessment": "high",
                "trading_opportunity": "strong",
                "volatility_estimate": 0.4
            },
            "market_2": {
                "liquidity_assessment": "low",
                "trading_opportunity": "weak",
                "volatility_estimate": 0.9
            }
        }
        
        scored = agent._score_markets(analysis_results)
        
        assert len(scored) == 2
        assert scored[0]["market_id"] == "market_1"  # Higher score first
        assert scored[0]["quality_score"] > scored[1]["quality_score"]


# =============================================================================
# Risk Assessor Tests
# =============================================================================

class TestRiskAssessorAgent:
    """Tests for the Risk Assessor agent."""
    
    @pytest.mark.asyncio
    async def test_kelly_calculation(self, mock_llm_router):
        """Test Kelly criterion calculation."""
        agent = RiskAssessorAgent(mock_llm_router)
        
        # Test with edge
        kelly = agent._calculate_kelly(
            predicted_prob=0.6,
            market_price=0.5,
            confidence=0.8
        )
        
        assert kelly > 0  # Should have positive Kelly with edge
        assert kelly < 1  # Should be less than 100%
    
    @pytest.mark.asyncio
    async def test_kelly_no_edge(self, mock_llm_router):
        """Test Kelly with no edge."""
        agent = RiskAssessorAgent(mock_llm_router)
        
        kelly = agent._calculate_kelly(
            predicted_prob=0.5,
            market_price=0.5,
            confidence=0.5
        )
        
        assert kelly == 0  # No edge = no bet
    
    @pytest.mark.asyncio
    async def test_volatility_risk_estimation(self, mock_llm_router):
        """Test volatility risk estimation."""
        agent = RiskAssessorAgent(mock_llm_router)
        
        # High liquidity, mid price = low volatility
        risk_low = agent._estimate_volatility_risk({
            "liquidity_score": 0.9,
            "current_price": 0.5
        })
        
        # Low liquidity, extreme price = high volatility
        risk_high = agent._estimate_volatility_risk({
            "liquidity_score": 0.1,
            "current_price": 0.95
        })
        
        assert risk_low < risk_high


# =============================================================================
# Trade Executor Tests
# =============================================================================

class TestTradeExecutorAgent:
    """Tests for the Trade Executor agent."""
    
    @pytest.mark.asyncio
    async def test_expected_value_calculation(self, mock_llm_router):
        """Test expected value calculation."""
        agent = TradeExecutorAgent(mock_llm_router)
        
        # Positive edge on YES
        ev = agent._calculate_expected_value(
            predicted_prob=0.6,
            current_price=0.5,
            size=100,
            action="buy_yes"
        )
        
        assert ev > 0  # Should be positive with edge
    
    @pytest.mark.asyncio
    async def test_urgency_determination(self, mock_llm_router):
        """Test urgency determination."""
        agent = TradeExecutorAgent(mock_llm_router)
        
        # High edge, near resolution = immediate
        urgency = agent._determine_urgency(
            forecast={"edge_vs_market": 0.15},
            details={},
            risk={"time_decay_risk": 0.9, "volatility_risk": 0.8}
        )
        
        assert urgency == "immediate"
        
        # Low edge, far from resolution = patient
        urgency = agent._determine_urgency(
            forecast={"edge_vs_market": 0.03},
            details={},
            risk={"time_decay_risk": 0.1, "volatility_risk": 0.2}
        )
        
        assert urgency == "patient"


# =============================================================================
# Integration Tests
# =============================================================================

class TestAgentIntegration:
    """Integration tests for agent pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self, mock_llm_router, initial_state):
        """Test running through all agents with mocks."""
        # Configure mock to return appropriate JSON for each agent
        mock_llm = mock_llm_router.get_llm_for_task()
        
        # Market analysis response
        mock_llm.ainvoke.return_value = Mock(
            content='''{
                "market_1": {
                    "liquidity_assessment": "high",
                    "trend_direction": "bullish",
                    "volatility_estimate": 0.4,
                    "trading_opportunity": "strong",
                    "key_factors": ["high volume"],
                    "recommended_strategy": "buy"
                }
            }''',
            usage={"prompt_tokens": 100, "completion_tokens": 50}
        )
        
        # Run market analyst
        analyst = MarketAnalystAgent(mock_llm_router)
        state = await analyst.run(initial_state)
        
        assert "market_analysis" in state
        assert len(state.get("selected_markets", [])) > 0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
