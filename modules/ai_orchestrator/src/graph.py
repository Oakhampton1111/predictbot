"""
PredictBot AI Orchestrator - LangGraph Workflow
================================================

This module defines the LangGraph workflow that orchestrates the
6 specialized agents through the trading decision pipeline.

Workflow Steps:
1. Market Analysis - Analyze and filter market opportunities
2. News Sentiment - Process news and social sentiment
3. Forecasting - Generate probability forecasts
4. Critique - Validate and challenge forecasts
5. Risk Assessment - Evaluate trade risk and sizing
6. Trade Execution - Generate final trade signals
"""

import os
import sys
from typing import Any, Dict, Optional, Literal
from datetime import datetime
import uuid
import json

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "END"
    MemorySaver = None

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from shared.logging_config import get_logger, log_critical_junction
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
    
    def log_critical_junction(*args, **kwargs):
        pass
    
    def get_metrics_registry():
        return None

from .state import TradingState, WorkflowStep, create_initial_state
from .agents import (
    MarketAnalystAgent,
    NewsSentimentAgent,
    ForecasterAgent,
    CriticAgent,
    RiskAssessorAgent,
    TradeExecutorAgent,
)
from .llm import LLMRouter


logger = get_logger("ai_orchestrator.graph")


class TradingWorkflow:
    """
    LangGraph-based trading workflow orchestrator.
    
    This class manages the multi-agent trading pipeline, coordinating
    the flow of information between specialized agents.
    """
    
    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        redis_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the trading workflow.
        
        Args:
            llm_router: LLM router instance (created if not provided)
            redis_url: Redis URL for state checkpointing
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logger
        self.metrics = get_metrics_registry()
        
        # Initialize LLM router
        self.llm_router = llm_router or LLMRouter(config)
        
        # Initialize agents
        self._init_agents()
        
        # Initialize Redis for checkpointing
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Compile the graph
        self.app = self._compile_graph()
        
        self.logger.info("Trading workflow initialized")
    
    def _init_agents(self) -> None:
        """Initialize all specialized agents."""
        agent_config = self.config.get("agents", {})
        
        self.market_analyst = MarketAnalystAgent(
            self.llm_router,
            config=agent_config.get("market_analyst")
        )
        
        self.news_sentiment = NewsSentimentAgent(
            self.llm_router,
            config=agent_config.get("news_sentiment")
        )
        
        self.forecaster = ForecasterAgent(
            self.llm_router,
            config=agent_config.get("forecaster")
        )
        
        self.critic = CriticAgent(
            self.llm_router,
            config=agent_config.get("critic")
        )
        
        self.risk_assessor = RiskAssessorAgent(
            self.llm_router,
            config=agent_config.get("risk_assessor")
        )
        
        self.trade_executor = TradeExecutorAgent(
            self.llm_router,
            config=agent_config.get("trade_executor")
        )
        
        self.logger.info("All agents initialized")
    
    def _build_graph(self) -> Optional[StateGraph]:
        """Build the LangGraph state graph."""
        if not LANGGRAPH_AVAILABLE:
            self.logger.warning("LangGraph not available, using fallback execution")
            return None
        
        # Create state graph
        graph = StateGraph(TradingState)
        
        # Add nodes for each agent
        graph.add_node("market_analysis", self._market_analysis_node)
        graph.add_node("news_sentiment", self._news_sentiment_node)
        graph.add_node("forecasting", self._forecasting_node)
        graph.add_node("critique", self._critique_node)
        graph.add_node("risk_assessment", self._risk_assessment_node)
        graph.add_node("trade_execution", self._trade_execution_node)
        
        # Set entry point
        graph.set_entry_point("market_analysis")
        
        # Add edges with conditional routing
        graph.add_conditional_edges(
            "market_analysis",
            self._should_continue_after_analysis,
            {
                "continue": "news_sentiment",
                "end": END
            }
        )
        
        graph.add_edge("news_sentiment", "forecasting")
        
        graph.add_conditional_edges(
            "forecasting",
            self._should_continue_after_forecasting,
            {
                "continue": "critique",
                "end": END
            }
        )
        
        graph.add_edge("critique", "risk_assessment")
        
        graph.add_conditional_edges(
            "risk_assessment",
            self._should_continue_after_risk,
            {
                "continue": "trade_execution",
                "end": END
            }
        )
        
        graph.add_edge("trade_execution", END)
        
        return graph
    
    def _compile_graph(self) -> Any:
        """Compile the graph with checkpointing."""
        if not self.graph:
            return None
        
        # Use memory saver for checkpointing
        # In production, would use Redis-based checkpointer
        checkpointer = MemorySaver() if MemorySaver else None
        
        return self.graph.compile(checkpointer=checkpointer)
    
    # =========================================================================
    # Node Functions
    # =========================================================================
    
    async def _market_analysis_node(self, state: TradingState) -> TradingState:
        """Execute market analysis agent."""
        self.logger.info(f"[{state['cycle_id']}] Running market analysis")
        return await self.market_analyst.run(state)
    
    async def _news_sentiment_node(self, state: TradingState) -> TradingState:
        """Execute news sentiment agent."""
        self.logger.info(f"[{state['cycle_id']}] Running news sentiment analysis")
        return await self.news_sentiment.run(state)
    
    async def _forecasting_node(self, state: TradingState) -> TradingState:
        """Execute forecaster agent."""
        self.logger.info(f"[{state['cycle_id']}] Running forecasting")
        return await self.forecaster.run(state)
    
    async def _critique_node(self, state: TradingState) -> TradingState:
        """Execute critic agent."""
        self.logger.info(f"[{state['cycle_id']}] Running critique")
        return await self.critic.run(state)
    
    async def _risk_assessment_node(self, state: TradingState) -> TradingState:
        """Execute risk assessor agent."""
        self.logger.info(f"[{state['cycle_id']}] Running risk assessment")
        return await self.risk_assessor.run(state)
    
    async def _trade_execution_node(self, state: TradingState) -> TradingState:
        """Execute trade executor agent."""
        self.logger.info(f"[{state['cycle_id']}] Running trade execution")
        result = await self.trade_executor.run(state)
        result["current_step"] = WorkflowStep.COMPLETED.value
        return result
    
    # =========================================================================
    # Conditional Edge Functions
    # =========================================================================
    
    def _should_continue_after_analysis(
        self,
        state: TradingState
    ) -> Literal["continue", "end"]:
        """Determine if workflow should continue after market analysis."""
        selected_markets = state.get("selected_markets", [])
        errors = state.get("errors", [])
        
        # Stop if no markets selected or too many errors
        if not selected_markets:
            self.logger.info("No markets selected, ending workflow")
            return "end"
        
        if len(errors) >= state.get("max_retries", 3):
            self.logger.warning("Too many errors, ending workflow")
            return "end"
        
        return "continue"
    
    def _should_continue_after_forecasting(
        self,
        state: TradingState
    ) -> Literal["continue", "end"]:
        """Determine if workflow should continue after forecasting."""
        forecasts = state.get("forecasts", [])
        
        if not forecasts:
            self.logger.info("No forecasts generated, ending workflow")
            return "end"
        
        return "continue"
    
    def _should_continue_after_risk(
        self,
        state: TradingState
    ) -> Literal["continue", "end"]:
        """Determine if workflow should continue after risk assessment."""
        risk_assessment = state.get("risk_assessment", {})
        individual = risk_assessment.get("individual", {})
        
        # Check if any trades are viable
        tradeable_count = sum(
            1 for r in individual.values()
            if r.get("tradeable", False)
        )
        
        if tradeable_count == 0:
            self.logger.info("No tradeable opportunities, ending workflow")
            return "end"
        
        return "continue"
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    async def run_cycle(
        self,
        opportunities: list,
        portfolio: Optional[Dict] = None,
        cycle_id: Optional[str] = None
    ) -> TradingState:
        """
        Run a complete trading cycle.
        
        Args:
            opportunities: List of market opportunities to analyze
            portfolio: Current portfolio state
            cycle_id: Optional cycle identifier
            
        Returns:
            Final TradingState with trade signals
        """
        # Create initial state
        cycle_id = cycle_id or str(uuid.uuid4())
        state = create_initial_state(cycle_id)
        state["opportunities"] = opportunities
        
        if portfolio:
            state["portfolio"] = portfolio
        
        self.logger.info(f"Starting trading cycle {cycle_id} with {len(opportunities)} opportunities")
        
        # Save initial state to Redis
        await self._save_checkpoint(state)
        
        try:
            if self.app:
                # Run through LangGraph
                config = {"configurable": {"thread_id": cycle_id}}
                result = await self.app.ainvoke(state, config)
            else:
                # Fallback: run agents sequentially
                result = await self._run_fallback(state)
            
            # Save final state
            await self._save_checkpoint(result)
            
            self.logger.info(
                f"Trading cycle {cycle_id} completed with "
                f"{len(result.get('trade_signals', []))} trade signals"
            )
            
            return result
            
        except Exception as e:
            self.logger.exception(f"Trading cycle {cycle_id} failed: {e}")
            state["errors"].append(str(e))
            state["current_step"] = WorkflowStep.FAILED.value
            await self._save_checkpoint(state)
            return state
    
    async def _run_fallback(self, state: TradingState) -> TradingState:
        """Run agents sequentially without LangGraph."""
        # Market Analysis
        state = await self.market_analyst.run(state)
        if not state.get("selected_markets"):
            return state
        
        # News Sentiment
        state = await self.news_sentiment.run(state)
        
        # Forecasting
        state = await self.forecaster.run(state)
        if not state.get("forecasts"):
            return state
        
        # Critique
        state = await self.critic.run(state)
        
        # Risk Assessment
        state = await self.risk_assessor.run(state)
        
        # Trade Execution
        state = await self.trade_executor.run(state)
        state["current_step"] = WorkflowStep.COMPLETED.value
        
        return state
    
    async def _save_checkpoint(self, state: TradingState) -> None:
        """Save state checkpoint to Redis."""
        if not REDIS_AVAILABLE:
            return
        
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(self.redis_url)
            
            key = f"predictbot:cycle:{state['cycle_id']}"
            await self.redis_client.set(
                key,
                json.dumps(dict(state)),
                ex=86400  # 24 hour expiry
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to save checkpoint: {e}")
    
    async def get_cycle_state(self, cycle_id: str) -> Optional[TradingState]:
        """Retrieve a cycle's state from Redis."""
        if not REDIS_AVAILABLE or not self.redis_client:
            return None
        
        try:
            key = f"predictbot:cycle:{cycle_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            self.logger.warning(f"Failed to get checkpoint: {e}")
        
        return None
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        return {
            "market_analyst": self.market_analyst.stats,
            "news_sentiment": self.news_sentiment.stats,
            "forecaster": self.forecaster.stats,
            "critic": self.critic.stats,
            "risk_assessor": self.risk_assessor.stats,
            "trade_executor": self.trade_executor.stats,
        }
    
    def get_llm_stats(self) -> Dict[str, Any]:
        """Get LLM router statistics."""
        return self.llm_router.get_stats()


# Factory function
def create_workflow(config: Optional[Dict[str, Any]] = None) -> TradingWorkflow:
    """
    Create a new trading workflow instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured TradingWorkflow instance
    """
    return TradingWorkflow(config=config)
